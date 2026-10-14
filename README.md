# fun-lists

**한국어** · [English](#english)

## Policy · 정책

Only **openly published, direct stream URLs**. No stations that need an API key, a login, per-play tokens, signed or expiring URLs, or an app-only resolver (for example the KBS/MBC/SBS token APIs). No DPRK (`KP`) stations. Apps play from this list only — no live external station directory at runtime.
Streams that need token renewal are not public streams, so we do not collect them.

**공개된 직접 스트림 주소만** 싣습니다. API 키·로그인·재생마다 받는 토큰·서명/만료 주소·앱 전용 리졸버(예: KBS/MBC/SBS 토큰 API)가 필요한 방송은 싣지 않습니다. 북한(`KP`) 방송은 싣지 않습니다. 앱은 이 목록에서만 재생하며, 실행 중에 외부 방송국 목록을 조회하지 않습니다.
토큰 갱신이 필요한 방송은 공개용이 아니므로 수집하지 않는다.

Details and enforcement · 자세한 규칙과 검사: [STATIONS_POLICY.md](STATIONS_POLICY.md)

인터넷 라디오와 영상 채널의 **공개 주소 목록**입니다. teslatube 앱이 이 저장소의 `radio.json` 을 받아 라디오 화면에 보여 줍니다.
이 저장소에는 **목록(데이터)만** 있습니다. 소리나 영상을 받거나 다시 보내는 서버는 없고, 앱은 방송사 주소에서 직접 재생합니다.
라이선스는 **CC0 1.0 (퍼블릭 도메인)** 입니다. 누구나 조건 없이 쓰고, 고치고, fork 할 수 있습니다.

## 파일

| 파일 | 내용 |
|---|---|
| `radio.json` | 추천 나라 순서대로 나라별 방송국. 방송국마다 아래 필드를 적습니다 |
| `video.json` | 영상 플랫폼 주소: YouTube(https://www.youtube.com), Twitch(https://www.twitch.tv). 항목마다 `id`, `name`, `url`, `type`(`platform`·`channel`·`playlist`·`video`), `note` 를 적습니다. teslatube 의 Twitch 재생은 `feature/twitch` 브랜치에만 있습니다 |
| `radio.schema.json`, `video.schema.json` | 형식(JSON Schema) |
| `scripts/validate.py` | 형식·중복·안전 규칙 확인(표준 라이브러리만). `--probe` 를 붙이면 각 스트림을 https 페이지의 브라우저처럼 열어 https·CORS·직접 재생 여부를 보여 줍니다(목록에 저장하지는 않습니다) |

방송국 필드는 다음과 같습니다.
- 필수: `id`, `name`, `url`
- 있으면 적음: `genre`, `homepage`, `lossless`
- 참고용(방송사가 밝힌 값): `codec`, `bitrateKbps`

상태 점검·대상 판정(AAR 등)은 앱이 직접 계산하며, 이 목록에는 넣지 않습니다.

## 넣지 않는 것

- 토큰·세션 값이 붙는 주소, 서명·만료 주소, 토큰 API·앱 전용 리졸버를 거쳐야 하는 방송, API 키·로그인이 필요한 방송
- 북한(`KP`) 방송
- 중계(relay)·프록시 주소(우리 것이든 남의 것이든)
- 개인 정보: 즐겨찾기, 시청 기록, PIN, 계정 등
- 로그인·결제가 필요한 방송

## 방송국·채널 제안하는 법

1. 방송사나 채널이 **공개한** 주소인지 확인합니다.
2. `radio.json` 의 해당 나라 `stations` 에 한 줄을 추가합니다. `id` 는 `나라코드-이름` 소문자입니다(예: `kr-cbs-music`). 영상 채널이면 `video.json` 에 추가합니다.
3. `python scripts/validate.py` 가 `ok` 인지 확인합니다.
4. Pull Request 를 보냅니다. 방송사가 요청하면 목록에서 바로 뺍니다.

## 앱에서 다른 목록 쓰기

이 저장소를 fork 한 뒤, 앱 서버 환경변수를 다음처럼 정하면 그 목록을 씁니다.
- `RADIO_STATIONS_URL`: 고정된 커밋의 raw 주소. 예: `https://raw.githubusercontent.com/<계정>/fun-lists/<커밋>/radio.json`
- `RADIO_STATIONS_SHA256`: 그 파일의 sha256 (선택)

받지 못하면 앱에 들어 있는 목록을 그대로 씁니다.

스트림 자체의 권리는 각 방송사·채널에 있습니다. 이 목록은 공개된 주소를 모은 것이며, 방송을 재배포하지 않습니다. 이 설명은 법률 자문이 아닙니다.

## 출처 · Attribution

Station data: Radio Browser (https://www.radio-browser.info), used under its free-use terms; stream URLs belong to their broadcasters.
방송국 데이터 출처: Radio Browser(radio-browser.info), 자유 이용 조건에 따라 사용합니다. 스트림 주소의 권리는 각 방송사에 있습니다.

CC0 은 이 저장소에서 **우리가 만든 부분**(선별·측정값·형식·스크립트)에만 적용됩니다. 방송국 이름·홈페이지·스트림 주소 자체의 권리는 각 방송사에 있습니다. 로고 이미지 주소는 싣지 않습니다.
CC0 covers only **our own work** here (curation, measurements, schema, scripts). Station names, homepages and stream URLs belong to their broadcasters. No logo image URLs are listed.

## 이용 조건 때문에 뺀 방송 · Removed for broadcaster terms (2026-10-14)

- BBC: 외부 플레이어 사용을 막으므로 모두 뺐습니다. BBC restricts its streams to approved third parties, so all BBC stations were removed.
- Radio France (France Inter, franceinfo, France Culture, France Musique, FIP, Mouv', ici): 서면 허가 없이 외부 앱이 목록으로 제공하는 것을 막으므로 모두 뺐습니다. Radio France forbids third-party apps from listing its streams without written permission, so all were removed.
- 출처가 확인되지 않는 재송출(relay) 주소도 뺐습니다. Restreams of unknown origin were removed.

---

## English

A list of **public addresses** for internet radio stations and video channels. The teslatube app fetches `radio.json` from this repository and shows it on its radio screen.
This repository holds **data only**. There is no server that receives or re-sends audio or video; the app plays from the broadcasters' own URLs.
Licence: **CC0 1.0 (public domain)**. Use, change and fork it freely, without conditions.

### Files

| File | Contents |
|---|---|
| `radio.json` | Stations grouped by country, in the recommended country order. Fields per station are below |
| `video.json` | Video platform addresses: YouTube (https://www.youtube.com) and Twitch (https://www.twitch.tv). Each item has `id`, `name`, `url`, `type` (`platform` / `channel` / `playlist` / `video`) and an optional `note`. Twitch playback in teslatube lives only on the `feature/twitch` branch |
| `radio.schema.json`, `video.schema.json` | JSON Schemas |
| `scripts/validate.py` | Checks schema, duplicates and safety rules (stdlib only). With `--probe`, it opens each stream like a browser on an https page and reports https / CORS / direct play. Results are printed, not stored |

Station fields:
- required: `id`, `name`, `url`
- when known: `genre`, `homepage`, `lossless`
- informational (as listed by the broadcaster): `codec`, `bitrateKbps`

Health and eligibility (AAR etc.) are computed by the app, not stored in this list.

### Not accepted

- URLs with tokens or session parameters, signed or expiring URLs, stations that need a token API, an app-only resolver, an API key or a login
- DPRK (`KP`) stations
- Relay or proxy URLs (ours or anyone's)
- Personal data: favourites, history, PINs, accounts
- Stations that require a login or payment

### Proposing a station or channel

1. Make sure the address is **published** by the broadcaster or channel.
2. Add one entry to the country's `stations` in `radio.json`. The `id` is `<country>-<name>` in lowercase, e.g. `kr-cbs-music`. Video channels go in `video.json`.
3. `python scripts/validate.py` must print `ok`.
4. Open a pull request. Stations are removed on the broadcaster's request.

### Using your own list in the app

Fork this repository, then set these on the app server:
- `RADIO_STATIONS_URL`: a raw URL pinned to a commit, e.g. `https://raw.githubusercontent.com/<you>/fun-lists/<commit>/radio.json`
- `RADIO_STATIONS_SHA256`: that file's sha256 (optional)

If the list can't be fetched, the app keeps its bundled list.

Rights in the streams belong to the broadcasters and channels. This list only collects publicly published addresses and does not redistribute any broadcast. This is not legal advice.
