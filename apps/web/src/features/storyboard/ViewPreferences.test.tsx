import { useState } from "react";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { expect, it } from "vitest";

import type { StoryboardPanel } from "../../lib/types";
import {
  DEFAULT_VIEW_SETTINGS,
  ViewPreferences,
  loadViewSettings,
  saveViewSettings,
  type ViewSettings,
} from "./ViewPreferences";

function ViewPreferencesHarness({ projectId }: { projectId: string }) {
  const [settings, setSettings] = useState(() => loadViewSettings(projectId));
  return (
    <ViewPreferences
      projectId={projectId}
      settings={settings}
      onChange={setSettings}
    />
  );
}

function makePanel(): StoryboardPanel {
  return {
    id: "panel-1",
    scene_id: "scene-1",
    ordinal: 1,
    shot_type: "medium",
    framing: "eye-level",
    action: "Lira raises the shard.",
    visual_description: "Cold light catches on Lira's face.",
    dialogue: [],
    character_entity_ids: ["lira"],
    location_entity_id: "gate",
    referenced_asset_ids: [],
    image_prompt: "Storyboard of Lira raising the shard.",
    negative_prompt: null,
    render_status: "unrendered",
    status: "draft",
  };
}

it("persists project-specific view fields without changing panel data", async () => {
  const user = userEvent.setup();
  const panel = makePanel();
  render(<ViewPreferencesHarness projectId="project-a" />);

  await user.click(screen.getByRole("button", { name: "View" }));
  await user.click(screen.getByRole("switch", { name: "Dialogue" }));
  await user.click(screen.getByRole("button", { name: "Detailed" }));

  expect(loadViewSettings("project-a").layout).toBe("detailed");
  expect(loadViewSettings("project-a").visibleFields.dialogue).toBe(true);
  expect(panel.action).toBe("Lira raises the shard.");
});

it("keeps independent settings for each project and repairs invalid storage", () => {
  const detailed: ViewSettings = {
    ...DEFAULT_VIEW_SETTINGS,
    layout: "detailed",
  };
  saveViewSettings("project-a", detailed);
  localStorage.setItem("openstory:view:project-b", "not-json");

  expect(loadViewSettings("project-a").layout).toBe("detailed");
  expect(loadViewSettings("project-b")).toEqual(DEFAULT_VIEW_SETTINGS);
});

it("applies appearance to the document root", async () => {
  const user = userEvent.setup();
  render(<ViewPreferencesHarness projectId="project-a" />);

  await user.click(screen.getByRole("button", { name: "View" }));
  await user.click(screen.getByRole("button", { name: "Dark" }));

  expect(document.documentElement.dataset.theme).toBe("dark");
  expect(loadViewSettings("project-a").appearance).toBe("dark");
});

it("closes the view popover on Escape", async () => {
  const user = userEvent.setup();
  render(<ViewPreferencesHarness projectId="project-a" />);

  await user.click(screen.getByRole("button", { name: "View" }));
  expect(screen.getByRole("dialog", { name: "Customize view" })).toBeVisible();

  await user.keyboard("{Escape}");

  expect(screen.queryByRole("dialog", { name: "Customize view" })).not.toBeInTheDocument();
});
