import hashlib
import io
import json
import os
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
from scripts import agent_setup,plugin_runtime

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
        with patch('scripts.agent_setup.shutil.which',return_value=None):
            for target in ['auto','claude','hermes','both']:
                with self.subTest(target=target),self.assertRaises(ValueError):agent_setup.agents(target)
    def test_native_registration_uses_documented_managers(self):
        with patch('scripts.agent_setup.run') as run:
            agent_setup.register({'claude':'/space path/claude','hermes':'/space path/hermes'})
            commands=[c.args[0] for c in run.call_args_list]
            self.assertEqual(commands[0],['/space path/claude','plugin','marketplace','add','jbellsolutions/ghl-super-hub'])
            self.assertEqual(commands[1][-2:],['--scope','user'])
            self.assertEqual(commands[2][-1],'--enable')
            self.assertEqual(commands[3],['/space path/hermes','plugins','enable','ghl-super-hub'])
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
            with patch.dict(os.environ,{'XDG_DATA_HOME':directory}),patch.object(sys,'argv',['setup','--agent','claude']),patch('scripts.agent_setup.agents',return_value={'claude':'stub'}),patch('scripts.agent_setup.download',side_effect=download),patch('scripts.agent_setup.register') as register:
                with self.assertRaisesRegex(ValueError,'checksum mismatch'):agent_setup.main()
                register.assert_not_called()
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
