import type {
  CanonEntity,
  CanonFact,
  Episode,
  EpisodeDetail,
  Job,
  JobRunResult,
  ProductionStatus,
  Project,
  RenderVersion,
  SourceChunk,
  SourceDocument,
  SourceIngestionResult,
  StoryboardPanel,
  TargetFormat,
} from "./types";
import { demoRenderUrl, demoRequest } from "./demoApi";

const API_BASE_URL = (import.meta.env.VITE_OPENSTORY_API_URL ?? "/api").replace(/\/$/, "");
const DEMO_MODE = import.meta.env.VITE_OPENSTORY_DEMO_MODE === "true"
  || window.location.hostname === "terminal.local";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly detail: string,
  ) {
    super(detail);
    this.name = "ApiError";
  }
}

async function requestJson<T>(path: string, init: RequestInit = {}): Promise<T> {
  if (DEMO_MODE) return await demoRequest(path, init) as T;
  const headers = new Headers(init.headers);
  if (init.body && !(init.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (!response.ok) {
    let detail = response.statusText || "Request failed";
    try {
      const payload = (await response.json()) as { detail?: string };
      detail = payload.detail ?? detail;
    } catch {
      // Preserve the HTTP status text when an upstream error is not JSON.
    }
    throw new ApiError(response.status, detail);
  }
  return (await response.json()) as T;
}

function jsonBody(value: unknown): string {
  return JSON.stringify(value);
}

export const api = {
  listProjects: () => requestJson<Project[]>("/projects"),
  getProject: (projectId: string) => requestJson<Project>(`/projects/${projectId}`),
  createProject: (input: { name: string; description?: string; target_format: TargetFormat }) =>
    requestJson<Project>("/projects", { method: "POST", body: jsonBody(input) }),

  uploadSource: (projectId: string, file: File) => {
    const form = new FormData();
    form.append("file", file);
    return requestJson<SourceIngestionResult>(`/projects/${projectId}/sources`, {
      method: "POST",
      body: form,
    });
  },
  listSources: (projectId: string) =>
    requestJson<SourceDocument[]>(`/projects/${projectId}/sources`),
  listChunks: (projectId: string) =>
    requestJson<SourceChunk[]>(`/projects/${projectId}/chunks`),

  extractCanon: (projectId: string, chunkIds?: string[]) =>
    requestJson<JobRunResult<unknown>>(`/projects/${projectId}/canon/extract`, {
      method: "POST",
      body: jsonBody(chunkIds ? { chunk_ids: chunkIds } : {}),
    }),
  listEntities: (projectId: string) =>
    requestJson<CanonEntity[]>(`/projects/${projectId}/entities`),
  listFacts: (projectId: string) => requestJson<CanonFact[]>(`/projects/${projectId}/facts`),

  adaptEpisode: (
    projectId: string,
    input: { source_chunk_ids: string[]; number: number; target_format: TargetFormat },
  ) =>
    requestJson<JobRunResult<EpisodeDetail>>(`/projects/${projectId}/episodes/adapt`, {
      method: "POST",
      body: jsonBody(input),
    }),
  listEpisodes: (projectId: string) =>
    requestJson<Episode[]>(`/projects/${projectId}/episodes`),
  getEpisode: (episodeId: string) => requestJson<EpisodeDetail>(`/episodes/${episodeId}`),
  updateEpisodeStatus: (episodeId: string, status: ProductionStatus) =>
    requestJson<Episode>(`/episodes/${episodeId}/status`, {
      method: "PATCH",
      body: jsonBody({ status }),
    }),
  updateSceneStatus: (sceneId: string, status: ProductionStatus) =>
    requestJson(`/scenes/${sceneId}/status`, {
      method: "PATCH",
      body: jsonBody({ status }),
    }),

  buildStoryboard: (sceneId: string) =>
    requestJson<JobRunResult<StoryboardPanel[]>>(`/scenes/${sceneId}/storyboard`, {
      method: "POST",
    }),
  getStoryboard: (sceneId: string) =>
    requestJson<StoryboardPanel[]>(`/scenes/${sceneId}/storyboard`),
  updatePanelStatus: (panelId: string, status: ProductionStatus) =>
    requestJson<StoryboardPanel>(`/panels/${panelId}/status`, {
      method: "PATCH",
      body: jsonBody({ status }),
    }),
  renderPanel: (panelId: string) =>
    requestJson<JobRunResult<RenderVersion>>(`/panels/${panelId}/render`, {
      method: "POST",
      body: jsonBody({}),
    }),
  renderScene: (sceneId: string) =>
    requestJson<JobRunResult<RenderVersion[]>>(`/scenes/${sceneId}/render`, {
      method: "POST",
      body: jsonBody({}),
    }),
  listPanelRenders: (panelId: string) =>
    requestJson<RenderVersion[]>(`/panels/${panelId}/renders`),
  getRenderFileUrl: (renderId: string) => DEMO_MODE
    ? demoRenderUrl(renderId)
    : `${API_BASE_URL}/renders/${renderId}/file`,
  updateRenderStatus: (renderId: string, status: ProductionStatus) =>
    requestJson<RenderVersion>(`/renders/${renderId}/status`, {
      method: "PATCH",
      body: jsonBody({ status }),
    }),

  listJobs: (projectId: string) => requestJson<Job[]>(`/projects/${projectId}/jobs`),
};
