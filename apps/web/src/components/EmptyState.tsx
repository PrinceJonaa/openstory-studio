import { ImageOff } from "lucide-react";

interface EmptyStateProps {
  title: string;
  detail?: string;
  compact?: boolean;
}

export function EmptyState({ title, detail, compact = false }: EmptyStateProps) {
  return (
    <div className={`empty-state ${compact ? "empty-state--compact" : ""}`}>
      <ImageOff aria-hidden="true" size={compact ? 20 : 28} strokeWidth={1.5} />
      <strong>{title}</strong>
      {detail ? <span>{detail}</span> : null}
    </div>
  );
}
