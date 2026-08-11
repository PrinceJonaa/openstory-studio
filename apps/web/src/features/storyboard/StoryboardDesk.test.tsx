import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";

import { api } from "../../lib/api";
import type { EpisodeDetail, StoryboardPanel } from "../../lib/types";
import { StoryboardDesk } from "./StoryboardDesk";

vi.mock("../../lib/api", () => ({
  api: {
    getEpisode: vi.fn(),
    getStoryboard: vi.fn(),
    listEntities: vi.fn(),
    listFacts: vi.fn(),
    listChunks: vi.fn(),
    listPanelRenders: vi.fn(),
    updatePanelStatus: vi.fn(),
    renderPanel: vi.fn(),
    renderScene: vi.fn(),
    getRenderFileUrl: vi.fn((renderId: string) => `/renders/${renderId}/file`),
  },
}));

const episode: EpisodeDetail = {
  episode: {
    id: "episode-1",
    project_id: "project-1",
    number: 1,
    title: "The Crossing",
    source_chunk_ids: ["chunk-1", "chunk-2"],
    logline: "Lira risks the shard to cross the gate.",
    adaptation_notes: "Omissions: none. Reordering: none.",
    status: "draft",
  },
  scenes: [
    {
      id: "scene-1",
      episode_id: "episode-1",
      ordinal: 2,
      title: "At the Gate",
      purpose: "Open the ward-bound gate.",
      location_entity_id: "gate",
      character_entity_ids: ["lira", "ashen"],
      summary: "Lira raises the shard and the North Gate opens.",
      status: "draft",
    },
  ],
};

function panel(ordinal: number, status: StoryboardPanel["status"]): StoryboardPanel {
  return {
    id: `panel-${ordinal}`,
    scene_id: "scene-1",
    ordinal,
    shot_type: ordinal === 1 ? "wide" : "medium close-up",
    framing: "eye-level",
    action: ordinal === 2 ? "Lira raises the shard." : `Visual beat ${ordinal}.`,
    visual_description: `Panel ${ordinal} at the North Gate.`,
    dialogue:
      ordinal === 3
        ? [{ speaker_entity_id: null, speaker_name: "Guard", text: "State your purpose." }]
        : [],
    character_entity_ids: ["lira"],
    location_entity_id: "gate",
    referenced_asset_ids: [],
    image_prompt: `Storyboard panel ${ordinal}.`,
    negative_prompt: null,
    render_status: "unrendered",
    status,
  };
}

const panels = [
  panel(1, "approved"),
  panel(2, "review"),
  panel(3, "draft"),
  panel(4, "approved"),
  panel(5, "review"),
  panel(6, "draft"),
];

beforeEach(() => {
  vi.mocked(api.getEpisode).mockResolvedValue(episode);
  vi.mocked(api.getStoryboard).mockResolvedValue(panels);
  vi.mocked(api.listEntities).mockResolvedValue([]);
  vi.mocked(api.listFacts).mockResolvedValue([]);
  vi.mocked(api.listChunks).mockResolvedValue([]);
  vi.mocked(api.listPanelRenders).mockResolvedValue([]);
  vi.mocked(api.updatePanelStatus).mockImplementation(async (panelId, status) => ({
    ...panels.find((item) => item.id === panelId)!,
    status,
  }));
});

it("renders the balanced board and opens the selected panel inspector", async () => {
  const user = userEvent.setup();
  render(
    <StoryboardDesk projectId="project-1" episodeId="episode-1" sceneId="scene-1" />,
  );

  expect(await screen.findByRole("heading", { name: "Scene 2 · At the Gate" })).toBeVisible();
  expect(screen.getAllByTestId("panel-card")).toHaveLength(6);

  await user.click(screen.getByRole("button", { name: "Select panel 2" }));

  expect(screen.getByRole("heading", { name: "Panel 2" })).toBeVisible();
  expect(screen.getAllByText("Lira raises the shard.")).toHaveLength(2);
});

it("batch approves only panels currently in review", async () => {
  const user = userEvent.setup();
  render(
    <StoryboardDesk projectId="project-1" episodeId="episode-1" sceneId="scene-1" />,
  );
  await screen.findByRole("heading", { name: "Scene 2 · At the Gate" });

  await user.click(screen.getByRole("button", { name: "Batch approve (2)" }));

  await waitFor(() => expect(api.updatePanelStatus).toHaveBeenCalledTimes(2));
  expect(api.updatePanelStatus).toHaveBeenCalledWith("panel-2", "approved");
  expect(api.updatePanelStatus).toHaveBeenCalledWith("panel-5", "approved");
});
