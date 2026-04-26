export type HarmType =
  | "hate"
  | "cyberbullying"
  | "misinformation"
  | "depressive"
  | "self_harm"
  | "other";

export type ReplyStatus =
  | "pending_mod"
  | "auto_approved"
  | "published"
  | "rejected"
  | "edited";

export type ModeratorAction =
  | "approve"
  | "reject"
  | "edit"
  | "polish"
  | "escalate";

export interface Author {
  user_id: string;
  display_name?: string | null;
}

export interface Post {
  id: string;
  author: Author;
  text: string;
  created_at: string;
  source: string;
}

export interface ReplyDraft {
  id: string;
  post_id: string;
  text: string;
  status: ReplyStatus;
  rag_doc_ids: string[];
  prompt_key: string;
  llm_model: string;
  created_at: string;
}

export interface LabelRow {
  id: number;
  post_id: string;
  stage: "binary" | "typed";
  is_harmful: number | null;
  harm_type: HarmType | null;
  score: number;
  strategy_hint: string | null;
  model_details?: {
    harmful?: Record<string, {
      probability: number;
      prediction: number;
      threshold: number;
    }>;
    moral?: {
      label: string;
      probabilities: Record<string, number>;
    };
    severity?: {
      label: string;
      probabilities: Record<string, number>;
    };
  } | null;
  model_version: string;
  created_at: string;
}

export interface FeedItem {
  post: Post;
  labels: LabelRow[];
  replies: ReplyDraft[];
  session_id: string | null;
}

export interface Turn {
  id: string;
  session_id: string;
  role: "user" | "bot" | "system";
  text: string;
  created_at: string;
}

export interface ChatTurnResponse {
  user_turn: Turn;
  bot_turn: Turn;
  safety_trip: boolean;
}
