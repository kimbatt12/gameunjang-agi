# Frontend Architecture

문서 상태: Living document
기획 기준: 제품 요구사항, 기술 요구사항, 구현 명세의 최신 합의

## Purpose

`frontend/`는 Gameunjang-agi의 모바일 우선 웹 챗 UI를 담당한다. 사용자는 이 UI에서 국내 관광 질문을 입력하고, 추천 답변·일정·출처 도메인·제한 안내를 확인한다.

## Boundaries

- 서버 API 키, LLM 호출, 한국관광공사 API 호출, 기상청 API 호출은 백엔드가 소유한다.
- 대화 기록은 브라우저 로컬 저장소에서만 관리한다.
- 브라우저 세션당 10회 질문 제한을 1차로 적용한다.
- 백엔드와는 HTTP API 계약(`/api/chat`)으로만 통신한다.
- `frontend/`는 별도 저장소로 분리 가능해야 하며, 자체 패키지/툴링 기준을 소유한다.

## Stack

- 런타임 기준: Node `24.x` when `package.json` exists.
- 패키지 매니저 기준: `frontend/RUNTIME.md`가 소유하며, lockfile과 스크립트는 `frontend/` 안에만 둔다.
- 앱 스택: Vite + React + TypeScript를 기본 계획으로 둔다.
- 배포: 정적 빌드 결과를 Vercel 등 정적 호스팅에서 제공 가능하게 유지한다.

## Planned Structure

구현 시점의 실제 구조가 우선이며, 아래는 초기 계획이다.

```text
frontend/
  src/
    components/        # ChatInput, ChatMessage, SourceDomains 등
    lib/               # apiClient, sessionLimit, localConversation
    styles/            # 전역/반응형 스타일
    App.tsx
    main.tsx
  public/
  package.json
  vite.config.ts
  tsconfig.json
```

## Responsibilities

- 모바일 우선 챗 화면과 PC 반응형 UI
- 질문 입력, 전송 중 상태, 오류/경고 표시
- localStorage 또는 IndexedDB 기반 로컬 대화 기록
- sessionStorage 기반 브라우저 세션 질문 제한
- 답변 본문, 추천 항목, 일정, 출처 도메인 렌더링
- 비관광 범위 안내와 제한 도달 메시지 표시

## Validation Expectations

`frontend/package.json`이 생기면 해당 패키지 안의 스크립트를 사용한다.

- lint script가 있으면 실행한다.
- typecheck script가 있으면 실행한다.
- test script가 있으면 실행한다.
- build script가 있으면 실행한다.

프론트엔드 변경은 `frontend/` 안에서 검증하고, Node 워크플로 기준은 `frontend/`가 소유한다.

## Architecture Rules

- API 키와 provider 비밀값은 서버 환경에서만 관리한다.
- 백엔드 기능은 HTTP API 계약을 통해 사용한다.
- 빌드 계약은 `frontend/` 안의 도구와 설정으로 완결한다.
- Vercel은 배포 대상 중 하나일 뿐이며, UI 코드는 정적 호스팅으로 이전 가능해야 한다.
