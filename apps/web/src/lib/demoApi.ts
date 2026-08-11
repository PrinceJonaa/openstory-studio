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
} from "./types";

const NOW = "2026-08-11T00:00:00Z";
const PROJECT_ID = "project-glass-orchard";

const project: Project = {
  id: PROJECT_ID,
  name: "The Glass Orchard",
  slug: "the-glass-orchard",
  description: "An original story about memory, ward-bound cities, and a dangerous inheritance.",
  target_format: "storyboard",
  created_at: NOW,
  updated_at: NOW,
};

const documents: SourceDocument[] = [{
  id: "document-glass-orchard",
  project_id: PROJECT_ID,
  filename: "glass_orchard.md",
  media_type: "text/markdown",
  sha256: "demo-glass-orchard",
  workspace_path: "source/glass_orchard.md",
}];

const chunks: SourceChunk[] = [
  {
    id: "chunk-shard",
    document_id: documents[0]!.id,
    ordinal: 1,
    heading: "Chapter 1: The Shard",
    text: "Lira Vale carried a palm-sized Glass Shard wrapped in blue cloth. The Glass Shard belonged to Lira, a keepsake left by her mother.\n\nWhen Lira whispered the old word “Aster,” the Glass Shard answered with a cold blue light. Ashen saw the light and warned her that the wardens would notice.",
    start_offset: 0,
    end_offset: 292,
  },
  {
    id: "chunk-crossing",
    document_id: documents[0]!.id,
    ordinal: 2,
    heading: "Chapter 2: The Crossing",
    text: "At late afternoon, Lira and Ashen reached the North Gate. The North Gate stood above a reed-choked causeway and was bound by the oldest wards in the city.\n\nThe lead guard stepped forward and asked their purpose. Lira raised the Glass Shard in her palm. Its cold blue pulse crossed the glass-etched seals, and the North Gate opened.",
    start_offset: 293,
    end_offset: 620,
  },
];

const entities: CanonEntity[] = [
  {
    id: "entity-lira",
    project_id: PROJECT_ID,
    kind: "character",
    canonical_name: "Lira",
    aliases: ["Lira Vale"],
    summary: "Bearer of the Glass Shard.",
    attributes: {},
  },
  {
    id: "entity-ashen",
    project_id: PROJECT_ID,
    kind: "character",
    canonical_name: "Ashen",
    aliases: [],
    summary: "Lira's wary companion.",
    attributes: {},
  },
  {
    id: "entity-shard",
    project_id: PROJECT_ID,
    kind: "object",
    canonical_name: "Glass Shard",
    aliases: [],
    summary: "A palm-sized keepsake wrapped in blue cloth.",
    attributes: { light: "cold blue" },
  },
  {
    id: "entity-gate",
    project_id: PROJECT_ID,
    kind: "location",
    canonical_name: "North Gate",
    aliases: [],
    summary: "A ward-bound city gate above a reed-choked causeway.",
    attributes: {},
  },
];

const facts: CanonFact[] = [
  {
    id: "fact-carries",
    project_id: PROJECT_ID,
    subject_entity_id: "entity-lira",
    predicate: "carries",
    object_entity_id: "entity-shard",
    value: null,
    valid_from_ordinal: 1,
    valid_to_ordinal: null,
    source_chunk_id: "chunk-shard",
    evidence: "Lira Vale carried a palm-sized Glass Shard wrapped in blue cloth.",
    confidence: 0.98,
  },
  {
    id: "fact-belongs",
    project_id: PROJECT_ID,
    subject_entity_id: "entity-shard",
    predicate: "belongs_to",
    object_entity_id: "entity-lira",
    value: null,
    valid_from_ordinal: 1,
    valid_to_ordinal: null,
    source_chunk_id: "chunk-shard",
    evidence: "The Glass Shard belonged to Lira, a keepsake left by her mother.",
    confidence: 0.96,
  },
  {
    id: "fact-reached-lira",
    project_id: PROJECT_ID,
    subject_entity_id: "entity-lira",
    predicate: "reached",
    object_entity_id: "entity-gate",
    value: null,
    valid_from_ordinal: 2,
    valid_to_ordinal: null,
    source_chunk_id: "chunk-crossing",
    evidence: "At late afternoon, Lira and Ashen reached the North Gate.",
    confidence: 0.98,
  },
  {
    id: "fact-opened",
    project_id: PROJECT_ID,
    subject_entity_id: "entity-gate",
    predicate: "opened_in_response_to",
    object_entity_id: null,
    value: "Glass Shard cold blue pulse",
    valid_from_ordinal: 2,
    valid_to_ordinal: null,
    source_chunk_id: "chunk-crossing",
    evidence: "Its cold blue pulse crossed the glass-etched seals, and the North Gate opened.",
    confidence: 0.97,
  },
];

const episode: Episode = {
  id: "episode-crossing",
  project_id: PROJECT_ID,
  number: 1,
  title: "The Crossing",
  source_chunk_ids: chunks.map((chunk) => chunk.id),
  logline: "Lira risks exposing a mysterious heirloom to pass a ward-bound gate.",
  adaptation_notes: "Omissions: incidental guard dialogue is compressed. Reordering: none; causal order is preserved.",
  status: "draft",
};

const episodeDetail: EpisodeDetail = {
  episode,
  scenes: [
    {
      id: "scene-shard",
      episode_id: episode.id,
      ordinal: 1,
      title: "The Shard Awakens",
      purpose: "Introduce Lira, Ashen, and the shard's dangerous response.",
      location_entity_id: null,
      character_entity_ids: ["entity-lira", "entity-ashen"],
      summary: "Lira reveals the Glass Shard and wakes its cold blue light; Ashen warns that the wardens may notice.",
      status: "draft",
    },
    {
      id: "scene-crossing",
      episode_id: episode.id,
      ordinal: 2,
      title: "At the Gate",
      purpose: "Turn the shard's power into a visible crossing of the city wards.",
      location_entity_id: "entity-gate",
      character_entity_ids: ["entity-lira", "entity-ashen"],
      summary: "At the North Gate, Lira raises the Glass Shard; its pulse crosses the seals and opens the way.",
      status: "review",
    },
  ],
};

const panelData: Array<Pick<StoryboardPanel, "shot_type" | "framing" | "action" | "visual_description" | "dialogue" | "character_entity_ids">> = [
  {
    shot_type: "wide",
    framing: "establishing, eye-level",
    action: "Lira and Ashen arrive at the North Gate.",
    visual_description: "The ward-bound North Gate towers over a reed-choked causeway as Lira and Ashen approach in late-afternoon light.",
    dialogue: [],
    character_entity_ids: ["entity-lira", "entity-ashen"],
  },
  {
    shot_type: "medium close-up",
    framing: "waist-up, slight low angle",
    action: "Lira raises the wrapped Glass Shard in her palm.",
    visual_description: "Lira steps forward and lifts the palm-sized shard toward the gate's glass-etched seals; Ashen watches behind her.",
    dialogue: [],
    character_entity_ids: ["entity-lira", "entity-ashen"],
  },
  {
    shot_type: "reverse angle",
    framing: "guard eyeline, medium close-up",
    action: "The lead guard blocks the path and questions Lira.",
    visual_description: "A stern guard fills the foreground while Lira holds her ground beyond his shoulder.",
    dialogue: [{ speaker_entity_id: null, speaker_name: "Lead Guard", text: "State your purpose." }],
    character_entity_ids: ["entity-lira"],
  },
  {
    shot_type: "extreme close-up",
    framing: "insert shot, centered",
    action: "Cold blue light pulses from the Glass Shard.",
    visual_description: "The shard rests in Lira's palm as a sharp blue pulse catches every etched edge and leaps toward the seals.",
    dialogue: [],
    character_entity_ids: ["entity-lira"],
  },
  {
    shot_type: "two-shot",
    framing: "tight profile two-shot",
    action: "Ashen leans toward Lira as the wards begin to react.",
    visual_description: "Lira watches the seals while Ashen turns toward her, tension held between their profiles and the growing light.",
    dialogue: [{ speaker_entity_id: "entity-ashen", speaker_name: "Ashen", text: "The wardens will see this." }],
    character_entity_ids: ["entity-lira", "entity-ashen"],
  },
  {
    shot_type: "wide",
    framing: "symmetrical reveal",
    action: "The North Gate opens and reveals the passage beyond.",
    visual_description: "The seals flare, the massive gate parts, and Lira and Ashen become small silhouettes before the newly opened path.",
    dialogue: [],
    character_entity_ids: ["entity-lira", "entity-ashen"],
  },
];

let panels: StoryboardPanel[] = panelData.map((data, index) => ({
  id: `panel-${index + 1}`,
  scene_id: "scene-crossing",
  ordinal: index + 1,
  ...data,
  location_entity_id: "entity-gate",
  referenced_asset_ids: [],
  image_prompt: `Monochrome production storyboard panel ${index + 1}: ${data.visual_description}`,
  negative_prompt: "photorealistic, illegible composition, text artifacts",
  render_status: "rendered",
  status: index + 1 === 2 || index + 1 === 5 ? "review" : "approved",
}));

let renders: RenderVersion[] = panels.map((panel) => ({
  id: `render-${panel.id}-v1`,
  panel_id: panel.id,
  version: 1,
  output_path: `demo/panel-${String(panel.ordinal).padStart(4, "0")}.png`,
  width: 960,
  height: 640,
  seed: 1000 + panel.ordinal,
  provider: "placeholder",
  metadata: { demo: true },
  status: "draft",
  created_at: NOW,
}));

const jobs: Job[] = [
  makeJob("job-canon", "canon_extract"),
  makeJob("job-adapt", "episode_adapt"),
  makeJob("job-storyboard", "storyboard_build"),
  makeJob("job-render", "image_render", 6, 6),
];

export async function demoRequest(path: string, init: RequestInit = {}): Promise<unknown> {
  const method = (init.method ?? "GET").toUpperCase();
  const body = typeof init.body === "string" ? JSON.parse(init.body) as Record<string, unknown> : {};

  if (path === "/projects" && method === "GET") return clone([project]);
  if (path === "/projects" && method === "POST") return clone(project);
  if (path === `/projects/${PROJECT_ID}`) return clone(project);
  if (path === `/projects/${PROJECT_ID}/sources` && method === "GET") return clone(documents);
  if (path === `/projects/${PROJECT_ID}/sources` && method === "POST") {
    return clone({ document: documents[0], chunks } satisfies SourceIngestionResult);
  }
  if (path === `/projects/${PROJECT_ID}/chunks`) return clone(chunks);
  if (path === `/projects/${PROJECT_ID}/entities`) return clone(entities);
  if (path === `/projects/${PROJECT_ID}/facts`) return clone(facts);
  if (path === `/projects/${PROJECT_ID}/episodes`) return clone([episode]);
  if (path === `/projects/${PROJECT_ID}/jobs`) return clone(jobs);
  if (path === `/projects/${PROJECT_ID}/canon/extract`) {
    return clone({ job: jobs[0], result: { entities, facts } });
  }
  if (path === `/projects/${PROJECT_ID}/episodes/adapt`) {
    return clone({ job: jobs[1], result: episodeDetail } satisfies JobRunResult<EpisodeDetail>);
  }
  if (path === `/episodes/${episode.id}`) return clone(episodeDetail);

  if (path === "/scenes/scene-shard/storyboard" && method === "GET") return [];
  if (path === "/scenes/scene-shard/storyboard" && method === "POST") return clone({ job: jobs[2], result: [] });
  if (path === "/scenes/scene-crossing/storyboard" && method === "GET") return clone(panels);
  if (path === "/scenes/scene-crossing/storyboard" && method === "POST") {
    return clone({ job: jobs[2], result: panels } satisfies JobRunResult<StoryboardPanel[]>);
  }

  const panelStatusMatch = path.match(/^\/panels\/(panel-\d+)\/status$/);
  if (panelStatusMatch && method === "PATCH") {
    const panelId = panelStatusMatch[1]!;
    const status = body.status as ProductionStatus;
    panels = panels.map((panel) => panel.id === panelId ? { ...panel, status } : panel);
    return clone(panels.find((panel) => panel.id === panelId));
  }

  const panelRendersMatch = path.match(/^\/panels\/(panel-\d+)\/renders$/);
  if (panelRendersMatch) {
    return clone(renders.filter((render) => render.panel_id === panelRendersMatch[1]));
  }

  const renderPanelMatch = path.match(/^\/panels\/(panel-\d+)\/render$/);
  if (renderPanelMatch && method === "POST") {
    const render = addRender(renderPanelMatch[1]!);
    return clone({ job: makeJob(`job-${render.id}`, "image_render"), result: render } satisfies JobRunResult<RenderVersion>);
  }

  if (path === "/scenes/scene-crossing/render" && method === "POST") {
    const generated = panels.map((panel) => addRender(panel.id));
    return clone({ job: makeJob("job-scene-render", "image_render", 6, 6), result: generated } satisfies JobRunResult<RenderVersion[]>);
  }

  const renderStatusMatch = path.match(/^\/renders\/(render-panel-\d+-v\d+)\/status$/);
  if (renderStatusMatch && method === "PATCH") {
    const renderId = renderStatusMatch[1]!;
    renders = renders.map((render) => render.id === renderId ? { ...render, status: body.status as ProductionStatus } : render);
    return clone(renders.find((render) => render.id === renderId));
  }

  throw new Error(`Demo route is not implemented: ${method} ${path}`);
}

export function demoRenderUrl(renderId: string): string {
  const match = renderId.match(/^render-panel-(\d+)-v\d+$/);
  return match ? `/demo/panel-${match[1]!.padStart(4, "0")}.png` : "/demo/panel-0001.png";
}

function addRender(panelId: string): RenderVersion {
  const panel = panels.find((item) => item.id === panelId);
  if (!panel) throw new Error("Panel not found.");
  const version = renders.filter((render) => render.panel_id === panelId).length + 1;
  const render: RenderVersion = {
    id: `render-${panelId}-v${version}`,
    panel_id: panelId,
    version,
    output_path: `demo/panel-${String(panel.ordinal).padStart(4, "0")}.png`,
    width: 960,
    height: 640,
    seed: 1000 + panel.ordinal + version,
    provider: "placeholder",
    metadata: { demo: true },
    status: "draft",
    created_at: NOW,
  };
  renders = [...renders, render];
  return render;
}

function makeJob(
  id: string,
  kind: Job["kind"],
  progressCurrent = 1,
  progressTotal = 1,
): Job {
  return {
    id,
    project_id: PROJECT_ID,
    kind,
    status: "succeeded",
    progress_current: progressCurrent,
    progress_total: progressTotal,
    error: null,
    created_at: NOW,
    updated_at: NOW,
  };
}

function clone<T>(value: T): T {
  return structuredClone(value);
}
