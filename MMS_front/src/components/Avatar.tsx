interface Props {
  name: string;
  bot?: boolean;
  size?: "sm" | "md";
}

function initials(name: string): string {
  const cleaned = name.replace(/^[@u-]+/i, "").trim();
  if (!cleaned) return "?";
  const parts = cleaned.split(/[\s_\-]+/).filter(Boolean);
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[1][0]).toUpperCase();
}

export default function Avatar({ name, bot, size = "md" }: Props) {
  const style = size === "sm" ? { width: 32, height: 32, fontSize: 13 } : undefined;
  return (
    <div className={`avatar${bot ? " bot" : ""}`} style={style}>
      {bot ? "◆" : initials(name)}
    </div>
  );
}
