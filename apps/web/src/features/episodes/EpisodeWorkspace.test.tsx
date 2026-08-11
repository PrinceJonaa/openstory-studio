import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";

import { api } from "../../lib/api";
import type { EpisodeDetail, SourceChunk } from "../../lib/types";
import { EpisodeWorkspace } from "./EpisodeWorkspace";

vi.mock("../../lib/api", () => ({
  api: {
    listChunks: vi.fn(),
    listEpisodes: vi.fn(),
    getEpisode: vi.fn(),
    adaptEpisode: vi.fn(),
    getStoryboard: vi.fn(),
    buildStoryboard: vi.fn(),
  },
}));

vi.mock("../storyboard/StoryboardDesk", () => ({
  StoryboardDesk: ({ sceneId }: { sceneId: string }) => (
    <div>Storyboard desk for {sceneId}</div>
  ),
}));

const chunks: SourceChunk[] = [
  {
    id: "chunk-1",
    document_id: "document-1",
    ordinal: 1,
    heading: "Chapter One",
    text: "Lira reaches the gate.",
    start_offset: 0,
    end_offset: 22,
  },
  {
    id: "chunk-2",
    document_id: "document-1",
    ordinal: 2,
    heading: "Chapter Two",
    text: "The gate opens.",
    start_offset: 23,
    end_offset: 38,
  },
];

const detail: EpisodeDetail = {
  episode: {
    id: "episode-1",
    project_id: "project-1",
    number: 1,
    title: "The Crossing",
    source_chunk_ids: chunks.map((chunk) => chunk.id),
    logline: "Lira crosses the ward-bound gate.",
    adaptation_notes: "Omissions: none. Reordering: none.",
    status: "draft",
  },
  scenes: [
    {
      id: "scene-1",
      episode_id: "episode-1",
      ordinal: 1,
      title: "At the Gate",
      purpose: "Open the gate.",
      location_entity_id: null,
      character_entity_ids: [],
      summary: "Lira raises the shard.",
      status: "draft",
    },
  ],
};

beforeEach(() => {
  vi.mocked(api.listChunks).mockResolvedValue(chunks);
  vi.mocked(api.listEpisodes).mockResolvedValue([]);
  vi.mocked(api.adaptEpisode).mockResolvedValue({
    job: {
      id: "job-1",
      project_id: "project-1",
      kind: "episode_adapt",
      status: "succeeded",
      progress_current: 1,
      progress_total: 1,
      error: null,
      created_at: "2026-08-10T00:00:00Z",
      updated_at: "2026-08-10T00:00:00Z",
    },
    result: detail,
  });
  vi.mocked(api.getStoryboard).mockResolvedValue([]);
  vi.mocked(api.buildStoryboard).mockResolvedValue({
    job: {
      id: "job-2",
      project_id: "project-1",
      kind: "storyboard_build",
      status: "succeeded",
      progress_current: 1,
      progress_total: 1,
      error: null,
      created_at: "2026-08-10T00:00:00Z",
      updated_at: "2026-08-10T00:00:00Z",
    },
    result: [],
  });
});

it("adapts selected chunks and opens a newly built scene storyboard", async () => {
  const user = userEvent.setup();
  render(
    <EpisodeWorkspace
      projectId="project-1"
      targetFormat="storyboard"
      projectName="The Glass Orchard"
    />,
  );

  expect(await screen.findByText("Chapter One")).toBeVisible();
  await user.click(screen.getByRole("checkbox", { name: "Chapter One" }));
  await user.click(screen.getByRole("checkbox", { name: "Chapter Two" }));
  await user.click(screen.getByRole("button", { name: "Adapt episode" }));

  await waitFor(() =>
    expect(api.adaptEpisode).toHaveBeenCalledWith("project-1", {
      source_chunk_ids: ["chunk-1", "chunk-2"],
      number: 1,
      target_format: "storyboard",
    }),
  );
  expect(await screen.findByRole("heading", { name: "The Crossing" })).toBeVisible();

  await user.click(screen.getByRole("button", { name: "Build storyboard" }));

  await waitFor(() => expect(api.buildStoryboard).toHaveBeenCalledWith("scene-1"));
  expect(await screen.findByText("Storyboard desk for scene-1")).toBeVisible();
});
