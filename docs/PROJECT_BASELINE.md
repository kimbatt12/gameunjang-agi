# Project Baseline

문서 상태: Milestone 0 baseline
적용 범위: 구현 전 문서/구조 기준선

이 문서는 `docs/MILESTONES.md`의 `0. 프로젝트 기준선 정리` 완료 상태를 확인하기 위한 기준선이다. 앱 구현, 스캐폴딩, 의존성 설치, 배포 설정은 마일스톤 1 이후 범위다.

## Repository Scope

- 저장소 루트: `/home/hermes/projects/gameunjang-agi`
- 프로젝트 규칙 원천: `AGENTS.md`
- `frontend/`와 `backend/`는 별도 저장소로 분리 가능한 경계로 유지한다.
- 앱별 문서, 환경변수 예시, ignore 파일, 향후 런타임/패키지 매니저 기준은 각 앱 디렉터리 안에 둔다.
- 공유 Node/Python 런타임, 공유 패키지 매니저, 루트 앱 오케스트레이션 없이 루트를 스택 중립으로 유지한다.
- 실제 비밀값은 로컬 `.env` 또는 배포 secret store에서 관리하고, 예시는 placeholder 값만 사용한다.

## Actual Directory Structure

Milestone 0 기준 실제 구조는 다음과 같다.

```text
gameunjang-agi/
  .editorconfig
  .githooks/
  .github/
    workflows/
  .gitignore
  .opencode/
  AGENTS.md
  backend/
    .env.example
    .gitignore
    ARCHITECTURE.md
    RUNTIME.md
  docs/
    IMPLEMENTATION_SPEC.md
    MILESTONES.md
    PRD.md
    PROJECT_BASELINE.md
    TRD.md
  frontend/
    .env.example
    .gitignore
    ARCHITECTURE.md
    RUNTIME.md
  LICENSE
  opencode.json
```

## Planned vs Actual Differences

PRD/TRD/Implementation Spec에는 MVP 구현 이후의 목표 구조도 포함되어 있다. Milestone 0에서는 아래 차이가 정상이다.

| 영역 | 현재 상태 | 이후 마일스톤 |
|---|---|---|
| `frontend/src/`, `frontend/package.json` | 없음 | 마일스톤 1에서 앱 골격 생성 |
| `backend/app/`, `backend/pyproject.toml`, `backend/tests/` | 없음 | 마일스톤 1에서 백엔드 골격 생성 |
| `data/`, `scripts/`, 데이터 갱신 workflow | 없음 | 마일스톤 4 이후 데이터/갱신 구현 |
| Vercel adapter 또는 `vercel.json` | 없음 | 배포 준비 단계에서 필요 시 추가 |
| 루트 `.env.example` | 없음 | 앱별 `.env.example`을 원칙으로 유지 |

## Environment Examples

- `frontend/.env.example`: 브라우저에 노출 가능한 공개 설정 이름과 placeholder 예시만 둔다.
- `backend/.env.example`: 서버 전용 API 키 이름과 placeholder 예시만 둔다.
- 실제 API 키, 토큰, 서비스 키, 배포 비밀값은 로컬 `.env` 또는 배포 환경변수로만 관리한다.

## Runtime and Package Manager Baseline

- Frontend 기준은 `frontend/RUNTIME.md`가 소유한다.
- Backend 기준은 `backend/RUNTIME.md`가 소유한다.
- 루트는 공유 `package.json`, lockfile, Python project file, Makefile 같은 앱 런타임/패키지 매니저 계약 없이 유지한다.

## Milestone 0 Validation

문서/구조 기준선 변경 시 최소 검증은 다음과 같다.

```sh
git diff --check
for path in \
  AGENTS.md \
  docs/PRD.md \
  docs/TRD.md \
  docs/IMPLEMENTATION_SPEC.md \
  docs/MILESTONES.md \
  docs/PROJECT_BASELINE.md \
  frontend/.env.example \
  frontend/.gitignore \
  frontend/ARCHITECTURE.md \
  frontend/RUNTIME.md \
  backend/.env.example \
  backend/.gitignore \
  backend/ARCHITECTURE.md \
  backend/RUNTIME.md
do
  test -e "$path" || { printf 'Missing baseline path: %s\n' "$path"; exit 1; }
done

for env_path in frontend/.env.example backend/.env.example
do
  line_number=0
  while IFS= read -r line || test -n "$line"
  do
    line_number=$((line_number + 1))
    case "$line" in ''|'#'*) continue ;; esac
    case "$line" in *=*) : ;; *) printf '%s:%s is not KEY=value\n' "$env_path" "$line_number"; exit 1 ;; esac
    key=${line%%=*}
    value=${line#*=}
    case "$key" in ''|*[[:space:]]*) printf '%s:%s has invalid key\n' "$env_path" "$line_number"; exit 1 ;; esac
    test -n "$value" || { printf '%s:%s must use a placeholder value\n' "$env_path" "$line_number"; exit 1; }
  done < "$env_path"
done
```
