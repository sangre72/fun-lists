# fun-lists

**한국어** · [English](#english)

인터넷 라디오와 영상 채널의 **공개 주소 목록**입니다. teslatube 앱이 이 저장소의 `radio.json` 을 받아 라디오 화면에 보여 줍니다.
이 저장소에는 **목록(데이터)만** 있습니다. 소리나 영상을 받거나 다시 보내는 서버는 없고, 앱은 방송사 주소에서 직접 재생합니다.
라이선스는 **CC0 1.0 (퍼블릭 도메인)** 입니다. 누구나 조건 없이 쓰고, 고치고, fork 할 수 있습니다.

## 파일

| 파일 | 내용 |
|---|---|
| `radio.json` | 추천 나라 순서대로 나라별 방송국. 방송국마다 아래 필드를 적습니다 |
| `video.json` | 공개 YouTube 채널·재생목록·영상과 Twitch 채널 주소. 지금은 비어 있습니다. 앱에 기본 추천 목록이 없기 때문입니다 |
| `radio.schema.json`, `video.schema.json` | 형식(JSON Schema) |
| `scripts/validate.py` | 형식·중복·안전 규칙 확인(표준 라이브러리만). `--probe` 를 붙이면 각 스트림을 https 페이지의 브라우저처럼 열어 https·CORS·직접 재생 여부를 보여 줍니다(목록에 저장하지는 않습니다) |

방송국 필드는 다음과 같습니다.
- 필수: `id`, `name`, `url`
- 있으면 적음: `genre`, `homepage`, `lossless`
- 참고용(방송사가 밝힌 값): `codec`, `bitrateKbps`

상태 점검·대상 판정(AAR 등)은 앱이 직접 계산하며, 이 목록에는 넣지 않습니다.

## 넣지 않는 것

- 토큰·세션 값이 붙는 주소, 비공식 토큰 API 를 거쳐야 하는 방송
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

---

## English

A list of **public addresses** for internet radio stations and video channels. The teslatube app fetches `radio.json` from this repository and shows it on its radio screen.
This repository holds **data only**. There is no server that receives or re-sends audio or video; the app plays from the broadcasters' own URLs.
Licence: **CC0 1.0 (public domain)**. Use, change and fork it freely, without conditions.

### Files

| File | Contents |
|---|---|
| `radio.json` | Stations grouped by country, in the recommended country order. Fields per station are below |
| `video.json` | Public YouTube channels / playlists / videos and Twitch channel URLs. Empty for now, because the app ships no default list |
| `radio.schema.json`, `video.schema.json` | JSON Schemas |
| `scripts/validate.py` | Checks schema, duplicates and safety rules (stdlib only). With `--probe`, it opens each stream like a browser on an https page and reports https / CORS / direct play. Results are printed, not stored |

Station fields:
- required: `id`, `name`, `url`
- when known: `genre`, `homepage`, `lossless`
- informational (as listed by the broadcaster): `codec`, `bitrateKbps`

Health and eligibility (AAR etc.) are computed by the app, not stored in this list.

### Not accepted

- URLs with tokens or session parameters, or stations that need an unofficial token API
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
