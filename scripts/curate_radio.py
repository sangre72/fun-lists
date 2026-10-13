"""a624 radio curation (OFFLINE, repeatable - re-run monthly). The app never queries a station directory at runtime (a618);
this tool grows radio.json and records what was MEASURED (not what directories claim).

  python scripts/curate_radio.py candidates   # 1) staging: candidates.json (existing list + Radio Browser + broadcaster names)
  python scripts/curate_radio.py measure      # 2) connect each stream ~8 s -> measured.json (alive, codec, kbps, sr, ch, icy)
  python scripts/curate_radio.py build        # 3) select + write radio.json (diff-reviewable), report counts

measure runs at low priority with max 10 parallel probes (do not starve the live server on the same PC).
"""
import concurrent.futures as cf
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STAGE = os.path.join(ROOT, 'staging')
RB = 'https://de1.api.radio-browser.info'
UA = 'fun-lists-curate/1.0 (+https://github.com/sangre72/fun-lists)'
PROBE_S = 8
PARALLEL = 10
CAP = 70  # stations per country (by votes); FR (Radio France set) and KR are not capped
UNCAPPED = {'FR', 'KR'}

COUNTRY = {  # code: (nameKo, flag, top-voted pull size)
    'KR': ('한국', '🇰🇷', 150), 'FR': ('프랑스', '🇫🇷', 80), 'US': ('미국', '🇺🇸', 60), 'GB': ('영국', '🇬🇧', 50), 'JP': ('일본', '🇯🇵', 50),
    'DE': ('독일', '🇩🇪', 50), 'IT': ('이탈리아', '🇮🇹', 40), 'ES': ('스페인', '🇪🇸', 40), 'NL': ('네덜란드', '🇳🇱', 40), 'CH': ('스위스', '🇨🇭', 30),
    'AT': ('오스트리아', '🇦🇹', 30), 'CA': ('캐나다', '🇨🇦', 40), 'AU': ('호주', '🇦🇺', 40), 'BR': ('브라질', '🇧🇷', 40),
    'MX': ('멕시코', '🇲🇽', 15), 'AR': ('아르헨티나', '🇦🇷', 15), 'CU': ('쿠바', '🇨🇺', 10), 'CO': ('콜롬비아', '🇨🇴', 15), 'JM': ('자메이카', '🇯🇲', 10),
}
NAME_PULLS = {  # broadcaster sets pulled by name (country, query)
    'FR': ['France Inter', 'franceinfo', 'France Culture', 'France Musique', 'FIP', 'Mouv', 'ici '],
    'KR': ['KBS', 'MBC', 'SBS', 'EBS', 'CBS', 'TBS', 'BBS', '국악', 'YTN', 'Arirang', 'FEBC', 'PBC', 'WBS', 'BTN'],
    'GB': ['BBC Radio'], 'JP': ['NHK'], 'DE': ['Deutschlandfunk', 'BR-KLASSIK', 'WDR', 'NDR', 'SWR'], 'US': ['WQXR', 'KEXP', 'NPR', 'KUSC', 'WNYC'],
}
GENRE_TAGS = ['classical', 'jazz', 'lounge', 'k-pop', 'j-pop', 'ambient']
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from validate import url_problems  # same rules as the validator: no tokens/signatures/credentials, no relay/proxy hosts

DPRK = re.compile(r'pyongyang|평양|조선중앙|korean central broadcasting|kcbs|voice of korea|조선의 ?소리|통일의 ?메아리', re.I)


def get(path):
    req = urllib.request.Request(RB + path, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def slug(cc, name):
    s = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')[:36] or 'station'
    return f'{cc.lower()}-{s}'


def candidates():
    os.makedirs(STAGE, exist_ok=True)
    cur = json.load(open(os.path.join(ROOT, 'radio.json'), encoding='utf-8'))
    out = {}

    def add(cc, s, src, rb=None):
        url = (s.get('url_resolved') or s.get('url') or '').strip()
        name = (s.get('name') or '').strip()
        if not url.startswith('http') or not name or DPRK.search(name) or cc == 'KP' or (s.get('countrycode') or cc) == 'KP':
            return
        if re.search(r'[?&](token|session|sid|auth|key)=', url, re.I):
            return  # no tokens / session urls
        key = url
        if key in out:
            return
        out[key] = {'country': cc, 'name': name, 'url': url, 'homepage': s.get('homepage') or None, 'genre': s.get('genre') or (s.get('tags') or '').split(',')[0][:40] or None,
                    'tags': [t for t in (s.get('tags') or '').split(',') if t][:6], 'language': (s.get('language') or '').split(',')[0] or None, 'logo': s.get('favicon') or None,
                    'id': s.get('id'), 'votes': s.get('votes', 0), 'src': src, 'rb': rb}
    for g in cur['countries']:
        for s in g['stations']:
            add(g['code'], s, 'existing')
    for cc, (_, _, n) in COUNTRY.items():
        for s in get(f'/json/stations/search?countrycode={cc}&order=votes&reverse=true&hidebroken=true&limit={n}'):
            add(cc, s, 'top', s.get('stationuuid'))
        for q in NAME_PULLS.get(cc, []):
            for s in get(f'/json/stations/search?{urllib.parse.urlencode({"name": q, "countrycode": cc})}&order=votes&reverse=true&hidebroken=true&limit=40'):
                add(cc, s, 'name', s.get('stationuuid'))
        time.sleep(0.5)
    for t in GENRE_TAGS:
        for s in get(f'/json/stations/search?{urllib.parse.urlencode({"tag": t})}&order=votes&reverse=true&hidebroken=true&limit=40'):
            cc = s.get('countrycode') or ''
            if cc in COUNTRY:
                add(cc, s, f'tag:{t}', s.get('stationuuid'))
    json.dump(list(out.values()), open(os.path.join(STAGE, 'candidates.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('candidates', len(out), Counter(v['country'] for v in out.values()).most_common())


def probe(c):
    """~8 s of real stream: alive + codec/sr/ch from the decoder, kbps from bytes read, icy from the response headers"""
    r = {'url': c['url'], 'alive': False}
    try:
        req = urllib.request.Request(c['url'], headers={'User-Agent': 'Mozilla/5.0', 'Icy-MetaData': '1'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            r['icy'] = resp.headers.get('icy-metaint') is not None
            ctype = resp.headers.get('content-type', '')
            if 'mpegurl' in ctype or c['url'].split('?')[0].endswith(('.m3u8', '.m3u', '.pls')):
                r['playlist'] = True
            t0 = time.time()
            n = 0
            while time.time() - t0 < PROBE_S and n < 4_000_000:
                b = resp.read(16384)
                if not b:
                    break
                n += len(b)
            dt = max(0.5, time.time() - t0)
            r['kbpsRead'] = round(n * 8 / dt / 1000)
        p = subprocess.run(['ffprobe', '-v', 'error', '-rw_timeout', '10000000', '-user_agent', 'Mozilla/5.0', '-show_entries', 'stream=codec_type,codec_name,profile,sample_rate,channels,bit_rate:format=bit_rate', '-of', 'json', c['url']],
                           capture_output=True, text=True, timeout=25, creationflags=getattr(subprocess, 'BELOW_NORMAL_PRIORITY_CLASS', 0))
        j = json.loads(p.stdout or '{}')
        a = next((s for s in j.get('streams', []) if s.get('codec_type') == 'audio' and s.get('codec_name')), None)  # HLS: skip timed_id3/video streams
        if a:
            r.update(alive=True, codec=a.get('codec_name'), profile=a.get('profile'), sr=int(a.get('sample_rate') or 0) or None, ch=a.get('channels'),
                     kbps=round(int(a.get('bit_rate') or j.get('format', {}).get('bit_rate') or 0) / 1000) or None)
    except Exception as e:
        r['err'] = str(e)[:120]
    return r


def remeasure():
    """re-probe only rows whose first probe picked a non-audio stream or that are playlists (probe fix)"""
    cands = {c['url']: c for c in json.load(open(os.path.join(STAGE, 'candidates.json'), encoding='utf-8'))}
    meas = json.load(open(os.path.join(STAGE, 'measured.json'), encoding='utf-8'))
    redo = [cands[m['url']] for m in meas if m.get('playlist') or (m.get('codec') or '') in ('timed_id3', 'h264', 'hevc', 'bin_data')]
    with cf.ThreadPoolExecutor(PARALLEL) as ex:
        new = {r['url']: r for r in ex.map(probe, redo)}
    meas = [new.get(m['url'], m) for m in meas]
    json.dump(meas, open(os.path.join(STAGE, 'measured.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('remeasured', len(redo), 'alive now', sum(1 for r in new.values() if r['alive']))


def measure():
    cands = json.load(open(os.path.join(STAGE, 'candidates.json'), encoding='utf-8'))
    out = []
    with cf.ThreadPoolExecutor(PARALLEL) as ex:
        for i, r in enumerate(ex.map(probe, cands)):
            out.append(r)
            if i % 50 == 0:
                print('measured', i, '/', len(cands), flush=True)
    json.dump(out, open(os.path.join(STAGE, 'measured.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('alive', sum(1 for r in out if r['alive']), '/', len(out))


CODEC_RANK = {'flac': 5, 'alac': 5, 'aac': 3, 'opus': 3, 'vorbis': 2, 'mp3': 2}


def build():
    cands = {c['url']: c for c in json.load(open(os.path.join(STAGE, 'candidates.json'), encoding='utf-8'))}
    meas = {m['url']: m for m in json.load(open(os.path.join(STAGE, 'measured.json'), encoding='utf-8'))}
    today = date.today().isoformat()
    by_station = {}
    drops = Counter()
    for url, c in cands.items():
        m = meas.get(url, {})
        if not m.get('alive'):
            drops['dead/geo/err'] += 1
            continue
        if url_problems(url, 'url') or (c.get('homepage') and url_problems(c['homepage'], 'homepage')):
            drops['token/relay url'] += 1
            continue
        if re.search(r'(^|[^A-Za-z])TV([^A-Za-z]|$)', c['name']):
            drops['tv-channel'] += 1
            continue
        codec = (m.get('codec') or '').lower()
        if codec not in CODEC_RANK:
            drops[f'codec:{codec or "none"}'] += 1
            continue
        kbps = m.get('kbps') or (0 if m.get('playlist') else m.get('kbpsRead')) or 0  # HLS: bytes read = playlist text, not audio
        if kbps and kbps < 24:
            drops['too-low-bitrate'] += 1
            continue
        key = (c['country'], re.sub(r'[^a-z0-9가-힣]+', '', c['name'].lower()))
        score = (c['src'] == 'existing', CODEC_RANK[codec], kbps)
        rank = (c['src'] in ('existing', 'name'), c.get('votes') or 0)
        prev = by_station.get(key)
        if prev and prev[0] >= score:
            drops['duplicate'] += 1
            continue
        if prev:
            drops['duplicate'] += 1
        aac = 'HE-AAC' if codec == 'aac' and (m.get('profile') or '').upper().startswith('HE') else codec.upper()
        row = {'id': c.get('id') or slug(c['country'], c['name']), 'name': c['name'][:160], 'url': url}
        if c.get('genre'):
            row['genre'] = c['genre'][:40]
        if c.get('homepage', '') and str(c['homepage']).startswith('http'):
            row['homepage'] = c['homepage']
        if codec in ('flac', 'alac'):
            row['lossless'] = True
        row['codec'] = aac[:12]
        if kbps:
            row['bitrateKbps'] = int(min(2000, max(8, kbps)))
        if m.get('sr'):
            row['sampleRate'] = m['sr']
        if m.get('ch'):
            row['channels'] = m['ch']
        if c.get('language'):
            row['language'] = c['language'][:30]
        if c.get('tags'):
            row['tags'] = [t[:24] for t in c['tags'][:6]]
        if c.get('logo') and str(c['logo']).startswith('http'):
            row['logo'] = c['logo']
        row['icy'] = bool(m.get('icy'))
        row['measured'] = today
        by_station[key] = (score, row, rank)
    groups = defaultdict(list)
    ids = set()
    per_cc = defaultdict(list)
    for (cc, _), (_, row, rank) in by_station.items():
        per_cc[cc].append((rank, row))
    picked = []
    for cc, rows in per_cc.items():
        rows.sort(key=lambda x: (not x[0][0], -x[0][1]))
        keep = rows if cc in UNCAPPED else rows[:CAP]
        drops['over-country-cap'] += len(rows) - len(keep)
        picked += [(cc, r) for _, r in keep]
    for cc, row in picked:
        base = row['id'] if re.fullmatch(r'[a-z]{2}-[a-z0-9-]{2,40}', row['id']) else slug(cc, row['name'])
        i, n = base, 2
        while i in ids:
            i = f'{base[:37]}-{n}'
            n += 1
        ids.add(i)
        row['id'] = i
        groups[cc].append(row)
    doc = {'$schema': './radio.schema.json', 'version': 1, 'updated': today,
           'countries': [{'code': cc, 'nameKo': COUNTRY[cc][0], 'flag': COUNTRY[cc][1], 'stations': groups[cc]} for cc in COUNTRY if groups.get(cc)]}
    json.dump(doc, open(os.path.join(ROOT, 'radio.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
    total = sum(len(v) for v in groups.values())
    print('stations', total)
    print('per country', {cc: len(v) for cc, v in groups.items()})
    print('per codec', Counter(r['codec'] for v in groups.values() for r in v).most_common())
    print('dropped', dict(drops))


if __name__ == '__main__':
    {'candidates': candidates, 'measure': measure, 'remeasure': remeasure, 'build': build}[sys.argv[1]]()
