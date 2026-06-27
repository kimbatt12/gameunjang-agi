# Cost Control Checks

문서 상태: Milestone 8 검증 기준

## 목표

- MVP 비용 목표는 월 1달러 미만이다.
- 일 1,000 쿼리를 상한 기준으로 점검한다.
- 비관광 질문은 LLM scope classification 후 Tourism/KMA API 호출 없이 범위 안내로 종료한다.
- 비용 통제는 브라우저 세션당 10회 질문 제한, 작은 classifier prompt/낮은 `max_tokens`, adapter 추상화, provider/fallback 설정, 캐시와 템플릿 답변을 함께 사용해 달성한다.

## 테스트 가능한 기준

`backend/app/cost_control.py`는 아래 입력을 기준으로 비용 게이트를 계산한다.

- `total_queries`: 일간 전체 요청 수
- `cache_hits`: 캐시 또는 템플릿으로 처리된 요청 수
- `llm_call_count`: scope classification과 답변 생성을 포함한 실제 LLM 호출 수
- `estimated_cost_per_llm_call_usd`: provider별 예상 단가

기본 게이트는 다음과 같다.

- `total_queries <= 1000`
- `cache_hit_rate >= 0.95`
- `llm_call_count <= total_queries - cache_hits`
- `llm_call_count * estimated_cost_per_llm_call_usd < 1 / 30`

대표 검증 시나리오: 일 1,000쿼리, 캐시 hit 960건, LLM 40회, 호출당 0.0005달러이면 일 예상 비용 0.02달러로 월 1달러 미만 목표의 일할 예산 안에 있다.

검증 명령은 `backend/`에서 `pytest tests/test_cost_control.py`를 실행한다.
