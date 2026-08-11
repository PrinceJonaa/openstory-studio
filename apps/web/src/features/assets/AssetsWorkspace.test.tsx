import { render, screen } from "@testing-library/react";
import { beforeEach, expect, it, vi } from "vitest";

import { api } from "../../lib/api";
import type { Episode, EpisodeDetail, RenderVersion, StoryboardPanel } from "../../lib/types";
import { AssetsWorkspace } from "./AssetsWorkspace";

vi.mock("../../lib/api", () => ({
  api: {
    listEpisodes: vi.fn(),
    getEpisode: vi.fn(),
    getStoryboard: vi.fn(),
    listPanelRenders: vi.fn(),
    getRenderFileUrl: vi.fn((id: string) => `/renders/${id}/file`),
  },
}));

const episode: Episode = {
  id: "episode-1",
  project_id: "project-1",
  number: 1,
  title: "The Crossing",
  source_chunk_ids: ["chunk-1"],
  logline: "Lira crosses the gate.",
  adaptation_notes: "None.",
  status: "draft",
};
const detail: EpisodeDetail = {
  episode,
  scenes: [{
    id: "scene-1",
    episode_id: "episode-1",
    ordinal: 1,
    title: "At the Gate",
    purpose: "Cross.",
    location_entity_id: null,
    character_entity_ids: [],
    summary: "The gate opens.",
    status: "draft",
  }],
};
const panel: StoryboardPanel = {
  id: "panel-1",
  scene_id: "scene-1",
  ordinal: 1,
  shot_type: "wide",
  framing: "establishing",
  action: "The gate opens.",
  visual_description: "A wide view of the gate.",
  dialogue: [],
  character_entity_ids: [],
  location_entity_id: null,
  referenced_asset_ids: [],
  image_prompt: "Gate.",
  negative_prompt: null,
  render_status: "rendered",
  status: "draft",
};
const renderVersion: RenderVersion = {
  id: "render-1",
  panel_id: "panel-1",
  version: 1,
  output_path: "renders/panel-0001/v001.png",
  width: 768,
  height: 1024,
  seed: 42,
  provider: "placeholder",
  metadata: {},
  status: "draft",
  created_at: "2026-08-10T00:00:00Z",
};

beforeEach(() => {
  vi.mocked(api.listEpisodes).mockResolvedValue([episode]);
  vi.mocked(api.getEpisode).mockResolvedValue(detail);
  vi.mocked(api.getStoryboard).mockResolvedValue([panel]);
  vi.mocked(api.listPanelRenders).mockResolvedValue([renderVersion]);
});

it("collects versioned storyboard renders into the asset workspace", async () => {
  render(<AssetsWorkspace projectId="project-1" />);

  expect(await screen.findByRole("img", { name: "Episode 1, scene 1, panel 1" })).toHaveAttribute(
    "src",
    "/renders/render-1/file",
  );
  expect(screen.getByText("v001")).toBeVisible();
  expect(screen.getByText("placeholder")).toBeVisible();
});
