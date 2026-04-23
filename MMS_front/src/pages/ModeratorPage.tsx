import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { ModeratorAction, ReplyDraft } from "../api/types";
import Avatar from "../components/Avatar";

const MOD_ID = "alice";

const OUTCOME: Record<ModeratorAction, { tone: "ok" | "warn" | "danger" | "info"; text: string }> = {
  approve:  { tone: "ok",     text: "Approved — bot reply is now visible in the feed." },
  edit:     { tone: "info",   text: "Edited & published — your text replaces the draft." },
  polish:   { tone: "info",   text: "Polished by the RLHF model and published." },
  reject:   { tone: "danger", text: "Rejected — draft will not be shown to anyone." },
  escalate: { tone: "warn",   text: "Escalated — a counseling session was opened on this post." },
};

export default function ModeratorPage() {
  const [queue, setQueue] = useState<ReplyDraft[] | null>(null);
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [flash, setFlash] = useState<{ tone: string; text: string } | null>(null);

  async function load() {
    setQueue(await api.modQueue());
  }
  useEffect(() => {
    load();
  }, []);

  async function decide(r: ReplyDraft, action: ModeratorAction) {
    const body: Parameters<typeof api.modDecide>[1] = {
      moderator_id: MOD_ID,
      action,
    };
    if (action === "edit") body.edited_text = edits[r.id] ?? r.text;
    await api.modDecide(r.id, body);
    setFlash(OUTCOME[action]);
    await load();
    setTimeout(() => setFlash(null), 4000);
  }

  if (!queue) return <div className="empty">Loading queue…</div>;

  return (
    <div>
      {flash ? (
        <div className={`flash flash-${flash.tone}`}>{flash.text}</div>
      ) : null}
      {queue.length === 0 ? (
        <div className="empty">
          <h3>Queue is empty</h3>
          <div>All drafts are handled. Post a harmful message to generate more.</div>
        </div>
      ) : null}
      {queue.map((r) => (
        <div className="mod-item" key={r.id}>
          <div className="origin">
            post <b>{r.post_id}</b> · prompt <b>{r.prompt_key}</b> · model <b>{r.llm_model}</b>
          </div>
          <div style={{ display: "grid", gridTemplateColumns: "32px 1fr", gap: 10, marginBottom: 8 }}>
            <Avatar name="Bot" bot size="sm" />
            <div className="muted" style={{ fontSize: 13, alignSelf: "center" }}>
              Draft reply from MMS Bot — edit freely before approving.
            </div>
          </div>
          <textarea
            defaultValue={r.text}
            onChange={(e) => setEdits((prev) => ({ ...prev, [r.id]: e.target.value }))}
          />
          {r.rag_doc_ids.length > 0 ? (
            <div className="rag" style={{ marginTop: 6 }}>
              RAG:{" "}
              {r.rag_doc_ids.map((id) => (
                <code key={id}>{id}</code>
              ))}
            </div>
          ) : null}
          <div className="actions">
            <button className="btn primary" onClick={() => decide(r, "approve")} title="Publish this draft as-is">
              Approve
            </button>
            <button className="btn" onClick={() => decide(r, "edit")} title="Publish your edited version">
              Edit &amp; publish
            </button>
            <button className="btn" onClick={() => decide(r, "polish")} title="Run the RLHF polish model on this draft and publish the rewrite">
              Polish (RLHF)
            </button>
            <button className="btn" onClick={() => decide(r, "escalate")} title="Open a counseling session on this post instead of replying">
              Escalate
            </button>
            <button className="btn danger" onClick={() => decide(r, "reject")} title="Discard this draft; nothing is published">
              Reject
            </button>
          </div>
          <div className="action-legend muted">
            <span><b>Approve</b> publishes the draft as-is</span>
            <span><b>Edit</b> publishes your typed-in edits</span>
            <span><b>Polish (RLHF)</b> runs Member D's alignment model on the draft and publishes the rewrite</span>
            <span><b>Escalate</b> drops the reply and opens a counseling session</span>
            <span><b>Reject</b> discards the draft</span>
          </div>
        </div>
      ))}
    </div>
  );
}
