# Backend Runtime Baseline

문서 상태: Milestone 0 baseline

`backend/`가 백엔드 Python 런타임과 패키지 매니저 기준을 소유한다. 루트는 백엔드용 공유 Python tooling 없이 유지한다.

## Runtime

- 앱 골격이 생성되고 `backend/pyproject.toml`이 생기면 Python `>=3.14,<3.15`를 기준으로 한다.
- 현재 Milestone 0 범위는 문서/구조 기준선이며, 앱 스캐폴딩과 의존성 설치는 이후 마일스톤에서 다룬다.

## Package Manager

- Python 패키지/lockfile/가상환경 기준은 `backend/` 안에서만 선택하고 유지한다.
- `ruff check .`, `ruff format --check .`, `pytest` 같은 검증은 `backend/pyproject.toml`이 생긴 뒤 `backend/`에서 실행한다.
- 백엔드 Python project file과 orchestration은 `backend/`가 소유한다.
