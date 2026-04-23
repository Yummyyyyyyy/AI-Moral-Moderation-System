import type {
  ChatTurnResponse,
  FeedItem,
  ModeratorAction,
  Post,
  ReplyDraft,
  Turn,
} from "./types";

async function j<T>(rp: Promise<Response>): Promise<T> {
  const r = await rp;
  if (!r.ok) throw new Error(`${r.status} ${await r.text()}`);
  return (await r.json()) as T;
}

export const api = {
  ingest: (post: Partial<Post> & { text: string; id: string; author: Post["author"] }) =>
    j<{ post_id: string; is_harmful: boolean; harm_type: string | null; reply: ReplyDraft | null; session: { id: string } | null }>(
      fetch("/ingest", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(post) }),
    ),

  feed: () => j<FeedItem[]>(fetch("/posts")),

  post: (id: string) => j<FeedItem>(fetch(`/posts/${id}`)),

  modQueue: () => j<ReplyDraft[]>(fetch("/mod/queue")),

  modDecide: (
    replyId: string,
    body: { moderator_id: string; action: ModeratorAction; edited_text?: string; note?: string },
  ) =>
    j<{ reply: ReplyDraft; decision: unknown }>(
      fetch(`/mod/${replyId}/decide`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      }),
    ),

  sessionMessages: (sessionId: string) => j<Turn[]>(fetch(`/sessions/${sessionId}/messages`)),

  sessionSend: (sessionId: string, text: string) =>
    j<ChatTurnResponse>(
      fetch(`/sessions/${sessionId}/messages`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      }),
    ),

  reset: () =>
    j<{ wiped_tables: string[]; reseeded: number }>(
      fetch("/admin/reset", { method: "POST" }),
    ),
};
