# Backend Architecture

문서 상태: Living document
기획 기준: 제품 요구사항, 기술 요구사항, 구현 명세의 최신 합의

## Purpose

`backend/`는 국내 관광 질문 처리, 공공데이터 조회, provider 연동, 답변 생성 정책을 담당한다. 프론트엔드는 백엔드 API를 통해서만 비밀값이 필요한 기능을 사용한다.

## Boundaries

- 프론트엔드 UI, 브라우저 로컬 저장, 화면 상태 관리는 `frontend/`가 소유한다.
- MVP 대화 기록은 브라우저 로컬 저장 범위로 둔다.
- 비밀값은 환경변수로만 읽고 로컬/배포 환경에서 관리한다.
- Vercel Python Function 같은 배포 엔트리포인트는 얇은 adapter로 유지한다.
- `backend/`는 별도 저장소로 분리 가능해야 하며, 자체 Python 패키지/툴링 기준을 소유한다.

## Stack

- 런타임 기준: Python `>=3.14,<3.15` when `pyproject.toml` exists.
- 앱 구조: FastAPI-compatible ASGI app 또는 동일한 service 함수 중심 구조.
- 배포: Vercel Python Functions, ASGI 서버, Docker 기반 호스팅으로 이전 가능하게 유지한다.
- 데이터: 초기 MVP는 정적 JSON 인덱스와 파일/메모리 캐시를 우선한다.

## Planned Structure

구현 시점의 실제 구조가 우선이며, 아래는 초기 계획이다.

```text
backend/
  app/
    main.py
    config.py
    schemas.py
    guard/             # 국내 관광 관련성 판별
    routing/           # API 후보 선택, 키워드/의미검색
    clients/           # tour API, weather, official link fetcher
    llm/               # base, upstage, openrouter, fake
    answer/            # 답변 생성/출처 정리
    cache/             # 캐시 키와 저장소
    data_loader.py
  tests/
```

## Responsibilities

### Provider / LLM

- Upstage API를 기본 provider로 사용한다.
- OpenRouter API를 fallback provider로 지원한다.
- provider adapter 인터페이스 뒤에 구현을 숨긴다.
- 명확한 비관광 질문은 LLM 호출을 건너뛰고 범위 안내로 처리한다.
- 비용 통제를 위해 캐싱, 소형 모델, 토큰 제한을 고려한다.

### Tourism Data

- 한국관광공사 API 메타데이터를 후보 도구로 관리한다.
- 질문과 메타데이터를 비교해 필요한 API만 호출한다.
- API 응답은 답변에 필요한 normalized item으로 정리한다.
- 확인 범위 밖의 정보는 “확인된 정보 없음”으로 처리한다.

### Weather

- 날씨 API는 기상청 API 기준으로 설계한다.
- 날짜/지역/날씨 조건 또는 일정 추천에 필요할 때 호출한다.
- 실패 시 관광 답변은 가능한 범위에서 계속 생성하고 warning을 포함한다.

### Session / Limits

- 브라우저 세션당 10회 제한은 프론트엔드가 1차 적용한다.
- 백엔드는 클라이언트 제공 카운트를 참고 정보로만 다룬다.
- MVP rate limit은 브라우저 세션 기준의 가벼운 제한에 집중한다.

### Source Policy

- 보완 조회는 한국관광공사 API 응답에 포함된 공식 링크로 제한한다.
- `*.go.kr`, `*.or.kr`, `visitkorea.or.kr`, `data.go.kr`, 확인 가능한 공식 홈페이지를 우선한다.
- 공식 출처 도메인과 API 제공 링크 중심으로 답변 근거를 구성한다.
- 응답에는 출처 도메인을 포함한다.

## Validation Expectations

`backend/pyproject.toml`이 생기면 `backend/`에서 최소한 아래를 실행한다.

- `ruff check .`
- `ruff format --check .`
- `pytest`

추가 스크립트가 생기면 변경 범위에 맞는 가장 작은 검증을 함께 실행한다.

## Architecture Rules

- 핵심 비즈니스 로직은 플랫폼 중립 서비스 모듈에 둔다.
- provider별 SDK나 API 형식은 adapter에 격리한다.
- 백엔드 실행과 검증은 Python 도구와 설정으로 완결한다.
- 정적 데이터 갱신은 성공 시에만 현재 스냅샷을 교체한다.
