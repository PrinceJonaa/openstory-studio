import { useEffect, useRef, useState } from "react";
import { ChevronDown, SlidersHorizontal } from "lucide-react";

export type ViewLayout = "visual" | "balanced" | "detailed";
export type ViewAppearance = "paper" | "dark" | "system";

export interface ViewSettings {
  layout: ViewLayout;
  appearance: ViewAppearance;
  visibleFields: {
    shotType: boolean;
    action: boolean;
    dialogue: boolean;
    characters: boolean;
    location: boolean;
    status: boolean;
    continuityFlags: boolean;
  };
  useAsProjectDefault: boolean;
}

export const DEFAULT_VIEW_SETTINGS: ViewSettings = {
  layout: "balanced",
  appearance: "paper",
  visibleFields: {
    shotType: true,
    action: true,
    dialogue: false,
    characters: false,
    location: false,
    status: true,
    continuityFlags: true,
  },
  useAsProjectDefault: true,
};

const FIELD_LABELS: Array<[keyof ViewSettings["visibleFields"], string]> = [
  ["shotType", "Shot type"],
  ["action", "Action"],
  ["dialogue", "Dialogue"],
  ["characters", "Characters"],
  ["location", "Location"],
  ["status", "Status"],
  ["continuityFlags", "Continuity flags"],
];

function storageKey(projectId: string): string {
  return `openstory:view:${projectId}`;
}

function cloneDefaults(): ViewSettings {
  return {
    ...DEFAULT_VIEW_SETTINGS,
    visibleFields: { ...DEFAULT_VIEW_SETTINGS.visibleFields },
  };
}

function isBooleanRecord(value: unknown): value is Record<string, boolean> {
  return typeof value === "object" && value !== null;
}

function normalizeSettings(value: unknown): ViewSettings | null {
  if (typeof value !== "object" || value === null) return null;
  const candidate = value as Partial<ViewSettings>;
  if (!(["visual", "balanced", "detailed"] as unknown[]).includes(candidate.layout)) return null;
  if (!(["paper", "dark", "system"] as unknown[]).includes(candidate.appearance)) return null;
  if (!isBooleanRecord(candidate.visibleFields)) return null;
  if (typeof candidate.useAsProjectDefault !== "boolean") return null;
  const defaults = DEFAULT_VIEW_SETTINGS.visibleFields;
  for (const key of Object.keys(defaults) as Array<keyof typeof defaults>) {
    if (typeof candidate.visibleFields[key] !== "boolean") return null;
  }
  return candidate as ViewSettings;
}

export function loadViewSettings(projectId: string): ViewSettings {
  try {
    const stored = localStorage.getItem(storageKey(projectId));
    if (!stored) return cloneDefaults();
    return normalizeSettings(JSON.parse(stored)) ?? cloneDefaults();
  } catch {
    return cloneDefaults();
  }
}

export function applyAppearance(appearance: ViewAppearance): void {
  document.documentElement.dataset.theme = appearance;
}

export function saveViewSettings(projectId: string, settings: ViewSettings): void {
  localStorage.setItem(storageKey(projectId), JSON.stringify(settings));
  applyAppearance(settings.appearance);
}

interface ViewPreferencesProps {
  projectId: string;
  settings: ViewSettings;
  onChange: (settings: ViewSettings) => void;
}

export function ViewPreferences({ projectId, settings, onChange }: ViewPreferencesProps) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => applyAppearance(settings.appearance), [settings.appearance]);
  useEffect(() => {
    if (!open) return;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setOpen(false);
    };
    const onPointerDown = (event: PointerEvent) => {
      if (!rootRef.current?.contains(event.target as Node)) setOpen(false);
    };
    document.addEventListener("keydown", onKeyDown);
    document.addEventListener("pointerdown", onPointerDown);
    return () => {
      document.removeEventListener("keydown", onKeyDown);
      document.removeEventListener("pointerdown", onPointerDown);
    };
  }, [open]);

  const update = (next: ViewSettings) => {
    saveViewSettings(projectId, next);
    onChange(next);
  };

  return (
    <div className="view-preferences" ref={rootRef}>
      <button
        className="toolbar-button view-trigger"
        type="button"
        aria-expanded={open}
        onClick={() => setOpen((value) => !value)}
      >
        <SlidersHorizontal aria-hidden="true" size={17} />
        View
        <ChevronDown aria-hidden="true" size={15} />
      </button>
      {open ? (
        <div className="view-popover" role="dialog" aria-label="Customize view">
          <h2>Customize view</h2>
          <fieldset>
            <legend>Panel layout</legend>
            <div className="segmented-control">
              {(["visual", "balanced", "detailed"] as ViewLayout[]).map((layout) => (
                <button
                  className={settings.layout === layout ? "is-active" : ""}
                  type="button"
                  key={layout}
                  onClick={() => update({ ...settings, layout })}
                >
                  {layout[0].toUpperCase() + layout.slice(1)}
                </button>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Show on panel cards</legend>
            <div className="field-switches">
              {FIELD_LABELS.map(([field, label]) => (
                <div className="switch-row" key={field}>
                  <span>{label}</span>
                  <button
                    type="button"
                    role="switch"
                    aria-label={label}
                    aria-checked={settings.visibleFields[field]}
                    className="switch-control"
                    onClick={() =>
                      update({
                        ...settings,
                        visibleFields: {
                          ...settings.visibleFields,
                          [field]: !settings.visibleFields[field],
                        },
                      })
                    }
                  >
                    <span />
                  </button>
                </div>
              ))}
            </div>
          </fieldset>
          <fieldset>
            <legend>Appearance</legend>
            <div className="segmented-control">
              {(["paper", "dark", "system"] as ViewAppearance[]).map((appearance) => (
                <button
                  className={settings.appearance === appearance ? "is-active" : ""}
                  type="button"
                  key={appearance}
                  onClick={() => update({ ...settings, appearance })}
                >
                  {appearance[0].toUpperCase() + appearance.slice(1)}
                </button>
              ))}
            </div>
          </fieldset>
          <div className="switch-row project-default-row">
            <span>Use as project default</span>
            <button
              type="button"
              role="switch"
              aria-label="Use as project default"
              aria-checked={settings.useAsProjectDefault}
              className="switch-control"
              onClick={() =>
                update({ ...settings, useAsProjectDefault: !settings.useAsProjectDefault })
              }
            >
              <span />
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
