"""Resumable official documentation ingestion and SQLite full-text search."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
import hashlib
import os
import json
import re
import sqlite3
import time
import threading
from urllib.parse import urlsplit, unquote
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get('GHL_KNOWLEDGE_DIR', str(ROOT / 'knowledge')))

class ArticleParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.stack = []; self.body = []; self.title = []; self.capture = None; self.h1 = False
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag not in ('area','base','br','col','embed','hr','img','input','link','meta','param','source','track','wbr'):
            self.stack.append(tag)
        if 'fw-content--single-article' in attrs.get('class', ''):
            self.capture = len(self.stack)
        if tag == 'h1' and 'fw-page-title' in attrs.get('class', ''): self.h1 = True
        if self.capture:
            if tag in ('p','div','li','h1','h2','h3','h4','br','pre','tr'): self.body.append('\n')
            if tag == 'a' and attrs.get('href'): self.body.append(' [' + attrs['href'] + '] ')
            if tag == 'img': self.body.append(' [image: ' + attrs.get('alt','') + ' ' + attrs.get('src','') + '] ')
    def handle_endtag(self, tag):
        if tag == 'h1': self.h1 = False
        if tag in self.stack:
            index = len(self.stack) - 1 - self.stack[::-1].index(tag)
            if self.capture is not None and index < self.capture: self.capture = None
            self.stack = self.stack[:index]
    def handle_data(self, data):
        if self.h1: self.title.append(data)
        if self.capture and not any(t in self.stack for t in ('script','style')): self.body.append(data)
    def result(self):
        return ''.join(self.title).strip(), re.sub(r'\n\s*\n+', '\n\n', ''.join(self.body)).strip()

_pace_lock = threading.Lock()
_next_request = 0.0
_help_cooldown = 0.0

def pace_help():
    global _next_request
    with _pace_lock:
        now=time.monotonic()
        scheduled=max(now, _next_request, _help_cooldown)
        _next_request=scheduled+0.3
    time.sleep(max(0,scheduled-now))

class DocsAccessBlocked(RuntimeError):
    pass

def fetch(url):
    request = urllib.request.Request(url, headers={'User-Agent': 'GHL-Hub-Documentation/0.1 (local knowledge archive)'})
    for attempt in range(4):
        try:
            if urlsplit(url).hostname == 'help.gohighlevel.com': pace_help()
            with urllib.request.urlopen(request, timeout=45) as response: return response.read()
        except Exception as exc:
            if getattr(exc, 'headers', {}).get('cf-mitigated') == 'challenge':
                raise DocsAccessBlocked('Documentation host requires browser verification; stopped HTTP ingestion') from exc
            if getattr(exc, 'code', None) in (401,403,404): raise
            if getattr(exc, 'code', None) == 429:
                retry=exc.headers.get('Retry-After','30')
                delay=min(300,max(10,float(retry))) if retry.isdigit() else 30
                global _help_cooldown
                with _pace_lock: _help_cooldown=max(_help_cooldown,time.monotonic()+delay)
            if attempt == 3: raise
            time.sleep(min(30, 2 ** attempt * 2))

def db():
    DATA.mkdir(exist_ok=True)
    conn = sqlite3.connect(DATA / 'search.sqlite3')
    conn.execute('CREATE VIRTUAL TABLE IF NOT EXISTS documents USING fts5(url UNINDEXED, title, body, tokenize="unicode61")')
    return conn

def rebuild():
    conn = db(); conn.execute('DELETE FROM documents')
    for p in sorted((DATA / 'articles').glob('*.json')):
        item = json.loads(p.read_text()); conn.execute('INSERT INTO documents VALUES (?,?,?)',(item['url'], item['title'], item['text']))
    for p in sorted((DATA / 'upstream').rglob('*')):
        if p.suffix in ('.md','.json') and p.is_file():
            rel = p.relative_to(DATA / 'upstream').as_posix()
            conn.execute('INSERT INTO documents VALUES (?,?,?)', ('https://github.com/GoHighLevel/highlevel-api-docs/blob/' + revision() + '/' + rel, rel, p.read_text()))
    conn.commit(); count = conn.execute('SELECT count(*) FROM documents').fetchone()[0]; conn.close(); return count

def revision():
    p = DATA / 'api-source.json'
    return json.loads(p.read_text()).get('revision','main') if p.exists() else 'main'

def search(query, limit=8):
    if not (DATA / 'search.sqlite3').exists(): rebuild()
    tokens = re.findall(r'\w+',query)
    if not tokens: return []
    expression = ' AND '.join('"' + t + '"' for t in tokens)
    conn = db()
    rows = conn.execute("SELECT url,title,snippet(documents,2,'[',']','…',48) FROM documents WHERE documents MATCH ? ORDER BY bm25(documents) LIMIT ?", (expression, max(1,min(limit,50)))).fetchall()
    conn.close(); return [dict(zip(('url','title','excerpt'),r)) for r in rows]

def sync_help(workers=6, limit=None, refresh=False):
    DATA.mkdir(exist_ok=True); articles = DATA / 'articles'; articles.mkdir(exist_ok=True)
    try:
        robots=fetch('https://help.gohighlevel.com/robots.txt')
        (DATA/'help-robots.txt').write_bytes(robots)
        robot = urllib.robotparser.RobotFileParser(); robot.parse(robots.decode().splitlines())
        sitemap = fetch('https://help.gohighlevel.com/support/sitemap.xml'); (DATA / 'help-sitemap.xml').write_bytes(sitemap)
    except Exception as exc:
        cached=DATA/'help-sitemap.xml'
        urls=[e.text for e in ET.fromstring(cached.read_bytes()).iter() if e.tag.endswith('}loc') and '/support/solutions/articles/' in (e.text or '')] if cached.exists() else []
        report=dict(complete=False,discovered=len(set(urls)),archived=len(list(articles.glob('*.json'))),errors=[dict(stage='discovery',error=str(exc))],finished_at=datetime.now(timezone.utc).isoformat())
        (DATA/'help-status.json').write_text(json.dumps(report,indent=2)); report['indexed']=rebuild(); refresh_coverage(); return report
    urls = sorted(set(e.text for e in ET.fromstring(sitemap).iter() if e.tag.endswith('}loc') and '/support/solutions/articles/' in (e.text or '')))
    denied = [u for u in urls if not robot.can_fetch('GHL-Hub-Documentation',u)]
    urls = [u for u in urls if u not in denied]
    def target(url): return articles / (re.search(r'/articles/(\d+)',url).group(1) + '.json')
    pending = [u for u in urls if refresh or not target(u).exists()]
    if limit is not None: pending = pending[:limit]
    for p in articles.glob('*.json'):
        record=json.loads(p.read_text())
        if record.get('parser_version',1)<2:
            slug=re.sub(r'^\d+-?', '', record['url'].rsplit('/',1)[-1])
            record['title']=unquote(slug).replace('-',' ').strip() or record['url']
            record['title_source']='sitemap-url-slug'
            record['parser_version']=2
            p.write_text(json.dumps(record,ensure_ascii=False))
    errors = []; completed = 0; blocked=threading.Event()
    def ingest(url):
        if blocked.is_set(): return False
        raw = fetch(url); parser = ArticleParser(); parser.feed(raw.decode('utf-8',errors='replace')); title, body = parser.result()
        if len(body) < 100 or not title: raise ValueError('Missing article body/title; not indexing an error or challenge page')
        record = dict(url=url,title=title,text=body,fetched_at=datetime.now(timezone.utc).isoformat(),sha256=hashlib.sha256(raw).hexdigest(), parser_version=2)
        p = target(url); temp = p.with_suffix('.tmp'); temp.write_text(json.dumps(record,ensure_ascii=False)); temp.replace(p); return True
    with ThreadPoolExecutor(max_workers=max(1,min(workers,8))) as pool:
        futures = {pool.submit(ingest,u):u for u in pending}
        for f in as_completed(futures):
            try:
                if f.result(): completed += 1
            except DocsAccessBlocked as exc:
                blocked.set(); errors.append(dict(url=futures[f],error=str(exc)))
            except Exception as exc: errors.append(dict(url=futures[f], error=str(exc)))
            if (completed + len(errors)) % 100 == 0:
                progress=dict(downloaded=completed,errors=errors,pending=len(pending),discovered=len(urls),archived=sum(target(u).exists() for u in urls),complete=False)
                (DATA/'help-status.json').write_text(json.dumps(progress,indent=2))
                print(json.dumps(dict(downloaded=completed,errors=len(errors),pending=len(pending))),flush=True)
    report = dict(finished_at=datetime.now(timezone.utc).isoformat(),discovered=len(urls)+len(denied),robots_denied=denied,scheduled=len(pending),attempted=completed+len(errors),downloaded=completed,archived=sum(target(u).exists() for u in urls),errors=errors)
    report['complete'] = report['archived'] == len(urls) and not denied
    (DATA / 'help-status.json').write_text(json.dumps(report,indent=2)); report['indexed'] = rebuild(); refresh_coverage(); return report

def refresh_coverage():
    """Keep the missing-URL manifest current after every sync, including blocked ones."""
    sitemap=DATA/'help-sitemap.xml'
    urls=sorted({e.text for e in ET.fromstring(sitemap.read_bytes()).iter() if e.tag.endswith('}loc') and '/support/solutions/articles/' in (e.text or '')}) if sitemap.exists() else []
    archived={json.loads(p.read_text())['url'] for p in (DATA/'articles').glob('*.json')}
    operations_path=DATA/'operations.json'
    operations=json.loads(operations_path.read_text()) if operations_path.exists() else []
    missing=[u for u in urls if u not in archived]
    report=dict(generated_at=datetime.now(timezone.utc).isoformat(),api_operations=len(operations),api_v2_operations=sum(not o['domain'].startswith('v3/') for o in operations),api_v3_operations=sum(o['domain'].startswith('v3/') for o in operations),api_domains=len({o['domain'] for o in operations}),help_discovered=len(urls),help_archived=len(archived),help_missing=len(missing),help_complete=bool(urls) and not missing,live_account_verified=False,missing_urls=missing)
    (DATA/'coverage.json').write_text(json.dumps(report,indent=2))
    return report
