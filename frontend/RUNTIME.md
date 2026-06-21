# Frontend Runtime Baseline

문서 상태: Milestone 0 baseline

`frontend/`가 프론트엔드 런타임과 패키지 매니저 기준을 소유한다. 루트는 프론트엔드용 공유 Node tooling 없이 유지한다.

## Runtime

- 앱 골격이 생성되고 `frontend/package.json`이 생기면 Node `24.x`를 기준으로 한다.
- 현재 Milestone 0 범위는 문서/구조 기준선이며, 앱 스캐폴딩과 의존성 설치는 이후 마일스톤에서 다룬다.

## Package Manager

- 패키지 매니저와 lockfile은 `frontend/` 안에서만 선택하고 유지한다.
- `lint`, `typecheck`, `test`, `build` 같은 검증 스크립트는 `frontend/package.json`이 생긴 뒤 해당 파일에서 소유한다.
- 프론트엔드 `package.json`과 npm orchestration은 `frontend/`가 소유한다.
