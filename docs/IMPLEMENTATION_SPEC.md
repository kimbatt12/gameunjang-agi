# Gameunjang-agi Implementation Spec (구현 상세 명세)

작성일: 2026-06-16  
프로젝트 경로: `~/projects/gameunjang-agi`  
문서 상태: 초안 v0.1  
관련 문서: `docs/PRD.md`, `docs/TRD.md`

---

## 1. 목적

이 문서는 Gameunjang-agi MVP 구현 전에 필요한 실행 단위 기술 결정을 구체화한다. PRD/TRD에서 확정한 방향을 실제 구현 가능한 수준으로 세분화하며, 이후 사용자가 명시적으로 구현을 지시하면 OpenCode가 이 문서를 기준으로 개발한다.

---

## 2. 확정 결정 요약

1. 호스팅은 **Vercel**로 한다.
2. Vercel 단일 프로젝트로 구성하되, 디렉토리는 `frontend/`, `backend/`로 분리한다.
3. LLM 기본 provider는 **Upstage API**다.
4. LLM 대체 provider는 **OpenRouter API**다.
5. LLM 호출부는 provider adapter 구조로 만든다.
6. 외부 출처 보완은 **한국관광공사 API 응답에 포함된 공식 링크**로 제한한다.
7. 임의 웹 검색, 네이버/카카오/블로그/카페 결과는 MVP에서 제외한다.
8. 날씨 API는 **기상청 API** 기준으로 설계한다.
9. 사용량 제한은 일일 전체 제한이 아니라 **브라우저 세션당 10회 질문 제한**으로 한다.
10. 개발 실행은 OpenCode가 수행한다. Hermes는 기획과 검토에 집중한다.

---

## 3. MVP 범위

## 3.1 포함 기능

- 모바일 우선 React 챗 UI
- PC 반응형 대응
- 브라우저 로컬 대화 기록
- 브라우저 세션당 10회 질문 제한
- 국내 관광 관련 질문 판별
- 비관광 질문 거절
- 한국관광공사 API 메타데이터 인덱스
- 질문 기반 API 후보 선택
- 한국관광공사 API 호출
- Upstage 기반 답변 생성
- OpenRouter fallback adapter
- 기상청 API 기반 날씨 정보 보완
- API 응답 공식 링크 기반 보완 조회
- 출처 도메인 표시
- 주 1회 GitHub Actions 데이터 갱신
- GitHub Actions `workflow_dispatch` 수동 갱신
- 갱신 성공 시에만 current 데이터 교체

## 3.2 제외 기능

- 로그인
- 서버 측 대화 기록 저장
- 관리자 웹 페이지
- 웹앱 내 수동 갱신 버튼
- 유료 DB
- 고비용 벡터 DB
- 임의 웹 검색
- 네이버/카카오/블로그/카페 출처 사용
- 예약/결제 연동
- 다국어 지원
- 지도 기반 고급 UI

---

## 4. 프로젝트 구조

Vercel 단일 프로젝트로 배포하되, 소스 구조는 프론트엔드와 백엔드를 분리한다.
Milestone 0의 실제 구조와 아래 목표 구조의 차이는 `docs/PROJECT_BASELINE.md`에서 확인한다. 앱별 런타임, 패키지 매니저, 환경변수 예시는 각 앱 디렉터리가 소유한다.

```text
~/projects/gameunjang-agi/
  docs/
    PRD.md
    TRD.md
    IMPLEMENTATION_SPEC.md
  frontend/
    .env.example
    src/
      components/
        ChatInput.tsx
        ChatMessage.tsx
        SourceDomains.tsx
        SessionLimitNotice.tsx
      lib/
        apiClient.ts
        sessionLimit.ts
        localConversation.ts
      styles/
        globals.css
      App.tsx
      main.tsx
    public/
    package.json
    vite.config.ts
    tsconfig.json
  backend/
    .env.example
    app/
      __init__.py
      config.py
      schemas.py
      main.py
      guard/
        tourism_guard.py
      routing/
        api_router.py
        keyword_index.py
      clients/
        tour_api.py
        weather_kma.py
        official_link_fetcher.py
      llm/
        base.py
        upstage.py
        openrouter.py
        fake.py
      answer/
        composer.py
      cache/
        keys.py
        memory.py
      data_loader.py
    tests/
      test_tourism_guard.py
      test_api_router.py
      test_source_policy.py
      test_session_limit_contract.py
  api/
    chat.py
  data/
    current/
      tour_api_metadata.json
      tour_api_index.json
      refresh_manifest.json
    staging/
  scripts/
    refresh_tour_api_metadata.py
    validate_data_snapshot.py
  .github/
    workflows/
      refresh-data.yml
  README.md
  vercel.json
```

### 4.1 Vercel 엔트리포인트

- `api/chat.py`는 Vercel Python Function의 얇은 adapter다.
- 실제 비즈니스 로직은 `backend/app/` 내부에 둔다.
- 향후 다른 호스팅으로 이전할 때 `api/chat.py`만 교체 가능해야 한다.

---

## 5. 환경변수

`backend/.env.example`에 아래 키를 placeholder 예시값으로 정의한다. 실제 값은 로컬 `.env` 또는 배포 secret store에서 관리한다. 브라우저에 노출 가능한 프론트엔드 공개 설정은 `frontend/.env.example`에만 둔다.

```text
# 공공데이터포털 API: 한국관광공사, 기상청 단기예보 조회서비스
TOUR_API_SERVICE_KEY=replace-with-tour-api-service-key

# LLM provider
LLM_PROVIDER=upstage
LLM_FALLBACK_PROVIDER=openrouter

# Upstage
UPSTAGE_API_KEY=replace-with-upstage-api-key
UPSTAGE_MODEL=replace-with-upstage-model-name

# OpenRouter fallback
OPENROUTER_API_KEY=replace-with-openrouter-api-key
OPENROUTER_MODEL=replace-with-openrouter-model-name

# Runtime limits
MAX_BROWSER_SESSION_QUESTIONS=10
MAX_USER_MESSAGE_CHARS=1000
ANSWER_MAX_ITEMS=5
ANSWER_MAX_TOKENS=800

# Source policy
ALLOWED_SOURCE_DOMAINS=go.kr,or.kr,visitkorea.or.kr,data.go.kr
```

---

## 6. LLM Provider 정책

## 6.1 기본/fallback

- 기본 provider: `upstage`
- fallback provider: `openrouter`
- provider 선택은 `LLM_PROVIDER`, `LLM_FALLBACK_PROVIDER` 환경변수로 제어한다.
- provider adapter는 동일한 인터페이스를 구현해야 한다.

## 6.2 Adapter 인터페이스

```text
LLMClient
  classify_tourism_question(input) -> GuardResult
  plan_api_calls(input, api_index) -> ApiCallPlan
  compose_answer(input, api_results, weather, sources) -> Answer
```

## 6.3 호출 정책

1. 먼저 LLM scope classifier로 국내 관광 관련성 판별을 수행한다.
2. classifier는 `domestic_tourism` 또는 `out_of_scope` label만 반환한다.
3. `out_of_scope`이면 외부 검색/Tourism/KMA API 호출 없이 안내 응답을 반환한다.
4. classifier provider가 없거나 사용할 수 없거나 응답 label이 올바르지 않으면 안전한 범위 안내로 종료한다.
5. `domestic_tourism`이면 deterministic API 후보 생성 후 compact 후보 메타데이터를 LLM에 전달해 API route 순서를 선택한다.
6. Upstage 호출 실패 시 설정된 OpenRouter fallback을 시도한다.
7. API route LLM이 실패하거나 malformed/unknown ID를 반환하면 deterministic metadata scoring 결과로 fallback한다.
8. 답변 생성 fallback도 실패하면 API 결과 기반의 최소 템플릿 답변 또는 오류 안내를 반환한다.
9. 답변 생성 응답 토큰은 기본 800 tokens 이내로 제한하고, scope classifier와 route selector는 작은 prompt와 낮은 `max_tokens`로 운영한다.

## 6.4 모델 후보 결정 필요 항목

구현 전 또는 구현 초기 단계에서 아래를 확정해야 한다.

- `UPSTAGE_MODEL`
- `OPENROUTER_MODEL`
- provider별 timeout
- provider별 최대 입력/출력 토큰
- fallback 발생 조건

---

## 7. 질문 처리 플로우

```text
POST /api/chat
  ↓
1. 요청 스키마 검증
  ↓
2. message 길이 제한 검사
  ↓
3. 브라우저 세션 제한은 클라이언트에서 1차 적용
  ↓
4. 입력 정규화
  ↓
5. LLM scope classifier 국내 관광 관련성 판별
  ├─ out_of_scope → rejection 응답
  ├─ provider 누락/오류/비정상 label → rejection 응답
  └─ domestic_tourism → 계속
  ↓
6. API 메타데이터 인덱스 검색 및 deterministic 라우팅 후보 생성
  ↓
7. LLM에 compact 후보 메타데이터를 전달해 API route 선택
  ↓
8. malformed/unknown/error이면 deterministic 후보 순서로 fallback
  ↓
9. 한국관광공사 API 호출
  ↓
10. 필요 시 기상청 API 호출
  ↓
11. API 응답에 포함된 공식 링크만 보완 조회
  ↓
12. 답변 생성
  ↓
13. 출처 도메인 정리
  ↓
14. 응답 반환
```

---

## 8. 브라우저 세션당 10회 제한

## 8.1 기준

- 기준: 브라우저 세션
- 저장소: `sessionStorage`
- 키 예시: `gameunjang_agi_question_count`
- 최대 질문 수: 10회

## 8.2 UX

- 1~9회: 정상 질문 가능
- 10회: 마지막 질문 가능
- 11회부터: 전송 차단

제한 도달 메시지:

```text
이번 브라우저 세션의 질문 한도 10회에 도달했습니다. 새 세션을 시작하거나 대화를 초기화한 뒤 다시 이용해 주세요.
```

## 8.3 서버 측 보완

로그인이 없으므로 강한 서버 제한은 MVP 범위가 아니다. 다만 아래는 고려한다.

- 요청 본문에 `clientSessionQuestionCount` 포함
- 서버는 값이 비정상적으로 크거나 누락된 경우에도 서버 기준 검증을 적용한다.
- abuse 방지는 향후 기능으로 둔다.

---

## 9. 한국관광공사 API 전략

## 9.1 전체 API 후보화

- 한국관광공사 관련 공공데이터 API는 전부 메타데이터 후보로 수집한다.
- 질문과 맞는 API 후보만 선별 호출한다.
- 질문과 메타데이터 인덱스를 비교해 API 후보를 고른다.
- 지역이 없는 질문은 서울 등 특정 지역으로 보정하지 않고 전국구 요청으로 처리한다.

## 9.2 MVP 우선 API 유형

실제 호출 우선순위는 아래 순서로 둔다.

1. 지역 기반 관광정보
2. 키워드 검색
3. 상세정보
4. 이미지 정보
5. 행사/축제
6. 숙박
7. 음식점
8. 여행코스
9. 지역코드/시군구코드
10. 분류코드

## 9.3 API 메타데이터 필수 필드

- `id`
- `name`
- `description`
- `endpoint`
- `method`
- `requiredParams`
- `optionalParams`
- `responseFields`
- `categories`
- `examples`
- `sourceDomain`
- `lastCheckedAt`

## 9.4 원자적 갱신

- 갱신 결과는 `data/staging/`에 생성한다.
- 검증 성공 시에만 `data/current/`를 교체한다.
- 하나라도 실패하면 기존 `data/current/`를 유지한다.

---

## 10. API 라우팅 / 의미검색

이 단계는 LLM scope classifier가 `domestic_tourism`으로 수락한 질문에만 적용한다. 키워드와 라우팅 메타데이터는 deterministic 후보 생성에 사용하고, compact API 메타데이터는 LLM route selector가 최종 후보 순서를 고르는 데 사용한다.

## 10.1 MVP 방식

임베딩 없이 시작한다.

사용 요소:

- 질문 정규화
- 지역명 사전
- 관광 카테고리 키워드
- 동의어 사전
- API 메타데이터 `searchText`
- API 카테고리 가중치
- LLM route selector 입력용 compact 후보 메타데이터: `id`, `endpoint`, 카테고리, 지역/전국구 가능 여부, 우선순위, 설명, `searchText`

## 10.2 후보 선택

- top-k 기본값: 3
- 관련 점수가 낮으면 되묻기 또는 정보 부족 응답
- LLM에는 전체 API 목록이 아니라 top-k 후보만 전달한다.
- LLM route selector는 strict JSON 후보 ID 목록을 반환해야 하며, 알 수 없는 ID나 malformed output 또는 provider 오류는 deterministic 후보 순서로 fallback한다.
- 지역이 감지되지 않은 질문은 전국구로 간주하고, 가능한 Tourism API 호출에서 `areaCode`를 생략한다.

## 10.3 예시 매핑

| 질문 유형 | 우선 API |
|---|---|
| “부산 실내 관광지 추천” | 지역 기반 관광정보, 키워드 검색, 상세정보 |
| “이번 달 서울 축제” | 행사/축제, 지역코드 |
| “강릉 2박 3일 코스” | 여행코스, 관광정보, 음식점, 숙박 |
| “제주 비 오는 날 갈 곳” | 관광정보, 키워드 검색, 기상청 API |
| “스키장 추천해줘” | 전국구 관광정보 |

---

## 11. 기상청 API 전략

## 11.1 사용 기준

- 날씨 API는 기상청 API를 기준으로 한다.
- 질문에 날짜/날씨/일정 조건이 있을 때 호출한다.
- 날짜/날씨/일정 조건이 있는 질문에만 호출한다.

## 11.2 필요 기능

- 지역명 → 좌표 또는 행정구역 매핑
- 좌표 → 기상청 격자 변환
- 현재/단기 예보 조회
- 실패 시 graceful degradation

## 11.3 실패 처리

기상청 API 실패 시:

- 관광 답변은 계속 생성한다.
- 날씨 고려가 제한적이라는 warning을 포함한다.
- 출처는 관광 정보 공식/공공 도메인으로 유지한다.

---

## 12. 공식 링크 보완 조회 정책

## 12.1 원칙

- MVP 보완 조회는 한국관광공사 API 응답에 포함된 공식 링크 기준으로 수행한다.
- 보완 조회는 한국관광공사 API 응답에 포함된 공식 링크로 제한한다.
- 공식 링크가 있는 경우에만 보완 조회를 수행한다.

## 12.2 허용 도메인

- `*.go.kr`
- `*.or.kr`
- `visitkorea.or.kr`
- `data.go.kr`
- 관광지 공식 홈페이지로 확인 가능한 API 응답 링크

## 12.3 제외

- 네이버 검색
- 카카오 검색
- 개인 블로그
- 카페
- 커뮤니티
- 광고성 페이지
- API 응답에 포함되지 않은 임의 URL

## 12.4 보완 조회 대상

- 운영시간
- 입장료/비용
- 공식 안내 URL
- 휴무일
- 행사 기간
- 주의사항

---

## 13. API 응답 스키마

## 13.1 요청

```json
{
  "message": "이번 주말 아이랑 부산에서 갈 만한 실내 관광지 추천해줘",
  "localConversationId": "browser-local-id",
  "clientSessionQuestionCount": 3,
  "clientContext": {
    "timezone": "Asia/Seoul"
  }
}
```

## 13.2 관광 답변

```json
{
  "type": "answer",
  "isTourismRelated": true,
  "answer": "추천 답변 본문",
  "items": [
    {
      "title": "관광지 이름",
      "reason": "추천 이유",
      "address": "주소",
      "openingHours": "운영시간 또는 확인된 정보 없음",
      "price": "비용 또는 확인된 정보 없음",
      "officialUrl": "https://...",
      "mapUrl": "https://..."
    }
  ],
  "sourceDomains": ["visitkorea.or.kr", "data.go.kr"],
  "warnings": []
}
```

## 13.3 비관광 질문 거절

```json
{
  "type": "rejection",
  "isTourismRelated": false,
  "answer": "이 서비스는 국내 관광 관련 질문에만 답변할 수 있습니다. 여행지, 관광지, 축제, 숙소, 음식점, 여행코스와 관련된 질문을 입력해 주세요.",
  "sourceDomains": [],
  "warnings": []
}
```

## 13.4 세션 제한 응답

클라이언트에서 우선 차단하지만, 서버 응답 형식은 아래와 같이 정의한다.

```json
{
  "type": "limit_exceeded",
  "isTourismRelated": null,
  "answer": "이번 브라우저 세션의 질문 한도 10회에 도달했습니다. 새 세션을 시작하거나 대화를 초기화한 뒤 다시 이용해 주세요.",
  "sourceDomains": [],
  "warnings": ["browser_session_question_limit_exceeded"]
}
```

---

## 14. 답변 포맷

## 14.1 추천 목록

- 기본 추천 개수: 최대 5개
- 사용자가 더 적은 개수를 요구하면 그 개수를 따른다.
- 정보가 부족하면 5개 미만이어도 된다.

각 추천 항목 포함 정보:

- 이름
- 추천 이유
- 주소/지역
- 운영시간
- 비용
- 공식 링크
- 지도 링크
- 날씨 고려 사항

## 14.2 일정 추천

일정 추천 기본 형식:

```text
1일차
- 오전: ...
- 점심: ...
- 오후: ...
- 저녁: ...
- 숙박: ...

2일차
...

출처: visitkorea.or.kr, data.go.kr, weather.go.kr
```

## 14.3 정보 없음

확인되지 않은 값은 아래처럼 표시한다.

```text
운영시간: 확인된 정보 없음
비용: 확인된 정보 없음
```

확인된 정보만 사용한다.

---

## 15. Vercel 배포 구조

## 15.1 단일 프로젝트

- Vercel 프로젝트 하나로 배포한다.
- repository root 기준으로 설정한다.
- 프론트엔드와 백엔드 코드는 디렉토리로 분리한다.

## 15.2 Frontend

- `frontend/`에 Vite React 앱을 둔다.
- 빌드 결과를 Vercel이 정적 파일로 제공한다.

## 15.3 Backend

- `api/chat.py`는 Vercel Python Function adapter다.
- `api/chat.py`는 `backend/app/main.py` 또는 service 함수를 호출한다.
- 핵심 로직은 `backend/app/`에 둔다.

## 15.4 로컬 개발

구현 단계에서 아래 중 하나를 선택한다.

- Vite dev server + Python API local server
- Vercel CLI 기반 local dev

MVP 구현 전 결정 필요.

---

## 16. 테스트 계획

## 16.1 Backend unit tests

- 관광 관련성 판별
- 비관광 질문 거절
- API 라우팅 점수 계산
- 공식 링크 보완 조회 정책
- 기상청 API 실패 처리
- LLM fallback 처리
- 응답 스키마 생성

## 16.2 Frontend tests

- 질문 입력
- 세션당 10회 제한
- 제한 도달 메시지
- 로컬 대화 저장/삭제
- 출처 도메인 렌더링

## 16.3 Integration tests

- 관광 질문 → API 후보 선택 → mock API 결과 → 답변 생성
- 비관광 질문 → LLM scope classification 후 Tourism/KMA API 호출 없이 거절
- 날씨 조건 질문 → 기상청 client 호출
- 공식 링크 없는 결과 → 보완 조회 생략
- Upstage 실패 → OpenRouter fallback

---

## 17. 구현 단계 초안

실제 구현은 사용자가 명시적으로 지시한 이후 OpenCode로 수행한다.

1. 프로젝트 기본 구조 생성
2. 문서/README/.env.example 정리
3. 프론트엔드 Vite React 기본 챗 UI 생성
4. 브라우저 세션당 10회 제한 구현
5. Vercel Python Function adapter 생성
6. backend 스키마/설정 모듈 구현
7. LLM-first 관광 관련성 guard 구현
8. API 메타데이터 JSON 샘플과 loader 구현
9. API 라우팅 키워드 인덱스 구현
10. LLM adapter base/upstage/openrouter/fake 구현
11. 한국관광공사 API client 구현
12. 기상청 API client 구현
13. 공식 링크 보완 조회 client 구현
14. 답변 composer 구현
15. `/api/chat` 통합
16. GitHub Actions 데이터 갱신 workflow 작성
17. 테스트 작성 및 실행
18. Vercel 배포 설정

---

## 18. 남은 확인 사항

구현 전에 또는 구현 초기에 확정해야 한다.

1. `UPSTAGE_MODEL` 기본 모델명
2. `OPENROUTER_MODEL` fallback 모델명
3. 한국관광공사 API 실제 목록 및 응답 포맷
4. 기상청 단기예보 조회서비스 endpoint(`getVilageFcst`)의 요청 파라미터 세부값
5. Vercel Python Function 실행시간 제한 내 복잡 일정 추천 가능 여부
6. 지도 링크 생성 방식
7. Vercel 로컬 개발 방식
