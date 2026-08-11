import { Check, Circle, LockKeyhole, RotateCcw } from "lucide-react";

import type { ProductionStatus } from "../lib/types";

const LABELS: Record<ProductionStatus, string> = {
  draft: "Draft",
  review: "Needs review",
  approved: "Approved",
  locked: "Locked",
  revise: "Revise",
};

export function StatusPill({ status }: { status: ProductionStatus }) {
  const Icon = status === "approved" ? Check : status === "locked" ? LockKeyhole : status === "revise" ? RotateCcw : Circle;
  return (
    <span className={`status-pill status-pill--${status}`}>
      <Icon aria-hidden="true" size={13} />
      {LABELS[status]}
    </span>
  );
}
