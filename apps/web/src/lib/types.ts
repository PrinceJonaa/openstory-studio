export type TargetFormat = "storyboard" | "comic" | "webtoon" | "anime" | "film";
export type ProductionStatus = "draft" | "review" | "approved" | "locked" | "revise";
export type RenderStatus = "unrendered" | "queued" | "rendered" | "failed";

export interface Project {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  target_format: TargetFormat;
  created_at: string;
  updated_at: string;
}

export interface SourceDocument {
  id: string;
  project_id: string;
  filename: string;
  media_type: string;
  sha256: string;
  workspace_path: string;
}

export interface SourceChunk {
  id: string;
  document_id: string;
  ordinal: number;
  heading: string | null;
  text: string;
  start_offset: number;
  end_offset: number;
}

export interface SourceIngestionResult {
  document: SourceDocument;
  chunks: SourceChunk[];
}

export type EntityKind = "character" | "location" | "object" | "faction" | "creature" | "concept";

export interface CanonEntity {
  id: string;
  project_id: string;
  kind: EntityKind;
  canonical_name: string;
  aliases: string[];
  summary: string;
  attributes: Record<string, unknown>;
}

export interface CanonFact {
  id: string;
  project_id: string;
  subject_entity_id: string;
  predicate: string;
  object_entity_id: string | null;
  value: unknown;
  valid_from_ordinal: number | null;
  valid_to_ordinal: number | null;
  source_chunk_id: string;
  evidence: string;
  confidence: number;
}

export interface Episode {
  id: string;
  project_id: string;
  number: number;
  title: string;
  source_chunk_ids: string[];
  logline: string;
  adaptation_notes: string;
  status: ProductionStatus;
}

export interface Scene {
  id: string;
  episode_id: string;
  ordinal: number;
  title: string;
  purpose: string;
  location_entity_id: string | null;
  character_entity_ids: string[];
  summary: string;
  status: ProductionStatus;
}

export interface EpisodeDetail {
  episode: Episode;
  scenes: Scene[];
}

export interface DialogueLine {
  speaker_entity_id: string | null;
  speaker_name: string;
  text: string;
}

export interface StoryboardPanel {
  id: string;
  scene_id: string;
  ordinal: number;
  shot_type: string;
  framing: string;
  action: string;
  visual_description: string;
  dialogue: DialogueLine[];
  character_entity_ids: string[];
  location_entity_id: string | null;
  referenced_asset_ids: string[];
  image_prompt: string;
  negative_prompt: string | null;
  render_status: RenderStatus;
  status: ProductionStatus;
}

export interface RenderVersion {
  id: string;
  panel_id: string;
  version: number;
  output_path: string;
  width: number;
  height: number;
  seed: number | null;
  provider: string;
  metadata: Record<string, unknown>;
  status: ProductionStatus;
  created_at: string;
}

export interface Job {
  id: string;
  project_id: string;
  kind: "canon_extract" | "episode_adapt" | "storyboard_build" | "image_render" | "export";
  status: "queued" | "running" | "succeeded" | "failed";
  progress_current: number;
  progress_total: number | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

export interface JobRunResult<T> {
  job: Job;
  result: T;
}
