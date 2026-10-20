import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import requests
from click.testing import CliRunner
from ghl_hub import catalog, executor, transport, knowledge
from ghl_hub.bootstrap import load_env
from ghl_hub.mcp import dispatch
from cli_anything.gohighlevel.gohighlevel_cli import cli

ROOT=Path(__file__).resolve().parents[1]

def response(code=200, data=None, headers=None):
    r=requests.Response();r.status_code=code;r._content=json.dumps(data or {'ok':True}).encode();r.headers.update(headers or {});return r

class CatalogAndExecution(unittest.TestCase):
    def test_catalog_unique_and_source_backed(self):
        operations=catalog.all_operations()
        self.assertGreater(len(operations),500)
        self.assertEqual(len(operations),len({o['id'] for o in operations}))
        for o in operations:
            s=json.loads((knowledge.DATA/o['source']).read_text())
            self.assertEqual(o['method'].lower() in s['paths'][o['path']],True)
    def test_schema_exposes_responses_and_reachable_components(self):
        result=catalog.schema('workflows:get-workflow')
        self.assertIn('200',result['operation']['responses'])
        self.assertIn('GetWorkflowSuccessfulResponseDto',result['components']['schemas'])
        self.assertIn('securitySchemes',result['components'])
    @patch.dict(os.environ,{},clear=True)
    def test_no_implicit_tenant(self):
        with self.assertRaisesRegex(ValueError,'locationId'): executor.prepare('workflows:get-workflow')
        from cli_anything.gohighlevel.utils.ghl_client import _get_location_id
        with self.assertRaises(ValueError): _get_location_id()
    @patch.dict(os.environ,{'GHL_LOCATION_ID':'tenant-a'},clear=True)
    def test_location_and_dry_run_do_not_send(self):
        with patch('ghl_hub.transport.requests.request') as send:
            result=executor.call('workflows:get-workflow')
            self.assertTrue(result['dry_run']);self.assertEqual(result['request']['query']['locationId'],'tenant-a');send.assert_not_called()
    def test_required_nested_fields_checked(self):
        with self.assertRaisesRegex(ValueError,'required'): executor.prepare('courses:import-courses',body={})
    def test_path_cannot_escape_origin(self):
        for path in ['https://example.com','//example.com','/contacts/../oauth','/contacts/%2E%2E','/contacts/x?token=secret','/contacts/x\r\nX:y']:
            with self.subTest(path=path),self.assertRaises(ValueError):transport.validate_path(path)
    def test_path_parameter_escaping_blocks_traversal(self):
        with self.assertRaises(ValueError): executor.prepare('affiliate-manager:get-affiliate',path_params={'locationId':'abc','affiliateId':'../evil'})
    def test_enum_and_nested_type_validation(self):
        with self.assertRaises(ValueError): executor.validate({'mode':'wrong'},{'type':'object','properties':{'mode':{'enum':['draft']}}},{},Path('.'))
        with self.assertRaises(ValueError): executor.validate(True,{'type':'integer'},{},Path('.'))
    def test_read_retry_and_mutation_not_replayed(self):
        with patch.dict(os.environ,{'GHL_API_KEY':'test'},clear=True),patch('ghl_hub.transport.time.sleep'),patch('ghl_hub.transport.requests.request',side_effect=[response(429),response()]) as send:
            self.assertEqual(transport.request('GET','/contacts/'),{'ok':True});self.assertEqual(send.call_count,2)
        with patch.dict(os.environ,{'GHL_API_KEY':'test'},clear=True),patch('ghl_hub.transport.requests.request',return_value=response(503)) as send:
            with self.assertRaises(requests.HTTPError): transport.request('POST','/contacts/',body={})
            self.assertEqual(send.call_count,1)
    def test_redirect_refused_and_token_not_forwarded(self):
        with patch.dict(os.environ,{'GHL_API_KEY':'test'},clear=True),patch('ghl_hub.transport.requests.request',return_value=response(302)) as send:
            with self.assertRaises(ValueError): transport.request('GET','/contacts/')
            self.assertFalse(send.call_args.kwargs['allow_redirects'])
    def test_empty_response(self):
        r=response(204);r._content=b''
        self.assertEqual(transport.decode(r),{'statusCode':204})
    def test_multipart_upload_read_only_during_execute(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'file.txt';p.write_text('test')
            plan=executor.prepare('medias:upload-media-content',files={'file':str(p)})
            self.assertEqual(plan['files'],{'file':[str(p.resolve())]})
            with patch.dict(os.environ,{'GHL_API_KEY':'test'},clear=True),patch('ghl_hub.transport.requests.request',return_value=response()) as send:
                executor.call('medias:upload-media-content',files={'file':str(p)},execute=True)
                self.assertEqual(send.call_args.kwargs['files'][0][0],'file')
                self.assertTrue(send.call_args.kwargs['files'][0][1][1].closed)
    def test_missing_file_fails_before_network(self):
        with self.assertRaisesRegex(ValueError,'does not exist'):executor.prepare('medias:upload-media-content',files={'file':'/does-not-exist-test'})
    def test_public_oauth_exchange_omits_bearer(self):
        with patch.dict(os.environ,{},clear=True),patch('ghl_hub.transport.requests.request',return_value=response()) as send:
            transport.request('POST','/oauth/token',body={'grant_type':'authorization_code'},content_type='application/x-www-form-urlencoded',auth_required=False)
            self.assertNotIn('Authorization',send.call_args.kwargs['headers']);self.assertIn('data',send.call_args.kwargs)
    def test_cli_location_flag_reaches_hub(self):
        result=CliRunner().invoke(cli,['--location-id','tenant-flag','hub','call','workflows:get-workflow'])
        self.assertEqual(result.exit_code,0,result.output);self.assertEqual(json.loads(result.output)['request']['query']['locationId'],'tenant-flag')

class KnowledgeAndConfig(unittest.TestCase):
    def test_parser_uses_article_not_navigation(self):
        p=knowledge.ArticleParser();p.feed('<nav>Secret navigation</nav><h1 class="fw-page-title">Article</h1><div class="fw-content--single-article"><h1>Inner heading</h1><p>Body <a href="/source">link</a></p></div><aside>Unrelated</aside>')
        title,body=p.result();self.assertEqual(title,'Article');self.assertIn('Inner heading',body);self.assertIn('/source',body);self.assertNotIn('Unrelated',body);self.assertNotIn('navigation',body)
    def test_shell_syntax_in_dotenv_is_inert(self):
        with tempfile.TemporaryDirectory() as directory,patch.dict(os.environ,{},clear=True):
            p=Path(directory)/'.env'; marker=Path(directory)/'should-not-exist'
            p.write_text('GHL_API_KEY="$(touch '+str(marker)+')"\nGHL_LOCATION_ID=tenant\n')
            load_env(p);self.assertFalse(marker.exists());self.assertIn('$(touch',os.environ['GHL_API_KEY'])
    def test_profile_omitting_token_does_not_reuse_parent(self):
        with tempfile.TemporaryDirectory() as directory:
            profile=Path(directory)/'profile.env';profile.write_text('GHL_LOCATION_ID=other\n')
            result=subprocess.run([str(ROOT/'ghl'),'--env-file',str(profile),'hub','doctor'],cwd=directory,env={**os.environ,'GHL_API_KEY':'parent-token'},capture_output=True,text=True)
            self.assertEqual(result.returncode,0,result.stderr);self.assertFalse(json.loads(result.stdout)['token_configured'])
    def test_search_handles_punctuation(self):
        self.assertIsInstance(knowledge.search('"affiliate:campaign" --',limit=2),list)
    def test_blocked_discovery_retains_archive_and_reports_incomplete(self):
        with tempfile.TemporaryDirectory() as directory,patch.object(knowledge,'DATA',Path(directory)),patch.object(knowledge,'fetch',side_effect=knowledge.DocsAccessBlocked('blocked')):
            report=knowledge.sync_help(limit=1)
            self.assertFalse(report['complete']);self.assertEqual(report['errors'][0]['stage'],'discovery')

class McpProtocol(unittest.TestCase):
    def test_handshake_tools_and_notifications(self):
        result=dispatch({'jsonrpc':'2.0','id':1,'method':'initialize','params':{'protocolVersion':'2025-03-26'}})
        self.assertEqual(result['result']['protocolVersion'],'2025-03-26')
        self.assertEqual(len(dispatch({'jsonrpc':'2.0','id':2,'method':'tools/list'})['result']['tools']),6)
        self.assertIsNone(dispatch({'jsonrpc':'2.0','method':'notifications/initialized'}))
    def test_tool_errors_are_structured(self):
        result=dispatch({'jsonrpc':'2.0','id':3,'method':'tools/call','params':{'name':'ghl_call','arguments':{'operation_id':'missing','execute':'true'}}})
        self.assertTrue(result['result']['isError'])
    def test_stdio_is_valid_json_without_startup_noise(self):
        result=subprocess.run([str(ROOT/'ghl'),'hub','mcp'],input='{"jsonrpc":"2.0","id":1,"method":"ping"}\n{broken\n',text=True,capture_output=True)
        rows=[json.loads(line) for line in result.stdout.splitlines()]
        self.assertEqual(rows[0]['result'],{});self.assertEqual(rows[1]['error']['code'],-32700);self.assertEqual(result.returncode,0,result.stderr)

if __name__=='__main__': unittest.main()
