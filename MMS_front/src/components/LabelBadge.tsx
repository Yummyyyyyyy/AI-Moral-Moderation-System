import type { HarmType } from "../api/types";

interface Props {
  type: HarmType | "neutral";
  score?: number;
  hint?: string | null;
}

export default function LabelBadge({ type, score, hint }: Props) {
  const cls = `badge ${type}`;
  const pct = score !== undefined ? ` ${Math.round(score * 100)}%` : "";
  const hintTxt = hint ? ` · ${hint}` : "";
  return <span className={cls}>{type}{pct}{hintTxt}</span>;
}
