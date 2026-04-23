import { useState } from "react";
import { api } from "../api/client";
import Avatar from "../components/Avatar";

const PRESETS: Array<{ label: string; text: string }> = [
  { label: "neutral", text: "Had a great coffee this morning, the barista was so kind!" },
  { label: "hate", text: "Everyone in that group is an idiot, they should just shut up forever." },
  { label: "bullying", text: "Nobody likes you, you should quit this game already, you loser." },
  { label: "misinfo", text: "Vaccine microchip controls your mind, do not take it." },
  { label: "depressive", text: "I'm so tired of everything, nobody cares whether I'm alive. I feel hopeless." },
  { label: "self-harm", text: "I just want to end it tonight. I can't go on." },
];

export default function IngestPage() {
  const [text, setText] = useState("I'm feeling so hopeless and nobody cares.");
  const [userId, setUserId] = useState("u-demo");
  const [sending, setSending] = useState(false);
  const [log, setLog] = useState<string[]>([]);

  async function push() {
    if (!text.trim()) return;
    setSending(true);
    try {
      const id = `p-${Date.now()}`;
      const r = await api.ingest({
        id,
        author: { user_id: userId, display_name: userId },
        text,
      });
      const harm = r.is_harmful ? `harmful/${r.harm_type ?? "?"}` : "neutral";
      const extras = [
        r.reply ? "reply drafted" : null,
        r.session ? "session opened" : null,
      ]
        .filter(Boolean)
        .join(" · ");
      setLog((prev) => [
        `${new Date().toLocaleTimeString()}  ${id}  →  ${harm}${extras ? "  ·  " + extras : ""}`,
        ...prev,
      ]);
      setText("");
    } finally {
      setSending(false);
    }
  }

  return (
    <>
      <div className="composer">
        <Avatar name={userId} />
        <div style={{ minWidth: 0 }}>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="What's happening?"
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) push();
            }}
          />
          <div className="presets">
            {PRESETS.map((p) => (
              <button
                key={p.label}
                className="btn small ghost"
                onClick={() => setText(p.text)}
                type="button"
              >
                {p.label}
              </button>
            ))}
          </div>
          <div className="controls">
            <input
              className="handle-input"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              placeholder="user id"
            />
            <button className="btn primary" onClick={push} disabled={sending}>
              {sending ? "Pushing…" : "Post"}
            </button>
          </div>
        </div>
      </div>
      <div className="log">
        {log.length === 0 ? (
          <div className="muted" style={{ padding: "8px 0" }}>
            Pipeline events will appear here after posting.
          </div>
        ) : (
          log.map((l, i) => <div key={i}>{l}</div>)
        )}
      </div>
    </>
  );
}
