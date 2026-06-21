import './App.css';

export function App() {
  return (
    <main className="app-shell">
      <section className="hero" aria-labelledby="app-title">
        <p className="eyebrow">Gameunjang-agi</p>
        <h1 id="app-title">국내 관광 챗 UI 스캐폴드</h1>
        <p>
          Vite, React, TypeScript 기반 프론트엔드 골격입니다. 실제 대화,
          세션 제한, 출처 표시 기능은 후속 마일스톤에서 이 구조 위에
          구현합니다.
        </p>
      </section>
    </main>
  );
}
