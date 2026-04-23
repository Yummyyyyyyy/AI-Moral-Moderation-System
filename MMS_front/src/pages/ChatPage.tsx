import { useEffect, useRef, useState } from "react";
import { useParams } from "react-router-dom";
import { api } from "../api/client";
import type { Turn } from "../api/types";

export default function ChatPage() {
  const { sessionId } = useParams();
  const [turns, setTurns] = useState<Turn[]>([]);
  const [text, setText] = useState("");
  const [sending, setSending] = useState(false);
  const [safety, setSafety] = useState(false);
  const bottom = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!sessionId) return;
    api.sessionMessages(sessionId).then(setTurns);
  }, [sessionId]);

  useEffect(() => {
    bottom.current?.scrollIntoView({ behavior: "smooth" });
  }, [turns]);

  async function send() {
    if (!sessionId || !text.trim()) return;
    setSending(true);
    try {
      const r = await api.sessionSend(sessionId, text);
      setTurns((prev) => [...prev, r.user_turn, r.bot_turn]);
      setText("");
      setSafety(r.safety_trip);
    } finally {
      setSending(false);
    }
  }

  return (
    <div>
      <div className="chat-header">
        <div>
          <div className="title">Counseling session</div>
          <div className="sub">session id: {sessionId}</div>
        </div>
        <span className="muted" style={{ fontSize: 12 }}>
          multi-turn · each user message is re-checked by C1 / C2
        </span>
      </div>
      {safety ? (
        <div className="crisis-banner">
          ⚠ Crisis signals detected. The bot has attached local crisis-line information.
        </div>
      ) : null}
      <div className="chat-stream">
        {turns.length === 0 ? (
          <div className="muted" style={{ textAlign: "center", padding: 40 }}>
            No messages yet. Write something to start the session.
          </div>
        ) : null}
        {turns.map((t) => (
          <div key={t.id} className={`msg-row ${t.role}`}>
            <div className="msg-bubble">{t.text}</div>
          </div>
        ))}
        <div ref={bottom} />
      </div>
      <div className="composer-inline">
        <textarea
          rows={2}
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Write a reply… (⌘/Ctrl+Enter to send)"
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) send();
          }}
        />
        <button className="btn primary" disabled={sending} onClick={send}>
          {sending ? "Sending…" : "Send"}
        </button>
      </div>
    </div>
  );
}
