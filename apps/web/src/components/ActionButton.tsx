import type { ButtonHTMLAttributes, ReactNode } from "react";

interface ActionButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  tone?: "primary" | "secondary" | "quiet";
}

export function ActionButton({ children, className = "", tone = "secondary", ...props }: ActionButtonProps) {
  return (
    <button className={`action-button action-button--${tone} ${className}`.trim()} {...props}>
      {children}
    </button>
  );
}
