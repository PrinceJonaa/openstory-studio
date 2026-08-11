import {
  BookOpenText,
  Clapperboard,
  FileText,
  Images,
  LayoutDashboard,
  ListChecks,
  type LucideIcon,
} from "lucide-react";

export type AppRoute = "overview" | "source" | "canon" | "episodes" | "assets" | "jobs";

export interface RouteDefinition {
  id: AppRoute;
  label: string;
  icon: LucideIcon;
}

export const APP_ROUTES: RouteDefinition[] = [
  { id: "overview", label: "Overview", icon: LayoutDashboard },
  { id: "source", label: "Source", icon: FileText },
  { id: "canon", label: "Canon", icon: BookOpenText },
  { id: "episodes", label: "Episodes", icon: Clapperboard },
  { id: "assets", label: "Assets", icon: Images },
  { id: "jobs", label: "Jobs", icon: ListChecks },
];
