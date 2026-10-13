# Stations policy

This list holds only **openly published, direct stream URLs** — addresses a broadcaster or station publishes for anyone to play, that work as they are, for everyone, without extra steps.

**Reason:** streams that need token renewal are not public streams, so we do not collect them.
토큰 갱신이 필요한 방송은 공개용이 아니므로 수집하지 않는다.

## Not listed

| Not listed | Examples |
|---|---|
| Streams that need an API key, a login, an account or a payment | key in the query, login-only players |
| Per-play tokens, signed or expiring URLs | `token=`, `signature=`, `Policy=` + `Key-Pair-Id=`, `expires=`, `_lsu_sa_=`, `wmsauth=` |
| Streams only reachable through an app-only resolver or a player API that issues a fresh URL per play | broadcaster player APIs that hand out tokenised URLs (for example the KBS, MBC and SBS web-player APIs) |
| Relays, proxies or scraping mirrors of someone else's stream | third-party relay hosts, tunnels |
| Stations from the DPRK (country code `KP`) | |
| Personal data | favourites, history, PINs, accounts |

## How it is enforced

- `scripts/validate.py` rejects token-like query keys, credentials in URLs, relay/proxy hosts, hosts that only serve per-play tokens, and DPRK stations. A pull request must pass it.
- `scripts/curate_radio.py` (offline curation) skips directory results that break these rules, and stops with exit code 2 — writing nothing — if such a station is already in `radio.json` or reaches the output.
- Apps that use this list play stations **from the list only**. They do not query a live station directory at runtime, and they do not resolve or renew stream URLs.

If a station's only working address needs token renewal, it stays out of the list until the broadcaster publishes a plain public URL.
