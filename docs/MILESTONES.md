# Gameunjang-agi Milestones

문서 상태: Living document
근거 문서: `docs/PRD.md`, `docs/TRD.md`, `docs/IMPLEMENTATION_SPEC.md`

이 문서는 구현 전후로 계속 갱신하는 가벼운 진행 체크리스트다. 세부 설계의 원천은 PRD/TRD/Implementation Spec을 우선한다.

---

## 0. 프로젝트 기준선 정리

- [x] `frontend/`와 `backend/`를 독립적으로 분리 가능한 경계로 유지한다.
- [x] 스택별 런타임/패키지 매니저 기준은 각 앱 디렉터리 안에 둔다.
- [x] `.env.example`에는 환경변수 이름과 예시 플레이스홀더만 둔다.
- [x] 구현 전 문서와 실제 디렉터리 구조의 차이를 확인한다.
- [x] 문서 검증: PRD/TRD/Implementation Spec과 이 체크리스트의 용어·범위·우선순위가 맞다.
- [x] 문서 검증: `docs/` 변경 diff가 간결하고 추적 가능하다.

## 1. 앱 골격 및 로컬 개발 기준

- [x] `frontend/`에 Node 24.x 기준 Vite + React + TypeScript 앱을 만든다.
- [x] `backend/`에 Python 3.14 기준 FastAPI 호환 구조를 만든다.
- [x] Vercel 전용 엔트리포인트는 얇은 배포 어댑터로 분리한다.
- [x] 프론트엔드/백엔드 각각의 검증 명령을 해당 디렉터리 안에 둔다.
- [x] 스캐폴딩 검증: 각 앱 디렉터리에서 install·lint/typecheck 또는 backend ruff/pytest 기본 명령이 실행된다.
- [x] 스캐폴딩 검증: 앱별 런타임 의존성은 각 앱 디렉터리에 있다.

## 2. 프론트엔드 MVP

- [x] 모바일 우선 챗 화면을 구현한다.
- [x] PC 반응형 레이아웃을 확인한다.
- [x] 브라우저 로컬 대화 기록 저장/삭제를 구현한다.
- [x] 브라우저 세션당 질문 10회 제한과 안내 메시지를 구현한다.
- [x] `/api/chat` 호출 클라이언트와 오류 표시를 구현한다.
- [x] 답변, 추천 항목, 경고, 출처 도메인을 렌더링한다.
- [x] 프론트엔드 검증: lint/typecheck/test/build 스크립트가 통과한다.
- [x] 프론트엔드 검증: 모바일·PC 화면, 세션 제한, 오류 표시를 수동 smoke로 확인한다. 대화 초기화는 localStorage 대화 기록만 지우며 같은 브라우저 세션의 10회 질문 카운터는 유지한다.

## 3. 백엔드 요청/응답 기반

- [x] `/api/chat` 요청/응답 스키마를 구현한다.
- [x] 입력 길이 제한과 기본 검증을 적용한다.
- [x] 국내 관광 관련성 guard를 우선 규칙/키워드 기반으로 구현한다.
- [x] 비관광 질문은 LLM/API 호출을 건너뛰고 정중한 범위 안내로 처리한다.
- [x] 응답에 `answer`, `items`, `sourceDomains`, `warnings`를 일관되게 포함한다.
- [x] 백엔드 검증: `ruff check .`, `ruff format --check .`, `pytest`가 통과한다.
- [x] 백엔드 검증: 관광 질문, 비관광 안내, 입력 길이, 응답 스키마 테스트를 포함한다.

## 4. 데이터 및 API 라우팅

- [x] 한국관광공사 API 메타데이터 JSON 스키마를 확정한다.
- [x] MVP 우선 API 유형을 기준으로 샘플 메타데이터를 준비한다.
- [x] 정적 JSON + 키워드/간단 의미검색 기반 API 후보 선택을 구현한다.
- [x] 지역명, 관광 카테고리, 동의어 기반 라우팅을 추가한다.
- [x] 낮은 관련도 또는 정보 부족 상황의 응답 정책을 구현한다.
- [x] 데이터 검증: 메타데이터 JSON schema 검사를 통과한다.
- [x] 데이터 검증: 지역·카테고리·동의어 샘플 질의가 기대 API 후보로 라우팅된다.

## 5. 외부 Provider 연동

- [x] LLM provider adapter 인터페이스를 만든다.
- [x] Upstage 기본 provider를 구현한다.
- [x] OpenRouter fallback provider를 구현한다.
- [x] 한국관광공사 API client와 응답 정규화를 구현한다.
- [x] 기상청 API client와 실패 시 graceful degradation을 구현한다.
- [x] API 응답에 포함된 공식 링크만 보완 조회하도록 제한한다.
- [ ] `/api/chat` 관광 답변 경로에서 한국관광공사 API를 실제 호출한다. 로컬/테스트 배선은 있으나 실제 배포 런타임 검증 전까지 완료로 보지 않는다.
- [ ] `/api/chat`이 한국관광공사 실응답 항목을 정규화해 답변 생성 입력으로 전달한다. mock/regression 검증은 통과하나 live runtime 검증은 남아 있다.
- [ ] `/api/chat` 관광 답변 경로에서 설계대로 LLM/provider를 호출한다. provider mock/regression 검증은 있으나 실제 배포 런타임 검증 전까지 완료로 보지 않는다.
- [x] `/api/chat` 관광 답변 경로의 TourAPI+LLM mock/regression 배선 테스트를 갖춘다.
- [ ] `/api/chat` 날씨 조건 질문에서 기상청 API를 실제 호출하고 실패 시 graceful degradation을 적용한다. Vercel에는 `TOUR_API_SERVICE_KEY`와 `UPSTAGE_*`가 있으나 `KMA_API_KEY`가 없어 live runtime 통합/검증은 차단됨.
- [x] 연동 검증: provider mock 테스트로 성공·fallback·timeout 흐름을 확인한다.
- [x] 연동 검증: 관광공사·기상청 응답 fixture가 정규화 스키마와 맞다.

## 6. 답변 생성과 출처 정책

- [x] API 데이터 우선 답변 생성을 구현한다.
- [x] 확인 가능한 값은 출처와 함께 표시하고 그 외 항목은 “확인된 정보 기준 제공”으로 표시한다.
- [x] 일정 추천 형식을 구현한다.
- [x] 날씨 조건을 추천 순서와 경고에 반영한다.
- [x] 출처 도메인을 답변 하단 또는 응답 필드에 표시한다.
- [x] 공식 출처 도메인과 API 제공 링크 중심의 답변 근거를 구현한다.
- [x] `/api/chat`이 정규화된 실제 관광 항목을 `compose_answer`에 넘겨 답변을 만든다.
- [x] `강릉 2박 3일 코스` 같은 대표 답변 가능 질문에서 API 데이터가 있으면 `confirmed_api_item_data_unavailable`을 반환하지 않는다.
- [ ] 날씨 조건 질문은 실제 날씨 데이터를 답변 순서, 경고, 출처에 반영한다.
- [x] 답변 검증: 출처 도메인, 경고, 추천 항목, 일정 형식 스냅샷 테스트를 통과한다.
- [x] 답변 검증: 날씨·일정·정보 부족 케이스가 안내 문구와 맞다.

## 7. 데이터 갱신 자동화

- [x] GitHub Actions 주 1회 cron 갱신을 추가한다.
- [x] `workflow_dispatch` 수동 갱신을 추가한다.
- [x] `data/staging/` 생성 후 검증 성공 시에만 `data/current/`를 교체한다.
- [x] 갱신 실패 시 기존 정상 데이터를 유지한다.
- [x] 데이터 스냅샷 검증과 smoke test를 자동화한다.
- [x] 데이터 갱신 검증: staging schema·row count·핵심 샘플 smoke가 통과한다.
- [x] 데이터 갱신 검증: 성공 run은 current 교체 로그와 산출물을 남긴다.

## 8. 통합, 비용, 배포 준비

- [x] 프론트엔드 lint/typecheck/test/build 스크립트를 실행 가능하게 한다.
- [x] 백엔드 `ruff check .`, `ruff format --check .`, `pytest`를 실행 가능하게 한다.
- [x] 관광 질문, 비관광 범위 안내, 세션 제한, 출처 정책 테스트를 추가한다.
- [x] LLM 호출 횟수, 캐시 hit rate, 일 1,000쿼리 기준 비용을 점검한다.
- [x] Vercel 무료 티어와 Python Function 제한을 확인한다.
- [x] 배포 환경변수를 문서화하고 실제 비밀값은 로컬/배포 환경에서만 관리한다.
- [x] 통합 검증: 프론트엔드에서 `/api/chat`까지 happy path와 오류 path가 통과한다.
- [ ] 통합 검증: `/api/chat` 대표 관광 질문이 한국관광공사 API 호출, 실항목 정규화, `compose_answer`, LLM/provider 호출까지 통과한다.
- [ ] 통합 검증: 날씨 조건 질문이 기상청 API 호출과 날씨 반영 답변까지 통과한다.
- [x] 회귀 검증: 현재 gap처럼 `강릉 2박 3일 코스`가 답변 가능 데이터가 있는데도 `confirmed_api_item_data_unavailable`로 끝나면 실패한다.
- [x] 배포 검증: preview 배포 smoke, 환경변수 체크, function 로그 확인을 완료한다.

## 9. MVP 완료 기준

- [ ] 모바일에서 국내 관광 질문을 입력하면 `/api/chat`이 실제 관광공사 데이터와 LLM/provider 경로를 거쳐 답변한다.
- [ ] 질문에 맞는 한국관광공사 API 후보를 선택하고 실제 호출해 정규화된 항목을 답변에 사용한다.
- [x] 비관광 질문에 정중한 범위 안내를 제공한다.
- [ ] 일정/날씨 조건 질문에 대해 관광공사·기상청 실데이터를 사용해 제한된 범위에서 답변한다.
- [ ] 답변에 실제 사용한 공식 출처 도메인이 표시된다.
- [x] 주 1회/수동 데이터 갱신이 성공 시에만 반영된다.
- [x] 월 1달러 미만 목표를 지키는 비용 통제 장치가 있다.
- [ ] 완료 검증: 문서·스캐폴딩·백엔드·프론트엔드·런타임 통합·데이터 갱신·배포 게이트가 모두 녹색이다.

---

## 이후 후보

- [ ] 임베딩 기반 고급 의미검색 검토
- [ ] 지도 UI와 위치 기반 추천 검토
- [ ] 사용자 취향/즐겨찾기/공유 기능 검토
- [ ] 관리자 대시보드와 실패 알림 검토
- [ ] 다국어 지원 검토
