export default function SidebarRail() {
  return (
    <aside className="rail">
      <div className="panel">
        <h4>Pipeline</h4>
        <div style={{ fontSize: 13, color: "var(--text-dim)", lineHeight: 1.7 }}>
          <div>① <b style={{ color: "var(--text)" }}>Classifier-1</b> — harmful?</div>
          <div>② <b style={{ color: "var(--text)" }}>Classifier-2</b> — harm type</div>
          <div>③ <b style={{ color: "var(--text)" }}>RAG</b> — retrieve corpus</div>
          <div>④ <b style={{ color: "var(--text)" }}>LLM</b> — persuasion draft</div>
          <div>⑤ <b style={{ color: "var(--text)" }}>Moderator</b> — human review</div>
        </div>
      </div>
      <div className="panel">
        <h4>Module owners</h4>
        <div className="row">
          <span>Binary classifier</span>
          <span className="who">member-A</span>
        </div>
        <div className="row">
          <span>Typed classifier</span>
          <span className="who">member-B</span>
        </div>
        <div className="row">
          <span>RAG retriever</span>
          <span className="who">member-C</span>
        </div>
        <div className="row">
          <span>RLHF LLM</span>
          <span className="who">member-D</span>
        </div>
        <div className="row">
          <span>Pipeline + UI</span>
          <span className="who">you</span>
        </div>
      </div>
      <div className="panel">
        <h4>Harm taxonomy</h4>
        <div className="chips">
          <span className="chip hate">hate</span>
          <span className="chip cyberbullying">cyberbullying</span>
          <span className="chip misinformation">misinfo</span>
          <span className="chip depressive">depressive</span>
          <span className="chip self_harm">self-harm</span>
        </div>
        <div style={{ fontSize: 12, color: "var(--text-dim)", marginTop: 10, lineHeight: 1.5 }}>
          <b style={{ color: "var(--depressive, #c9aeff)" }}>depressive</b> &amp;{" "}
          <b style={{ color: "#ff9a9a" }}>self-harm</b> open a multi-turn counseling session.
        </div>
      </div>
    </aside>
  );
}
