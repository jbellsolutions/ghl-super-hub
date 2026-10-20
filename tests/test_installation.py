import hashlib
import io
import json
import os
import pty
import select
import time
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from click.testing import CliRunner
from ghl_hub.bootstrap import load_env
from ghl_hub.connect import save_credentials, connect_command
from scripts import agent_setup,plugin_runtime,hermes_setup

ROOT=Path(__file__).resolve().parents[1]

class Installer(unittest.TestCase):
    def test_unpack_refuses_traversal_and_symlinks(self):
        with tempfile.TemporaryDirectory() as directory:
            for name,symlink in [('ghl-super-hub/../escape',False),('/absolute/file',False),('other/file',False),('ghl-super-hub/link',True)]:
                p=Path(directory)/'bad.zip'
                with zipfile.ZipFile(p,'w') as z:
                    entry=zipfile.ZipInfo(name)
                    if symlink:entry.external_attr=(stat.S_IFLNK|0o777)<<16
                    z.writestr(entry,b'test')
                with self.subTest(name=name),self.assertRaises(ValueError):agent_setup.unpack(p,Path(directory)/'out')
    def test_unpack_retains_executable_and_space_paths(self):
        with tempfile.TemporaryDirectory(prefix='ghl space ') as directory:
            p=Path(directory)/'good.zip'
            with zipfile.ZipFile(p,'w') as z:
                entry=zipfile.ZipInfo('ghl-super-hub/ghl');entry.external_attr=0o100755<<16;z.writestr(entry,b'#!/bin/sh\n')
            dest=Path(directory)/'out';agent_setup.unpack(p,dest)
            self.assertEqual((dest/'ghl').stat().st_mode & 0o777,0o755)
    def test_detection_does_not_silently_target_a_missing_agent(self):
        with patch('scripts.agent_setup.find_agent',return_value=None):
            for target in ['auto','claude','hermes','both']:
                with self.subTest(target=target),self.assertRaises(ValueError):agent_setup.agents(target)
    def test_native_registration_uses_documented_managers(self):
        with patch('scripts.agent_setup.run') as run:
            agent_setup.register({'claude':'/space path/claude'})
            commands=[c.args[0] for c in run.call_args_list]
            self.assertEqual(commands[0],['/space path/claude','plugin','marketplace','add','jbellsolutions/ghl-super-hub'])
            self.assertEqual(commands[1][-2:],['--scope','user'])
            self.assertEqual(len(commands),2)
    def test_existing_install_is_safe_to_repeat_but_real_errors_stop(self):
        already=subprocess.CompletedProcess([],1,stdout='Plugin already installed')
        denied=subprocess.CompletedProcess([],1,stdout='Permission denied')
        with patch('scripts.agent_setup.subprocess.run',return_value=already):agent_setup.run(['stub'],already_ok=True)
        with patch('scripts.agent_setup.subprocess.run',return_value=denied),self.assertRaisesRegex(RuntimeError,'Permission denied'):agent_setup.run(['stub'],already_ok=True)
    def test_wrong_checksum_stops_before_agent_registration(self):
        with tempfile.TemporaryDirectory() as directory:
            def download(url,path=None):
                if path:Path(path).write_bytes(b'wrong archive')
                else:return ('0'*64+'  ghl-super-hub.zip\n').encode()
            with patch.dict(os.environ,{'XDG_DATA_HOME':directory}),patch.object(sys,'argv',['setup','--agent','claude','--docs-only']),patch('scripts.agent_setup.agents',return_value={'claude':'stub'}),patch('scripts.agent_setup.download',side_effect=download),patch('scripts.agent_setup.register') as register:
                with self.assertRaisesRegex(ValueError,'checksum mismatch'):agent_setup.main()
                register.assert_not_called()
    def test_preflight_collects_missing_requirements_without_mutations(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'XDG_CONFIG_HOME':directory,'GHL_API_KEY':'','GHL_LOCATION_ID':''}),patch('scripts.agent_setup.shutil.which',return_value=None),patch('scripts.agent_setup.find_agent',return_value=None),patch('scripts.agent_setup.download') as download:
            args=type('Args',(),{'agent':'both','docs_only':False})()
            report,found=agent_setup.preflight(args)
            self.assertEqual(found,{})
            self.assertEqual({item['id'] for item in report['needs']},{'git','agent','ghl_connection'})
            self.assertFalse((Path(directory)/'ghl-super-hub').exists());download.assert_not_called()
    def test_noninteractive_missing_connection_stops_before_download(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'XDG_CONFIG_HOME':directory,'GHL_API_KEY':'','GHL_LOCATION_ID':''}),patch.object(sys,'argv',['setup','--non-interactive']),patch('scripts.agent_setup.agents',return_value={'claude':'stub'}),patch('scripts.agent_setup.download') as download,patch('sys.stdout',new_callable=io.StringIO) as output:
            self.assertEqual(agent_setup.main(),2);download.assert_not_called()
            report=json.loads(output.getvalue());self.assertEqual(report['status'],'needs_input')
            self.assertIn('ghl_connection',[item['id'] for item in report['needs']])
    def test_docs_only_preflight_is_read_only_and_needs_no_token(self):
        with patch.object(sys,'argv',['setup','--preflight','--docs-only']),patch('scripts.agent_setup.agents',return_value={'hermes':'stub'}),patch('scripts.agent_setup.check_hermes',return_value=[]),patch('scripts.agent_setup.download') as download,patch('sys.stdout',new_callable=io.StringIO) as output:
            self.assertEqual(agent_setup.main(),0);download.assert_not_called()
            self.assertEqual(json.loads(output.getvalue())['mode'],'documentation-only')
    def test_preflight_reuses_private_credentials_without_disclosing_them(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'XDG_CONFIG_HOME':directory,'GHL_API_KEY':'','GHL_LOCATION_ID':''}):
            agent_setup.save_connection('pit-private-test','tenant-test')
            self.assertEqual(agent_setup.credential_file().stat().st_mode & 0o777,0o600)
            args=type('Args',(),{'agent':'claude','docs_only':False})()
            with patch('scripts.agent_setup.agents',return_value={'claude':'stub'}):report,_=agent_setup.preflight(args)
            self.assertTrue(report['account_configured']);self.assertNotIn('pit-private-test',json.dumps(report))
            with patch.dict(os.environ,{'GHL_API_KEY':'','GHL_LOCATION_ID':''}):self.assertTrue(agent_setup.has_credentials())
    def test_prompt_eof_pauses_instead_of_looping(self):
        with self.assertRaises(EOFError):agent_setup.terminal_prompt(io.StringIO(),'Continue? ')
    def test_piped_install_prompts_on_tty_and_hides_token(self):
        for mode in ('connect','docs'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as directory:
                code="""from scripts import agent_setup as a
from unittest.mock import patch
from types import SimpleNamespace
args=SimpleNamespace(agent='claude',docs_only=False,preflight=False,non_interactive=False)
with patch.object(a,'agents',return_value={'claude':'stub'}):
    result=a.prepare(args)
    print('PREFLIGHT_DONE',bool(result),args.docs_only,flush=True)
"""
                env={**os.environ,'XDG_CONFIG_HOME':directory,'GHL_API_KEY':'','GHL_LOCATION_ID':'','GHL_ENV_FILE':''}
                pid,fd=pty.fork()
                if pid==0:
                    os.chdir(ROOT)
                    os.dup2(os.open(os.devnull,os.O_RDONLY),0)
                    os.execve(sys.executable,[sys.executable,'-c',code],env)
                output=b'';sent=set();deadline=time.monotonic()+12
                prompts=[(b'quit [q]? [c]: ',b'c\n' if mode=='connect' else b'd\n'),(b'access token (hidden): ',b'pit-hidden-install-test\n'),(b'sub-account ID: ',b'tenant-install-test\n')]
                try:
                    while time.monotonic()<deadline:
                        if not select.select([fd],[],[],0.2)[0]:continue
                        try:chunk=os.read(fd,8192)
                        except OSError:break
                        if not chunk:break
                        output+=chunk
                        for prompt,response in prompts:
                            if prompt in output and prompt not in sent:os.write(fd,response);sent.add(prompt)
                        if b'PREFLIGHT_DONE' in output:break
                    self.assertIn(b'PREFLIGHT_DONE True',output,output.decode())
                    self.assertNotIn(b'pit-hidden-install-test',output)
                    path=Path(directory)/'ghl-super-hub/credentials.env'
                    self.assertEqual(path.exists(),mode=='connect')
                    if path.exists():self.assertEqual(path.stat().st_mode & 0o777,0o600)
                finally:
                    os.close(fd)
                    # Kill only our child if a failed prompt left it waiting.
                    if os.waitpid(pid,os.WNOHANG)[0]==0:
                        os.kill(pid,15);os.waitpid(pid,0)
    def test_protected_credential_file_is_not_required_to_be_executable(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'GHL_ENV_FILE':str(Path(directory)/'.env'),'GHL_API_KEY':'','GHL_LOCATION_ID':''}):
            save_credentials('pit-protected-test','tenant-test',Path(directory)/'.env')
            self.assertFalse(os.access(Path(directory)/'.env',os.X_OK))
            args=type('Args',(),{'agent':'claude','docs_only':False})()
            with patch('scripts.agent_setup.agents',return_value={'claude':'stub'}):report,_=agent_setup.preflight(args)
            self.assertEqual(report['status'],'ready',report)
    def test_explicit_hermes_path_is_found_outside_path(self):
        with tempfile.TemporaryDirectory() as directory:
            executable=Path(directory)/'hermes';executable.write_text('#!/bin/sh\nexit 0\n');executable.chmod(0o755)
            with patch.dict(os.environ,{'GHL_HERMES_BIN':str(executable)}),patch('scripts.agent_setup.shutil.which',return_value=None):
                self.assertEqual(agent_setup.agents('hermes'),{'hermes':str(executable)})
    def test_orgo_hermes_virtualenv_is_discovered_without_path_edits(self):
        with patch.dict(os.environ,{'GHL_HERMES_BIN':''}),patch('scripts.agent_setup.shutil.which',return_value=None),patch.object(Path,'is_file',lambda path:str(path)=='/opt/hermes/.venv/bin/hermes'),patch('scripts.agent_setup.os.access',return_value=True):
            self.assertEqual(agent_setup.agents('hermes'),{'hermes':'/opt/hermes/.venv/bin/hermes'})
    def test_hermes_compatibility_registration_avoids_plugin_manager(self):
        with patch('scripts.agent_setup.hermes_python',return_value=Path('/hermes/python')),patch('scripts.agent_setup.run') as run:
            agent_setup.register_hermes(ROOT,'hermes')
            command=run.call_args.args[0]
            self.assertEqual(command[:2],['/hermes/python',str(ROOT/'scripts/hermes_setup.py')])
            self.assertNotIn('plugins',command)
    def test_runtime_preflight_does_not_download_python_without_consent(self):
        with tempfile.TemporaryDirectory() as directory:
            for name in ['python3','python3.14','python3.13','python3.12','python3.11','python3.10']:
                stub=Path(directory)/name;stub.write_text('#!/bin/sh\nexit 1\n');stub.chmod(0o755)
            env={**os.environ,'PATH':directory+':/usr/bin:/bin','GHL_INSTALL_PREFLIGHT':'1','GHL_PYTHON':''}
            result=subprocess.run(['bash',str(ROOT/'scripts/python-run.sh'),'ignored','--non-interactive'],env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,2,result.stderr)
            self.assertEqual(json.loads(result.stdout)['needs'][0]['id'],'python')
    def test_portable_mcp_tools_have_no_credentials(self):
        for file in ['mcp.json','.mcp.json']:
            data=json.loads((ROOT/file).read_text());server=data['mcpServers']['ghl-super-hub']
            self.assertEqual(server['type'],'stdio');self.assertEqual(server['command'],'bash')
            self.assertTrue(server['args'][0].endswith('/scripts/run-hub.sh'))
            for value in server.get('env',{}).values():self.assertTrue(value.startswith('${'))
    def test_manifests_agree_with_package_version(self):
        manifests=[json.loads((ROOT/p).read_text()) for p in ['plugin.json','.claude-plugin/plugin.json']]
        self.assertEqual(manifests[0]['version'],manifests[1]['version'])
        self.assertIn('version="'+manifests[0]['version']+'"',(ROOT/'setup.py').read_text())
    def test_prewarmed_native_runtime_requires_matching_source(self):
        with tempfile.TemporaryDirectory() as directory:
            release=Path(directory)/'ghl-super-hub/releases/v2.2.0';(release/'.venv/bin').mkdir(parents=True)
            python=release/'.venv/bin/python';python.touch();(release/'.ghl-runtime.json').write_text(json.dumps({'fingerprint':plugin_runtime.fingerprint(ROOT)}))
            with patch.dict(os.environ,{'XDG_DATA_HOME':directory}):
                selected,data=plugin_runtime.prepare(ROOT)
                self.assertEqual(selected,python);self.assertEqual(data,release/'knowledge')
    def test_native_build_snapshot_keeps_generated_files_outside_plugin(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/'build source';plugin_runtime.snapshot(ROOT,target)
            self.assertTrue((target/'setup.py').exists());self.assertTrue((target/'ghl_hub/mcp.py').exists())
            self.assertFalse((target/'.env').exists());self.assertFalse((target/'knowledge/search.sqlite3').exists())
            self.assertFalse(any(target.rglob('*.pyc')))
    def test_symlink_launcher_works_without_readlink_f(self):
        with tempfile.TemporaryDirectory(prefix='ghl path ') as directory:
            p=Path(directory)/'ghl';p.symlink_to(ROOT/'ghl')
            result=subprocess.run([str(p),'hub','operations','workflow','--limit','1'],text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertGreater(json.loads(result.stdout)['total'],0)

class HermesCompatibility(unittest.TestCase):
    def test_skills_mcp_backup_and_repeat_preserve_user_configuration(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);config=home/'config.yaml'
            original={'model':'user-choice','mcp_servers':{'other':{'command':'keep-this'}},'plugins':{'enabled':['other-plugin']}}
            config.write_text(json.dumps(original));credentials=save_credentials('pit-never-serialize','tenant',home/'private.env')
            first=hermes_setup.configure(ROOT,home,credentials,json.loads,json.dumps)
            self.assertEqual(first['skills'],9);self.assertTrue(first['backup'])
            self.assertEqual(Path(first['backup']).stat().st_mode & 0o777,0o600)
            after=json.loads(config.read_text());self.assertEqual(after['model'],original['model'])
            self.assertEqual(after['mcp_servers']['other'],original['mcp_servers']['other'])
            self.assertEqual(after['plugins'],original['plugins']);self.assertNotIn('pit-never-serialize',config.read_text())
            self.assertEqual(config.stat().st_mode & 0o777,0o600)
            second=hermes_setup.configure(ROOT,home,credentials,json.loads,json.dumps)
            self.assertIsNone(second['backup']);self.assertEqual(len(list((home/'skills').glob('ghl-*/SKILL.md'))),9)
    def test_existing_unmanaged_skill_is_reported_before_changes(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);skill=home/'skills/ghl-operator';skill.mkdir(parents=True);(skill/'SKILL.md').write_text('user content')
            self.assertTrue(hermes_setup.inspect_profile(home,json.loads))
            with self.assertRaisesRegex(ValueError,'not managed'):hermes_setup.configure(ROOT,home,home/'absent.env',json.loads,json.dumps)
            self.assertEqual((skill/'SKILL.md').read_text(),'user content');self.assertFalse((home/'config.yaml').exists())
    def test_customized_server_is_preserved_and_invalid_yaml_is_not_logged(self):
        with tempfile.TemporaryDirectory() as directory:
            home=Path(directory);config=home/'config.yaml';config.write_text(json.dumps({'mcp_servers':{'ghl-super-hub':{'command':'custom'}}}))
            problems=hermes_setup.inspect_profile(home,json.loads);self.assertIn('not managed',problems[0])
            config.write_text('pit-private-syntax-error')
            problems=hermes_setup.inspect_profile(home,json.loads);self.assertNotIn('pit-private',str(problems));self.assertIn('could not be parsed',problems[0])

class AccountConnection(unittest.TestCase):
    def test_hidden_prompt_never_echoes_token_and_saves_mode_600(self):
        with tempfile.TemporaryDirectory() as directory:
            file=Path(directory)/'credentials.env'
            result=CliRunner().invoke(connect_command,['--credentials-file',str(file)],input='pit-private-test\ntenant-test\n')
            self.assertEqual(result.exit_code,0,result.output);self.assertNotIn('pit-private-test',result.output)
            self.assertEqual(file.stat().st_mode & 0o777,0o600)
            with patch.dict(os.environ,{},clear=True):
                load_env(file);self.assertEqual(os.environ['GHL_API_KEY'],'pit-private-test')
    def test_credential_line_injection_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(ValueError):save_credentials('token\nEVIL=yes','tenant',Path(directory)/'out')
            self.assertFalse((Path(directory)/'out').exists())
    def test_connect_works_with_an_unconfigured_checkout_env(self):
        with tempfile.TemporaryDirectory() as directory:
            shared=Path(directory)/'ghl-super-hub/credentials.env';save_credentials('pit-test','tenant-test',shared)
            env={**os.environ,'XDG_CONFIG_HOME':directory,'GHL_API_KEY':'','GHL_LOCATION_ID':''}
            result=subprocess.run([str(ROOT/'ghl'),'hub','doctor'],env=env,text=True,capture_output=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertTrue(json.loads(result.stdout)['token_configured']);self.assertTrue(json.loads(result.stdout)['location_configured'])
    def test_empty_forwarded_environment_does_not_hide_saved_credentials(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{'GHL_API_KEY':''},clear=True):
            p=save_credentials('pit-test','tenant-test',Path(directory)/'out');load_env(p)
            self.assertEqual(os.environ['GHL_API_KEY'],'pit-test')

if __name__=='__main__':unittest.main()
