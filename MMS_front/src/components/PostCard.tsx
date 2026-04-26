import { Link } from "react-router-dom";
import type { FeedItem, HarmType, ReplyDraft } from "../api/types";
import Avatar from "./Avatar";
import { useViewMode } from "../viewMode";

function timeAgo(iso: string): string {
  const d = new Date(iso);
  const diff = (Date.now() - d.getTime()) / 1000;
  if (diff < 60) return `${Math.floor(diff)}s`;
  if (diff < 3600) return `${Math.floor(diff / 60)}m`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h`;
  return d.toLocaleDateString();
}

function derive(item: FeedItem) {
  let binary: { harmful: boolean; score: number } | null = null;
  let typed: {
    type: HarmType;
    score: number;
    hint: string | null;
    details: FeedItem["labels"][number]["model_details"];
  } | null = null;

  for (const label of item.labels) {
    if (label.stage === "binary") {
      binary = { harmful: !!label.is_harmful, score: label.score };
    }
    if (label.stage === "typed" && label.harm_type) {
      typed = {
        type: label.harm_type,
        score: label.score,
        hint: label.strategy_hint,
        details: label.model_details,
      };
    }
  }
  return { binary, typed };
}

function bestProbability(probs: Record<string, number>, label: string): number {
  return probs[label] ?? 0;
}

function ReplyRow({ reply, admin }: { reply: ReplyDraft; admin: boolean }) {
  const cls =
    reply.status === "rejected"
      ? "reply-card rejected"
      : reply.status === "pending_mod"
        ? "reply-card pending"
        : "reply-card";
  const badgeCls =
    reply.status === "pending_mod"
      ? "badge pending"
      : reply.status === "rejected"
        ? "badge rejected"
        : reply.status === "edited"
          ? "badge edited"
          : "badge approved";

  return (
    <div className={cls}>
      <Avatar name="Bot" bot size="sm" />
      <div className="body">
        <div className="meta">
          <span className="name">MMS Bot</span>
          <span>@mms-bot</span>
          <span>-</span>
          <span>{timeAgo(reply.created_at)}</span>
          {admin ? <span className={badgeCls}>{reply.status.replace("_", " ")}</span> : null}
          {admin ? (
            <span className="muted" style={{ fontSize: 12 }}>
              {reply.prompt_key} - {reply.llm_model}
            </span>
          ) : null}
        </div>
        <div className="text">{reply.text}</div>
        {admin && reply.rag_doc_ids.length > 0 ? (
          <div className="rag">
            RAG:{" "}
            {reply.rag_doc_ids.map((id) => (
              <code key={id}>{id}</code>
            ))}
          </div>
        ) : null}
      </div>
    </div>
  );
}

export default function PostCard({ item }: { item: FeedItem }) {
  const [mode] = useViewMode();
  const admin = mode === "admin";
  const { binary, typed } = derive(item);
  const author = item.post.author.display_name || item.post.author.user_id;
  const handle = item.post.author.user_id;
  const visibleReplies = item.replies;
  const pendingBlocked =
    visibleReplies.length === 0 && binary?.harmful && !item.session_id;

  return (
    <article className="post">
      <Avatar name={author} />
      <div className="post-body">
        <div className="post-meta">
          <span className="name">{author}</span>
          <span className="handle">@{handle}</span>
          <span className="dot">-</span>
          <span className="ts">{timeAgo(item.post.created_at)}</span>
        </div>
        <div className="post-text">{item.post.text}</div>

        {admin ? (
          <div className="chips">
            {binary ? (
              <span className={`chip ${binary.harmful ? "hate" : "neutral"}`}>
                <span className="lbl">C1</span>
                {binary.harmful ? "harmful" : "neutral"}: {Math.round(binary.score * 100)}%
              </span>
            ) : null}
            {typed?.details ? (
              <>
                {Object.entries(typed.details.harmful ?? {})
                  .filter(([, value]) => value.prediction === 1)
                  .map(([label, value]) => (
                    <span key={`harmful-${label}`} className="chip model-chip active">
                      <span className="lbl">harmful</span>
                      {label}: {Math.round(value.probability * 100)}%
                    </span>
                  ))}
                {typed.details.moral ? (
                  <span className="chip model-chip selected">
                    <span className="lbl">moral</span>
                    {typed.details.moral.label}:{" "}
                    {Math.round(
                      bestProbability(
                        typed.details.moral.probabilities,
                        typed.details.moral.label,
                      ) * 100,
                    )}
                    %
                  </span>
                ) : null}
                {typed.details.severity ? (
                  <span className="chip model-chip severity">
                    <span className="lbl">severity</span>
                    {typed.details.severity.label}:{" "}
                    {Math.round(
                      bestProbability(
                        typed.details.severity.probabilities,
                        typed.details.severity.label,
                      ) * 100,
                    )}
                    %
                  </span>
                ) : null}
              </>
            ) : typed ? (
              <span className={`chip ${typed.type}`}>
                <span className="lbl">C2</span>
                {typed.type}: {Math.round(typed.score * 100)}%
              </span>
            ) : null}
            {typed?.hint ? (
              <span className="chip stage">
                <span className="lbl">hint</span>
                {typed.hint}
              </span>
            ) : null}
          </div>
        ) : null}

        {visibleReplies.length > 0 ? (
          <div className="thread">
            {visibleReplies.map((reply) => (
              <ReplyRow key={reply.id} reply={reply} admin={admin} />
            ))}
          </div>
        ) : null}

        {admin && pendingBlocked ? (
          <div className="thread">
            <div className="reply-card pending">
              <Avatar name="Bot" bot size="sm" />
              <div className="body">
                <div className="meta">
                  <span className="name">MMS Bot</span>
                  <span className="badge pending">awaiting moderator</span>
                </div>
                <div className="text muted">
                  A persuasion draft was generated and is queued for human review.
                </div>
              </div>
            </div>
          </div>
        ) : null}

        {item.session_id ? (
          <Link className="session-cta" to={`/chat/${item.session_id}`}>
            Open counseling session -&gt;
          </Link>
        ) : null}
      </div>
    </article>
  );
}
