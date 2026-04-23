import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { FeedItem } from "../api/types";
import PostCard from "../components/PostCard";

export default function FeedPage() {
  const [items, setItems] = useState<FeedItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    try {
      setItems(await api.feed());
      setError(null);
    } catch (e) {
      setError(String(e));
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 4000);
    return () => clearInterval(t);
  }, []);

  if (error) return <div className="empty"><h3>Error</h3><div>{error}</div></div>;
  if (!items) return <div className="empty">Loading feed…</div>;
  if (items.length === 0)
    return (
      <div className="empty">
        <h3>No posts yet</h3>
        <div>
          Compose one from the <a href="/ingest">Compose</a> page, or seed a batch:
          <div style={{ fontFamily: "ui-monospace, Menlo, monospace", marginTop: 8 }}>
            python scripts/seed_mock.py data/mock_posts.jsonl
          </div>
        </div>
      </div>
    );
  return (
    <div>
      {items.map((it) => (
        <PostCard key={it.post.id} item={it} />
      ))}
    </div>
  );
}
