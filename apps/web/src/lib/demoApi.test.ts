import { expect, it } from "vitest";

import type { Project, StoryboardPanel } from "./types";
import { demoRenderUrl, demoRequest } from "./demoApi";

it("serves a deterministic interactive project without a running backend", async () => {
  const projects = await demoRequest("/projects") as Project[];
  expect(projects).toHaveLength(1);
  expect(projects[0]?.name).toBe("The Glass Orchard");

  const panels = await demoRequest("/scenes/scene-crossing/storyboard") as StoryboardPanel[];
  expect(panels).toHaveLength(6);
  expect(panels.filter((panel) => panel.status === "review")).toHaveLength(2);

  const updated = await demoRequest("/panels/panel-2/status", {
    method: "PATCH",
    body: JSON.stringify({ status: "approved" }),
  }) as StoryboardPanel;
  expect(updated.status).toBe("approved");
  expect(demoRenderUrl("render-panel-2-v1")).toBe("/demo/panel-0002.png");
});
