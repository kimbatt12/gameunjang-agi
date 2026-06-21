# Gameunjang-agi TRD (기술 요구사항 문서)

작성일: 2026-06-15  
프로젝트 경로: `~/projects/gameunjang-agi`  
문서 상태: 초안 v0.1

---

## 1. 기술 목표

Gameunjang-agi는 한국관광공사 공공데이터 API를 기반으로 국내 관광 질문에 답변하는 저비용 웹 챗봇이다. 기술 설계의 최우선 목표는 다음과 같다.

1. 월 1달러 미만 운영비
2. 일 1,000쿼리 미만 처리
3. 특정 벤더 종속 최소화
4. 한국관광공사 API 전체를 후보 도구로 활용
5. API 메타데이터 의미검색 기반 라우팅
6. API 데이터 우선 답변
7. 허용된 공식/공공 출처만 보완 사용
8. 주 1회 및 수동 데이터 갱신
9. 갱신 실패 시 기존 정상 데이터 유지
10. 모바일 우선 반응형 UI

---

## 2. 핵심 기술 결정

## 2.1 권장 스택

### 프론트엔드

- React
- TypeScript
- Vite 또는 Next.js 중 선택 가능
- 초기 추천: **Vite + React + TypeScript**

선정 이유:

- 정적 배포가 쉬움
- Cloudflare Pages, Vercel, Netlify, GitHub Pages 등으로 이전 가능
- 특정 서버리스 플랫폼에 강하게 종속되지 않음
- 모바일 우선 UI 구현이 단순함

### 백엔드

- Python
- FastAPI 호환 구조
- 서버리스 함수 또는 경량 ASGI 서버로 배포 가능하게 설계

선정 이유:

- API 라우팅, 데이터 처리, 배치 스크립트 작성에 적합
- Vercel Python Functions, Render, Fly.io, Railway, Docker 기반 호스팅 등으로 이전 가능
- 특정 벤더 전용 언어/런타임 의존을 피할 수 있음

### 데이터 저장

- 초기 MVP: 정적 JSON 파일
- 위치: repository 내부 `data/` 또는 빌드 산출물
- DB 미사용

선정 이유:

- 무료
- 운영 복잡도 낮음
- 일 1,000쿼리 미만에서 충분
- 배치 성공 시 정적 파일 교체만으로 갱신 가능

### 배치/스케줄러

- GitHub Actions cron
- GitHub Actions `workflow_dispatch` 수동 실행

선정 이유:

- 무료 티어 활용 가능
- 관리자 사용자가 1명이라 웹 관리자 페이지가 불필요
- 수동 갱신 버튼 요구를 GitHub Actions 수동 실행으로 대체 가능
- 특정 호스팅 벤더 종속 없음

### LLM

- API 기반 호출을 사용한다.
- 기본 provider는 **Upstage API**다.
- 대체 provider로 **OpenRouter API**를 지원한다.
- LLM 호출부는 벤더 중립 어댑터로 설계한다.

주의:

- Upstage와 OpenRouter 중 하나가 장애/가격 변경/모델 변경을 겪어도 다른 공급자로 교체 가능해야 한다.
- API 키는 Vercel 환경변수로 관리하고 클라이언트 번들은 공개 설정만 포함한다.

---

## 3. 아키텍처 개요

```text
[Browser]
  └─ React Chat UI
      ├─ localStorage / IndexedDB 대화 기록
      ├─ 브라우저 세션당 10회 대화 제한
      └─ /api/chat 호출

[Backend API]
  ├─ Tourism Guard
  │   └─ 국내 관광 관련 질문 여부 판별
  ├─ API Router
  │   └─ 질문과 API 메타데이터 의미검색
  ├─ Tour API Client
  │   └─ 한국관광공사 API 호출
  ├─ Weather Client
  │   └─ 무료/공공 날씨 API 호출
  ├─ Official Source Fetcher
  │   └─ 허용 도메인만 보완 조회
  ├─ Answer Composer
  │   └─ LLM + 캐시 + 템플릿 혼합 답변
  └─ Cache Layer
      └─ 정적/메모리/파일 기반 캐시 후보

[Static Data]
  ├─ API metadata index JSON
  ├─ API semantic/search index JSON
  ├─ allowed domains config
  └─ last successful refresh metadata

[GitHub Actions]
  ├─ weekly cron
  ├─ workflow_dispatch manual refresh
  ├─ API metadata fetch/validate
  ├─ build next data snapshot
  └─ success only replace current snapshot
```

---

## 4. 프로젝트 구조 제안

실제 생성/구현은 사용자가 명시적으로 실행 지시한 이후 OpenCode를 활용한다.
Milestone 0의 실제 구조와 목표 구조의 차이는 `docs/PROJECT_BASELINE.md`에서 추적한다. 앱별 런타임, 패키지 매니저, 환경변수 예시는 `frontend/`와 `backend/`가 각각 소유하며 루트 공유 앱 tooling 없이 유지한다.

```text
~/projects/gameunjang-agi/
  docs/
    PRD.md
    TRD.md
    IMPLEMENTATION_SPEC.md
  frontend/
    src/
      components/
      pages/
      styles/
      lib/
    public/
    package.json
  backend/
    app/
      main.py
      config.py
      guard/
      routing/
      clients/
      answer/
      cache/
    tests/
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
```

Vercel 단일 프로젝트로 배포하되, 디렉토리는 `frontend/`와 `backend/`로 분리한다. 벤더 종속 최소화를 위해 `frontend/`, `backend/`, `data/`, `scripts/`를 분리한다.

---

## 5. 데이터 설계

## 5.1 API 메타데이터 스키마

파일 예: `data/current/tour_api_metadata.json`

```json
{
  "version": "2026-06-15T00:00:00Z",
  "source": "data.go.kr",
  "provider": "한국관광공사",
  "apis": [
    {
      "id": "tour-api-example",
      "name": "API 이름",
      "description": "API 설명",
      "domain": "data.go.kr",
      "endpoint": "https://...",
      "method": "GET",
      "requiredParams": ["serviceKey"],
      "optionalParams": ["areaCode", "sigunguCode", "keyword"],
      "responseFields": ["title", "addr1", "mapx", "mapy"],
      "categories": ["관광지", "지역검색"],
      "examples": [
        {
          "question": "부산 실내 관광지 추천",
          "params": {
            "areaCode": "6"
          }
        }
      ],
      "lastCheckedAt": "2026-06-15T00:00:00Z"
    }
  ]
}
```

## 5.2 검색 인덱스 스키마

파일 예: `data/current/tour_api_index.json`

```json
{
  "version": "2026-06-15T00:00:00Z",
  "items": [
    {
      "apiId": "tour-api-example",
      "searchText": "관광지 지역검색 부산 실내 아이 가족 여행 추천",
      "keywords": ["관광지", "지역", "부산", "실내", "가족"],
      "categories": ["관광지", "지역검색"],
      "weight": 1.0
    }
  ]
}
```

초기에는 임베딩 벡터 대신 텍스트 검색/키워드/간단한 의미 확장 사전을 사용한다. 필요 시 향후 `embedding` 필드를 추가한다.

---

## 6. 질문 처리 파이프라인

## 6.1 전체 플로우

```text
사용자 질문
  ↓
1. 입력 정규화
  ↓
2. 국내 관광 관련성 판별
  ├─ 아니오 → 거절 응답
  └─ 예 → 계속
  ↓
3. 질문 의도 추출
  ↓
4. API 메타데이터 의미검색
  ↓
5. 관련 API 후보 선택
  ↓
6. API 파라미터 생성
  ↓
7. 한국관광공사 API 호출
  ↓
8. 날씨 API 호출 필요 여부 판단 및 호출
  ↓
9. 허용 출처 보완 조회 필요 여부 판단
  ↓
10. 답변 생성
  ↓
11. 출처 도메인 정리
  ↓
12. 응답 반환 및 브라우저 로컬 저장
```

## 6.2 국내 관광 Guard

우선순위:

1. 규칙 기반 판별
2. 키워드/지역명/관광 카테고리 기반 판별
3. 애매한 경우에만 LLM 판별

관광 관련 키워드 예:

- 여행
- 관광
- 관광지
- 숙소
- 호텔
- 펜션
- 맛집
- 음식점
- 축제
- 행사
- 코스
- 일정
- 아이와
- 가족여행
- 실내
- 비 오는 날
- 지역명

거절 조건 예:

- 해외 지역 중심 질문
- 국내 관광 의도가 없는 일반 지식 질문
- 코딩/투자/정치/연예 등 관광 무관 질문

---

## 7. LLM 사용 전략

사용자 결정: **모든 관광 관련 질문에 소형 LLM 호출 + 강한 캐싱으로 비용 절감**

## 7.1 LLM 호출 위치

LLM은 다음 단계에서 사용할 수 있다.

1. 질문 의도 구조화
2. API 후보 선택 보조
3. API 파라미터 생성 보조
4. API 결과 기반 답변 생성
5. 일정 생성

단, 비용 절감을 위해 다음을 적용한다.

- 동일 질문 캐시
- 유사 질문 캐시
- API 결과 캐시
- 시스템 프롬프트 최소화
- 답변에 필요한 컨텍스트만 주입
- 소형 모델 우선
- 모델 교체 가능한 어댑터 구조

## 7.2 LLM Provider Adapter

코드는 특정 SDK에 직접 결합하지 않고 아래 추상 인터페이스를 기준으로 설계한다.

```text
LLMClient
  ├─ classifyTourismQuestion(input) -> GuardResult
  ├─ planApiCalls(input, apiIndex) -> ApiCallPlan
  ├─ composeAnswer(input, apiResults, sources) -> Answer
  └─ summarizeItinerary(input, apiResults, weather) -> Answer
```

가능한 구현체:

- Upstage 구현체
- OpenRouter 구현체
- 향후 OpenAI API 구현체
- 로컬/기타 모델 구현체
- 테스트용 Fake 구현체

## 7.3 중요 리스크

Upstage API를 기본 provider로 사용하고 OpenRouter API를 대체 provider로 지원하더라도, 모든 관광 관련 질문에 LLM을 호출하면 비용 목표를 초과할 수 있다. 또한 공급자별 응답 형식, rate limit, 장애 대응 정책이 다를 수 있다.

- 공급자별 요청 단가와 무료/유료 한도
- rate limit 및 동시성 제한
- 모델별 한국어 품질
- API 장애 시 fallback 순서
- Vercel 서버리스 함수 제한 내에서의 실행 가능성

따라서 TRD는 특정 방식에 고정하지 않고 LLM 어댑터 구조를 필수로 둔다.

---

## 8. 한국관광공사 API Client 설계

## 8.1 환경변수

초기 키 관리:

```text
TOUR_API_SERVICE_KEY=...
```

향후 API별 키가 필요하면 다음 구조로 확장 가능하다.

```text
TOUR_API_SERVICE_KEY=...
TOUR_API_SERVICE_KEY_<API_ID>=...
```

## 8.2 API 호출 원칙

- 질문에 필요한 API만 호출
- 호출 실패 시 해당 API 실패를 기록하고 가능한 경우 부분 답변
- API 응답 원본 전체를 LLM에 넣지 않고 필요한 필드만 정규화
- API별 응답 필드 차이를 normalized item으로 변환

## 8.3 정규화 데이터 모델

```json
{
  "type": "attraction | festival | accommodation | restaurant | course | etc",
  "title": "이름",
  "summary": "요약",
  "address": "주소",
  "region": "지역",
  "lat": 0,
  "lng": 0,
  "openingHours": "운영시간 또는 null",
  "price": "비용 또는 null",
  "officialUrl": "공식 링크 또는 null",
  "mapUrl": "지도 링크 또는 null",
  "sourceDomain": "visitkorea.or.kr",
  "rawApiId": "원본 API ID"
}
```

---

## 9. 날씨 API 설계

MVP에서 날씨 API 연동을 포함한다.

## 9.1 후보 기준

- 기상청 API 기준
- 무료 또는 공공 API 사용 범위 우선
- 국내 지역 날씨 지원
- 안정적
- 지역 좌표/격자 변환 지원 가능

## 9.2 사용 방식

- 사용자가 날짜/지역/날씨 조건을 명시한 경우 호출
- 일정 추천 시 여행 날짜가 있으면 호출
- 날짜가 없으면 현재/가까운 예보를 사용하거나 날씨 조건 기반으로만 판단

## 9.3 답변 반영

- 비/눈/폭염/한파 등은 실내 관광지 우선 추천
- 날씨 출처 도메인을 답변 하단에 포함

---

## 10. 공식/공공 출처 보완 조회

## 10.1 허용 도메인 정책

허용:

- `*.go.kr`
- `*.or.kr`
- 정부기관 도메인
- 지자체 도메인
- 공공기관 도메인
- 관광지 공식 홈페이지

기본 제외:

- 개인 블로그
- 커뮤니티
- 카페
- 광고성 페이지
- 일반 포털 검색 결과

## 10.2 보완 조회 사용 조건

- API 데이터에 운영시간/비용/공식 링크 등이 없고, API 응답에 공식 링크가 포함되어 있을 때
- 사용자가 명시적으로 최신 정보나 공식 정보를 요구했고, API 응답 공식 링크가 있을 때
- 일정 추천 품질에 필요한 핵심 정보가 API에 없고, API 응답 공식 링크에서 보완 가능한 때

## 10.3 안전장치

- 허용 도메인 목록 통과 후 조회
- API 응답에 포함된 공식 링크만 조회
- 임의 웹 검색은 MVP에서 제외
- 출처 도메인 표시
- 불확실하면 “확인된 정보 없음”으로 처리

---

## 11. 캐싱 전략

비용 절감을 위해 캐싱은 필수다.

## 11.1 캐시 대상

1. 사용자 질문 정규화 결과
2. 관광 관련성 판별 결과
3. API 라우팅 결과
4. 한국관광공사 API 응답
5. 날씨 API 응답
6. 최종 답변

## 11.2 캐시 저장소

MVP에서는 서버 메모리 캐시 또는 정적/파일 기반 캐시로 시작한다.

서버리스 환경에서는 메모리 캐시가 안정적이지 않을 수 있으므로 다음 우선순위를 둔다.

1. 빌드 시 생성된 정적 데이터
2. 브라우저 로컬 캐시
3. 서버 응답 캐시 헤더
4. 필요 시 무료 KV/DB 검토

## 11.3 캐시 키

- 정규화 질문 텍스트
- 지역
- 날짜
- 사용자 조건
- API 인덱스 버전
- 날씨 기준 시각

## 11.4 브라우저 세션 대화 제한

- 서버 계정/로그인이 없으므로 비용 통제는 브라우저 세션 단위로 수행한다.
- 한 브라우저 세션에서 최대 10회 질문할 수 있다.
- 제한 카운트는 sessionStorage 기준으로 관리한다.
- 10회 초과 시 클라이언트에서 추가 전송을 막고 새 세션 시작 또는 대화 초기화를 안내한다.
- 서버는 클라이언트 전달 카운트를 신뢰하지 않고, 가능하면 요청 메타데이터 기반의 가벼운 방어 로직을 둔다.

---

## 12. 배치 갱신 설계

## 12.1 자동 갱신

- GitHub Actions cron
- 주 1회 실행

## 12.2 수동 갱신

- GitHub Actions `workflow_dispatch`
- 관리자: 사용자 본인 1명
- 웹앱 내 관리자 버튼 없음

## 12.3 원자적 갱신

사용자 결정: **갱신 작업 전체가 성공했을 때만 새 API 메타정보로 교체**

절차:

1. 현재 데이터는 `data/current/`에 유지
2. 갱신 결과는 `data/staging/`에 생성
3. 모든 API 메타데이터 수집 성공
4. 스키마 검증 성공
5. 인덱스 생성 성공
6. smoke test 성공
7. `data/staging/`을 `data/current/`로 교체
8. 실패 시 `data/current/` 유지

## 12.4 실패 알림

- MVP에서는 실패 알림 없음
- GitHub Actions 실행 로그에서 확인

---

## 13. 배포 전략

## 13.1 확정 호스팅: Vercel

MVP 호스팅 플랫폼은 **Vercel**로 결정한다.

Vercel 사용 범위:

- React 프론트엔드 정적 배포
- Python 기반 API 라우트 또는 서버리스 함수
- 환경변수 관리
- GitHub 연동 배포

Vercel에 배포하되, 핵심 로직은 배포 플랫폼과 분리한다.

## 13.2 벤더 종속 완화 전략

프로젝트는 다음 조건을 만족해야 한다.

- 프론트엔드는 정적 빌드 가능
- 백엔드는 Python ASGI 또는 서버리스 함수로 실행 가능
- 데이터는 정적 JSON으로 제공 가능
- 호스팅 이전 시 핵심 코드 변경 최소화
- Vercel 전용 엔트리포인트는 얇은 어댑터로 유지
- 관광 API 라우팅, LLM 어댑터, 데이터 정규화, 캐싱 로직은 순수 Python 모듈로 분리

## 13.3 Vercel 선택 이유

- React 정적/SSR 배포가 편리하다.
- Python serverless functions 사용이 가능하다.
- 무료 티어가 있다.
- GitHub 연동과 환경변수 관리가 쉽다.
- 현재 요구사항에서는 Cloudflare Workers 전용 구조보다 벤더 전용 코드가 적다.

## 13.4 Vercel 배포 시 주의사항

- 서버리스 함수 실행시간 제한 확인
- Python 런타임 cold start 확인
- OpenRouter/Upstage API 호출 timeout 관리
- 정적 JSON 파일 크기와 배포 번들 크기 관리
- API 키는 Vercel 환경변수로만 관리

## 13.5 대체 가능성

Vercel로 결정했지만, 향후 이전 가능성을 위해 다음을 유지한다.

- `frontend`는 정적 빌드 가능
- `backend`는 FastAPI 앱으로 로컬/서버리스/Docker 실행 가능
- 배포 어댑터는 별도 파일로 격리

---

## 14. 보안 요구사항

## 14.1 API 키

- `TOUR_API_SERVICE_KEY`는 서버 환경변수로만 관리
- 클라이언트 번들은 공개 설정만 포함
- 서버 또는 배치에서만 사용

## 14.2 LLM API 키

- OpenRouter API 키와 Upstage API 키는 Vercel 환경변수로 관리한다.
- 로컬 개발에서는 `.env`를 사용하되 `.env.example`에는 키 이름만 제공한다.
- 클라이언트에는 공개 설정만 노출한다.
- 서버리스 로그에 API 키 또는 응답 원문 민감정보가 남지 않도록 한다.

## 14.3 입력 검증

- 사용자 입력 길이 제한
- 악성 프롬프트/프롬프트 인젝션 방지
- 조회 대상은 허용 도메인으로 제한
- 비관광 질문 조기 거절

---

## 15. API 응답 형식

## 15.1 `/api/chat` 요청

```json
{
  "message": "이번 주말 아이랑 부산에서 갈 만한 실내 관광지 추천해줘",
  "localConversationId": "browser-local-id",
  "clientContext": {
    "timezone": "Asia/Seoul"
  }
}
```

## 15.2 `/api/chat` 응답

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
      "openingHours": "운영시간",
      "price": "비용",
      "officialUrl": "https://...",
      "mapUrl": "https://..."
    }
  ],
  "sourceDomains": ["visitkorea.or.kr", "data.go.kr"],
  "warnings": []
}
```

## 15.3 비관광 질문 응답

```json
{
  "type": "rejection",
  "isTourismRelated": false,
  "answer": "이 서비스는 국내 관광 관련 질문에만 답변할 수 있습니다. 여행지, 관광지, 축제, 숙소, 음식점, 여행코스와 관련된 질문을 입력해 주세요.",
  "sourceDomains": [],
  "warnings": []
}
```

---

## 16. 테스트 요구사항

## 16.1 단위 테스트

- 국내 관광 관련성 판별
- 비관광 질문 거절
- API 메타데이터 검색
- API 후보 선택
- API 파라미터 생성
- 출처 도메인 필터링
- 답변 출처 도메인 표시
- 데이터 스냅샷 검증

## 16.2 통합 테스트

- 질문 → API 선택 → API 호출 mock → 답변 생성
- 갱신 성공 시 staging → current 교체
- 갱신 실패 시 current 유지
- 날씨 조건 질문 처리
- 일정 추천 처리

## 16.3 비용 테스트

- LLM 호출 횟수 측정
- 캐시 hit rate 측정
- 일 1,000쿼리 기준 예상 비용 산출

## 16.4 E2E 테스트

- 모바일 화면에서 질문 입력
- 답변 렌더링
- 로컬 대화 기록 유지
- 대화 기록 삭제
- 비관광 질문 거절

---

## 17. 비용 모델

## 17.1 비용 절감 원칙

1. DB 없이 정적 JSON 우선
2. GitHub Actions 무료 cron 사용
3. 정적 호스팅 무료 티어 사용
4. LLM 호출 캐싱
5. 소형 모델 사용
6. API 결과를 요약해 컨텍스트 최소화
7. 외부 조회는 필요한 경우로 제한

## 17.2 비용 리스크

모든 관광 질문에 소형 LLM을 호출하는 전략은 일 1,000쿼리에서 모델 비용이 발생할 수 있다. Upstage/OpenRouter API의 모델 단가와 토큰 사용량에 따라 월 1달러 미만 조건을 초과할 수 있다.

대응:

- 최종 답변 캐시
- 인기 지역/질문 사전 생성
- 일정 추천 같은 복잡 질문만 더 긴 답변 허용
- 응답 토큰 제한
- 브라우저 세션당 10회 대화 제한

---

## 18. 개발 실행 원칙

사용자 지침에 따라 개발 실행 시 다음을 따른다.

1. 모든 개발 관련 태스크 실행은 OpenCode를 활용한다.
2. 개발 코딩은 OpenCode가 담당한다.
3. 모든 개발 프로젝트는 `~/projects/` 아래 프로젝트별로 관리한다.
4. 이 프로젝트의 디렉토리는 `~/projects/gameunjang-agi`다.
5. 구현, 설치, 배포, 커밋은 사용자의 명시적 실행 지시 이후 진행한다.

---

## 19. 향후 확장

- 고급 지도 UI
- 위치 기반 추천
- 사용자 취향 저장
- 다국어 지원
- 여행 일정 공유
- 즐겨찾기
- 지역별 추천 카드 UI
- 관리자 웹 대시보드
- 임베딩 기반 고급 의미검색
- 관광 데이터 품질 점수화

---

## 20. 다음 기술 검토 항목

1. Upstage/OpenRouter 모델 후보와 예상 단가 확인
2. 한국관광공사 API 목록과 실제 인증 방식 확인
3. 무료 날씨 API 후보 선정
4. Vercel Python Functions 적합성 확인
5. 정적 JSON 크기와 클라이언트/서버 로딩 전략 확인
6. 일 1,000쿼리 기준 캐싱/LLM 비용 시뮬레이션
7. API 메타데이터 갱신 스크립트 구현 계획 수립
