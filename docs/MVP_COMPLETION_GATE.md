# MVP Completion Gate

문서 상태: Milestone 9 완료 검증 기준

이 게이트는 실제 비밀값 또는 라이브 외부 호출 없이, 로컬 fixture·정적 메타데이터·mock 가능한 경로만으로 MVP 완료 기준을 확인한다.

## 완료 기준 매핑

- 모바일 국내 관광 질문: `frontend/index.html`의 모바일 viewport와 모바일 우선 챗 UI, `backend/tests/test_mvp_completion_gate.py`의 `/api/chat` 관광 질문 smoke로 확인한다.
- API 후보 선택: `backend/tests/test_api_routing.py`와 완료 게이트 테스트가 한국관광공사 API 후보를 질문 신호에 맞게 선택하는지 확인한다.
- 비관광 범위 안내: `/api/chat`이 LLM scope classifier의 `out_of_scope` 판별 후 Tourism/KMA API 호출 없이 종료하고 출처·외부 호출 근거와 public warning을 비워 둔다.
- 일정/날씨 제한 답변: 일정 형식, 질문 내 날씨 조건 반영, 확인된 데이터 없을 때 임의 추천 금지를 테스트한다.
- 출처 도메인 표시: 백엔드 응답의 `sourceDomains`와 프론트엔드의 출처 도메인 섹션을 검증한다.
- 주 1회/수동 데이터 갱신: `.github/workflows/data-refresh.yml`은 weekly cron과 `workflow_dispatch`만 제공하며, staging validation과 smoke가 성공한 후에만 promote한다.
- 월 1달러 미만 비용 통제: `backend/app/cost_control.py`의 일 1,000쿼리·캐시 hit rate·LLM 호출 수·일할 예산 게이트를 통과해야 한다.

## 최종 검증 명령

백엔드:

```sh
cd backend
ruff check .
ruff format --check .
pytest
```

프론트엔드:

```sh
cd frontend
npm run lint
npm run typecheck
npm test
npm run build
```

저장소 수준:

```sh
git diff --check
```
