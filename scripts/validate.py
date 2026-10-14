#!/usr/bin/env python3
"""Validate radio.json and video.json (stdlib only).

  python scripts/validate.py            # schema-ish checks + dedupe + safety rules (offline, used in CI / PRs)
  python scripts/validate.py --probe    # also probe every radio stream as Chrome on an https page: https / CORS / direct-play
                                        # (printed only; health/eligibility is computed by the app, not stored in the list)

Safety rules (a station is rejected if it breaks one):
  - url/homepage are http(s); no credentials (user:pass@), no token-like query keys (token, sig, signature, auth, key,
    session, jwt, policy, expires, _lsu_sa_, key-pair-id...), no relay/proxy hosts ("proxy", "relay", tunnel or app hosts)
  - stream url not on a host that only serves per-play tokens / app-only resolvers (STATIONS_POLICY.md)
  - no DPRK (KP) stations
  - ids unique, urls unique, countries unique; video URLs must be plain public YouTube/Twitch addresses
"""
import json
import os
import re
import sys
import urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
TOKEN_KEYS = re.compile(r'(^|[_-])(token|sig|signature|auth|authorization|key|apikey|session|sess|jwt|policy|expires|hdnts|hdnea|hmac|wmsauth)($|[_-])|^_lsu_sa_$|^key-pair-id$', re.I)
BAD_HOSTS = re.compile(r'(\.trycloudflare\.com$|(^|\.)proxy\.|relay|teslatube)', re.I)
# STATIONS_POLICY.md: hosts whose streams are only reachable through per-play tokens or app-only resolvers / scraping relays
TOKEN_HOSTS = re.compile(r'((^|\.)bsod\.kr$|(^|\.)gscdn\.kbs\.co\.kr$|(^|\.)imbc\.com$|(^|\.)sbs\.co\.kr$)', re.I)
DPRK = re.compile(r'pyongyang|평양|조선중앙|korean central broadcasting|kcbs|voice of korea|조선의 ?소리|통일의 ?메아리', re.I)
ID_RE = re.compile(r'^[a-z]{2}-[a-z0-9-]{2,40}$')


def url_problems(u, field):
    p = []
    try:
        s = urllib.parse.urlsplit(u)
    except ValueError:
        return [f'{field}: not a URL']
    if s.scheme not in ('http', 'https'):
        p.append(f'{field}: scheme must be http(s)')
    if s.username or s.password:
        p.append(f'{field}: credentials in URL')
    if s.hostname and BAD_HOSTS.search(s.hostname):
        p.append(f'{field}: relay/proxy or our own host ({s.hostname})')
    if field == 'url' and s.hostname and TOKEN_HOSTS.search(s.hostname):
        p.append(f'{field}: host needs per-play tokens or an app-only resolver ({s.hostname}) - see STATIONS_POLICY.md')
    for k, _ in urllib.parse.parse_qsl(s.query, keep_blank_values=True):
        if TOKEN_KEYS.search(k):
            p.append(f'{field}: token-like query key "{k}"')
    return p


ALLOWED_RADIO_TOP = {'$schema', 'version', 'updated', 'countries'}
ALLOWED_COUNTRY = {'code', 'nameKo', 'flag', 'stations'}
ALLOWED_RADIO_ST = {'id', 'name', 'genre', 'url', 'homepage', 'lossless', 'codec', 'bitrateKbps', 'sampleRate', 'channels', 'language', 'tags', 'logo', 'icy', 'measured', 'unstable', 'note'}  # a624 measured fields; a706 unstable/note
YT_RE = re.compile(r'^https://(www\.|m\.)?(youtube\.com/(@[A-Za-z0-9._-]+|channel/[A-Za-z0-9_-]+|playlist\?list=[A-Za-z0-9_-]+|watch\?v=[A-Za-z0-9_-]{11})|youtu\.be/[A-Za-z0-9_-]{11})$')
TW_RE = re.compile(r'^https://(www\.)?twitch\.tv/[A-Za-z0-9_]{3,25}$')


def validate_radio(doc):
    errs = []
    for k in set(doc) - ALLOWED_RADIO_TOP:
        errs.append(f'radio.json: unknown top-level key {k}')
    if doc.get('version') != 1:
        errs.append('radio.json: version must be 1')
    ids, urls, codes = set(), set(), set()
    for ci, c in enumerate(doc.get('countries', [])):
        cw = f"countries[{ci}] {c.get('code', '?')}"
        for k in set(c) - ALLOWED_COUNTRY:
            errs.append(f'{cw}: unknown key {k}')
        if not re.fullmatch(r'[A-Z]{2}', str(c.get('code', ''))):
            errs.append(f'{cw}: bad country code')
        if c.get('code') == 'KP':
            errs.append(f'{cw}: DPRK stations are not listed (STATIONS_POLICY.md)')
        if c.get('code') in codes:
            errs.append(f'{cw}: duplicate country')
        codes.add(c.get('code'))
        for i, s in enumerate(c.get('stations', [])):
            where = f"{cw} stations[{i}] {s.get('id', '?')}"
            for k in set(s) - ALLOWED_RADIO_ST:
                errs.append(f'{where}: unknown key {k}')
            for k in ('id', 'name', 'url'):
                if not s.get(k):
                    errs.append(f'{where}: missing {k}')
            if s.get('id') and not ID_RE.match(s['id']):
                errs.append(f'{where}: bad id format')
            if DPRK.search(str(s.get('name', ''))):
                errs.append(f'{where}: DPRK stations are not listed (STATIONS_POLICY.md)')
            if s.get('id') in ids:
                errs.append(f'{where}: duplicate id')
            ids.add(s.get('id'))
            if s.get('url'):
                key = s['url'].split('#')[0].rstrip('/').lower()
                if key in urls:
                    errs.append(f'{where}: duplicate url')
                urls.add(key)
                errs += [f'{where}: {m}' for m in url_problems(s['url'], 'url')]
            if s.get('homepage'):
                errs += [f'{where}: {m}' for m in url_problems(s['homepage'], 'homepage')]
    return errs


PLATFORM_RE = re.compile(r'^https://(www\.youtube\.com|www\.twitch\.tv)/?$')
VIDEO_URL_RE = {'youtube': YT_RE, 'twitch': TW_RE}


def validate_video(doc):
    """v2: items[] {id, name, url, type: platform|channel|playlist|video, note?}"""
    errs = []
    for k in set(doc) - {'$schema', 'version', 'updated', 'items'}:
        errs.append(f'video.json: unknown top-level key {k}')
    if doc.get('version') != 2:
        errs.append('video.json: version must be 2')
    ids, urls = set(), set()
    for i, e in enumerate(doc.get('items', [])):
        where = f"items[{i}] {e.get('id', '?')}"
        for k in set(e) - {'id', 'name', 'url', 'type', 'note'}:
            errs.append(f'{where}: unknown key {k}')
        for k in ('id', 'name', 'url', 'type'):
            if not e.get(k):
                errs.append(f'{where}: missing {k}')
        if e.get('id') in ids:
            errs.append(f'{where}: duplicate id')
        ids.add(e.get('id'))
        u = str(e.get('url', ''))
        t = e.get('type')
        if t == 'platform':
            if not PLATFORM_RE.match(u):
                errs.append(f'{where}: platform url must be https://www.youtube.com or https://www.twitch.tv')
        elif t in ('channel', 'playlist', 'video'):
            if not (YT_RE.match(u) or TW_RE.match(u)):
                errs.append(f'{where}: url is not a plain public YouTube/Twitch address')
        else:
            errs.append(f'{where}: type must be platform|channel|playlist|video')
        if u.lower() in urls:
            errs.append(f'{where}: duplicate url')
        urls.add(u.lower())
        if e.get('note') is not None and len(str(e['note'])) > 200:
            errs.append(f'{where}: note too long')
    return errs


def flat_stations(doc):
    return [s for c in doc.get('countries', []) for s in c.get('stations', [])]


def probe_all(stations):
    """https / CORS / direct-play as Chrome 140 on https://example.org (any https origin works for the check)."""
    import concurrent.futures as cf
    import datetime
    import http.client
    import ssl
    origin = 'https://example.org'
    ua = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36'
    ctx = ssl.create_default_context()

    def get(url, hops=6, n=20000):
        mixed = False
        for _ in range(hops):
            u = urllib.parse.urlsplit(url)
            C = http.client.HTTPSConnection if u.scheme == 'https' else http.client.HTTPConnection
            try:
                c = C(u.hostname, u.port, timeout=12, **({'context': ctx} if u.scheme == 'https' else {}))
                c.request('GET', (u.path or '/') + ('?' + u.query if u.query else ''), headers={'User-Agent': ua, 'Origin': origin, 'Accept': '*/*'})
                r = c.getresponse()
            except Exception:
                return None, {}, b'', url, True
            if r.status in (301, 302, 303, 307, 308) and r.getheader('Location'):
                nxt = urllib.parse.urljoin(url, r.getheader('Location'))
                mixed = mixed or (url.startswith('https:') and nxt.startswith('http:'))
                url = nxt
                continue
            h = {k.lower(): v for k, v in r.getheaders()}
            try:
                b = r.read(n)
            except Exception:
                b = b''
            return r.status, h, b, url, mixed or url.startswith('http:')
        return None, {}, b'', url, True

    def cors(h):
        a = h.get('access-control-allow-origin', '')
        return a == '*' or a.rstrip('/') == origin

    def one(s):
        url = s['url']
        if url.startswith('http:'):
            st, h, b, fin, mixed = get('https:' + url[5:])
            if not st or st >= 400 or mixed:
                return {'https': False, 'cors': False, 'hls': url.split('?')[0].endswith('.m3u8'), 'directPlay': 'needs-relay'}
            url = 'https:' + url[5:]
        st, h, b, fin, mixed = get(url)
        if not st or st >= 400 or mixed:
            return {'https': not mixed and bool(st), 'cors': False, 'hls': False, 'directPlay': 'needs-relay'}
        hls = 'mpegurl' in h.get('content-type', '').lower() or b[:7] == b'#EXTM3U'
        ok = [cors(h)]
        if hls:
            text, base = b.decode('utf-8', 'replace'), fin
            lines = text.splitlines()
            if '#EXT-X-STREAM-INF' in text:
                i = next(i for i, l in enumerate(lines) if l.startswith('#EXT-X-STREAM-INF'))
                v = next((l for l in lines[i + 1:] if l.strip() and not l.startswith('#')), None)
                if v:
                    st2, h2, b2, base, _ = get(urllib.parse.urljoin(base, v.strip()))
                    ok.append(cors(h2)); lines = b2.decode('utf-8', 'replace').splitlines()
            m = re.search(r'#EXT-X-MAP:URI="([^"]+)"', '\n'.join(lines))
            seg = m.group(1) if m else next((l for l in lines if l.strip() and not l.startswith('#')), None)
            if seg:
                st3, h3, _, _, m3 = get(urllib.parse.urljoin(base, seg.strip()), n=1024)
                ok.append(cors(h3) and not m3)
        c = all(ok)
        dp = 'direct+effects' if c else ('needs-relay' if hls else 'direct-no-effects')
        return {'https': True, 'cors': c, 'hls': hls, 'directPlay': dp}

    from collections import Counter
    cnt = Counter()
    with cf.ThreadPoolExecutor(6) as ex:
        for s, res in zip(stations, ex.map(one, stations)):
            cnt[res['directPlay']] += 1
            print(f"{s['id']:32s} {res['directPlay']:18s} https={res['https']} cors={res['cors']} hls={res['hls']}", flush=True)
    print('directPlay:', dict(cnt), '(informational; not stored in the list)')


def main():
    radio = json.load(open(os.path.join(ROOT, 'radio.json'), encoding='utf-8'))
    video = json.load(open(os.path.join(ROOT, 'video.json'), encoding='utf-8'))
    errs = validate_radio(radio) + validate_video(video)
    for e in errs:
        print('ERROR', e)
    if errs:
        sys.exit(1)
    st = flat_stations(radio)
    print(f"ok: radio {len(st)} stations in {len(radio['countries'])} countries; video {len(video['items'])} items")
    if '--probe' in sys.argv:
        probe_all(st)


if __name__ == '__main__':
    main()
