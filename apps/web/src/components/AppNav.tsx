import { BookMarked, ChevronsLeft, Settings } from "lucide-react";

import { APP_ROUTES, type AppRoute } from "../app/routes";

interface AppNavProps {
  active: AppRoute;
  onChange: (route: AppRoute) => void;
}

export function AppNav({ active, onChange }: AppNavProps) {
  return (
    <nav className="app-nav" aria-label="Production workspace">
      <div className="app-mark" aria-label="OpenStory Studio">
        <BookMarked aria-hidden="true" size={23} strokeWidth={1.7} />
      </div>
      <div className="app-nav__routes">
        {APP_ROUTES.map(({ id, label, icon: Icon }) => (
          <button
            className={active === id ? "is-active" : ""}
            type="button"
            key={id}
            onClick={() => onChange(id)}
            aria-current={active === id ? "page" : undefined}
          >
            <Icon aria-hidden="true" size={21} strokeWidth={1.6} />
            <span>{label}</span>
          </button>
        ))}
      </div>
      <div className="app-nav__utility">
        <button type="button" aria-label="Settings">
          <Settings aria-hidden="true" size={20} strokeWidth={1.6} />
          <span>Settings</span>
        </button>
        <button type="button" aria-label="Collapse navigation">
          <ChevronsLeft aria-hidden="true" size={20} strokeWidth={1.6} />
          <span>Collapse</span>
        </button>
      </div>
    </nav>
  );
}
