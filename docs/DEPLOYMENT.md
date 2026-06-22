# Deployment Readiness

문서 상태: Milestone 8 배포 준비 체크리스트

## Vercel 무료 티어와 Python Function 제약 확인

- Vercel 무료 티어는 개인/비상업적 MVP 검증에 맞춰 사용한다. 팀/상업 운영 또는 사용량 증가 시 유료 플랜 전환 여부를 확인한다.
- Python Function은 서버리스 실행 시간, 메모리, 번들 크기, 콜드 스타트, 파일 시스템 쓰기 지속성 제한을 받는다는 전제로 설계한다.
- 장시간 배치, 대용량 데이터 갱신, 영구 파일 쓰기는 배포 함수가 아니라 GitHub Actions 데이터 갱신 흐름에서 처리한다.
- `backend/api/index.py`는 얇은 adapter로 유지하고 실제 로직은 `backend/app/`에 둔다.

## 배포 환경변수

실제 비밀값은 로컬 `.env` 또는 Vercel 환경변수 저장소에만 저장한다. 문서와 예시 파일에는 placeholder만 둔다.

### Backend server-only

```text
TOUR_API_SERVICE_KEY=replace-with-tour-api-service-key
LLM_PROVIDER=upstage
LLM_FALLBACK_PROVIDER=openrouter
UPSTAGE_API_KEY=replace-with-upstage-api-key
UPSTAGE_MODEL=replace-with-upstage-model-name
OPENROUTER_API_KEY=replace-with-openrouter-api-key
OPENROUTER_MODEL=replace-with-openrouter-model-name
KMA_API_KEY=replace-with-kma-api-key
APP_BASE_URL=https://example.invalid
MAX_BROWSER_SESSION_QUESTIONS=10
MAX_USER_MESSAGE_CHARS=1000
ANSWER_MAX_ITEMS=5
ANSWER_MAX_TOKENS=800
ALLOWED_SOURCE_DOMAINS=go.kr,or.kr,visitkorea.or.kr,data.go.kr
```

### Frontend public-only

```text
PUBLIC_APP_BASE_URL=https://example.invalid
```

## Preview deployment checklist

1. Frontend validation: `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build` from `frontend/`.
2. Backend validation: `ruff check .`, `ruff format --check .`, `pytest` from `backend/`.
3. Preview 환경변수 이름이 모두 존재하는지 확인한다. 값은 Vercel UI/CLI secret store에서만 확인하고 로그에 출력하지 않는다.
4. Preview URL에서 `/health`가 `{"status":"ok"}`를 반환하는지 확인한다.
5. Preview URL에서 `/api/chat` happy path로 국내 관광 질문이 200 응답과 `sourceDomains`를 반환하는지 확인한다.
6. Preview URL에서 `/api/chat` error path로 빈 message 또는 길이 초과 message가 422를 반환하는지 확인한다.
7. 비관광 질문이 LLM/API 호출 없이 국내 관광 범위 안내와 빈 `sourceDomains`를 반환하는지 확인한다.
8. 브라우저 세션 질문 10회 제한 안내가 표시되고 11번째 질문 전송이 차단되는지 확인한다.
9. Function 로그에서 secret 값이 출력되지 않고, 오류 path가 stack trace 없이 예상 상태 코드로 처리되는지 확인한다.
10. 비용 점검: 일 1,000쿼리 기준 LLM 호출 수, 캐시 hit rate, 예상 비용이 `docs/COST_CONTROL.md` 게이트를 통과하는지 확인한다.
