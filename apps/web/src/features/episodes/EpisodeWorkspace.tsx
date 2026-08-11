import { useEffect, useMemo, useState } from "react";
import {
  ArrowLeft,
  BookOpenCheck,
  Check,
  ChevronRight,
  Clapperboard,
  Layers3,
  Sparkles,
} from "lucide-react";

import { ActionButton } from "../../components/ActionButton";
import { EmptyState } from "../../components/EmptyState";
import { StatusPill } from "../../components/StatusPill";
import { ApiError, api } from "../../lib/api";
import type { Episode, EpisodeDetail, SourceChunk, TargetFormat } from "../../lib/types";
import { StoryboardDesk } from "../storyboard/StoryboardDesk";

interface EpisodeWorkspaceProps {
  projectId: string;
  projectName: string;
  targetFormat: TargetFormat;
}

export function EpisodeWorkspace({
  projectId,
  projectName,
  targetFormat,
}: EpisodeWorkspaceProps) {
  const [chunks, setChunks] = useState<SourceChunk[]>([]);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [details, setDetails] = useState<Record<string, EpisodeDetail>>({});
  const [panelCounts, setPanelCounts] = useState<Record<string, number>>({});
  const [selectedChunks, setSelectedChunks] = useState<Set<string>>(new Set());
  const [selectedEpisodeId, setSelectedEpisodeId] = useState<string | null>(null);
  const [openSceneId, setOpenSceneId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    Promise.all([api.listChunks(projectId), api.listEpisodes(projectId)])
      .then(async ([loadedChunks, loadedEpisodes]) => {
        const loadedDetails = await Promise.all(
          loadedEpisodes.map((episode) => api.getEpisode(episode.id)),
        );
        const scenePanels = await Promise.all(
          loadedDetails.flatMap((detail) =>
            detail.scenes.map(async (scene) => [scene.id, await api.getStoryboard(scene.id)] as const),
          ),
        );
        if (!active) return;
        setChunks(loadedChunks);
        setEpisodes(loadedEpisodes);
        setDetails(Object.fromEntries(loadedDetails.map((detail) => [detail.episode.id, detail])));
        setPanelCounts(Object.fromEntries(scenePanels.map(([id, panels]) => [id, panels.length])));
        setSelectedEpisodeId(loadedEpisodes.at(-1)?.id ?? null);
      })
      .catch((reason) => active && setError(toMessage(reason)))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [projectId]);

  const selectedDetail = selectedEpisodeId ? details[selectedEpisodeId] ?? null : null;
  const nextEpisodeNumber = useMemo(
    () => Math.max(0, ...episodes.map((episode) => episode.number)) + 1,
    [episodes],
  );

  const toggleChunk = (chunkId: string) => {
    setSelectedChunks((current) => {
      const next = new Set(current);
      if (next.has(chunkId)) next.delete(chunkId);
      else next.add(chunkId);
      return next;
    });
  };

  const adapt = async () => {
    if (!selectedChunks.size || busy) return;
    setBusy("adapt");
    setError(null);
    setMessage(null);
    try {
      const result = await api.adaptEpisode(projectId, {
        source_chunk_ids: chunks
          .filter((chunk) => selectedChunks.has(chunk.id))
          .map((chunk) => chunk.id),
        number: nextEpisodeNumber,
        target_format: targetFormat,
      });
      const detail = result.result;
      setEpisodes((current) => [...current, detail.episode]);
      setDetails((current) => ({ ...current, [detail.episode.id]: detail }));
      setSelectedEpisodeId(detail.episode.id);
      setMessage(`Episode ${detail.episode.number} adapted into ${detail.scenes.length} scenes.`);
    } catch (reason) {
      setError(toMessage(reason));
    } finally {
      setBusy(null);
    }
  };

  const buildStoryboard = async (sceneId: string) => {
    if (busy) return;
    setBusy(`storyboard-${sceneId}`);
    setError(null);
    try {
      const result = await api.buildStoryboard(sceneId);
      setPanelCounts((current) => ({ ...current, [sceneId]: result.result.length }));
      setOpenSceneId(sceneId);
    } catch (reason) {
      setError(toMessage(reason));
    } finally {
      setBusy(null);
    }
  };

  if (openSceneId && selectedDetail) {
    return (
      <div className="episode-storyboard-shell">
        <button className="back-link" type="button" onClick={() => setOpenSceneId(null)}>
          <ArrowLeft size={16} /> Back to episode
        </button>
        <StoryboardDesk
          projectId={projectId}
          episodeId={selectedDetail.episode.id}
          sceneId={openSceneId}
          projectName={projectName}
        />
      </div>
    );
  }

  if (loading) return <div className="desk-state">Loading episodes…</div>;

  return (
    <section className="standard-workspace episode-workspace">
      <header className="workspace-title workspace-title--row">
        <div>
          <span>Visual adaptation</span>
          <h1>Episodes</h1>
          <p>Select source chapters, preserve causal order, and turn prose into reviewable scenes.</p>
        </div>
        <ActionButton
          tone="primary"
          onClick={adapt}
          disabled={!selectedChunks.size || Boolean(busy)}
        >
          <Sparkles size={16} /> {busy === "adapt" ? "Adapting…" : "Adapt episode"}
        </ActionButton>
      </header>

      {message ? <div className="inline-message">{message}</div> : null}
      {error ? <div className="inline-message inline-message--error">{error}</div> : null}

      {!chunks.length ? (
        <EmptyState title="No source chunks" detail="Import a TXT or Markdown story before adapting an episode." />
      ) : (
        <div className="episode-layout">
          <aside className="episode-source-picker">
            <div className="picker-heading">
              <div><Layers3 size={17} /><strong>Source selection</strong></div>
              <span>{selectedChunks.size} selected</span>
            </div>
            <div className="episode-chunk-list">
              {chunks.map((chunk) => (
                <label key={chunk.id}>
                  <input
                    type="checkbox"
                    aria-label={chunk.heading || `Chunk ${chunk.ordinal}`}
                    checked={selectedChunks.has(chunk.id)}
                    onChange={() => toggleChunk(chunk.id)}
                  />
                  <span className="custom-checkbox"><Check size={12} /></span>
                  <div>
                    <strong>{chunk.heading || `Chunk ${chunk.ordinal}`}</strong>
                    <p>{chunk.text.slice(0, 96)}</p>
                  </div>
                </label>
              ))}
            </div>
          </aside>

          <div className="episode-production">
            {!episodes.length ? (
              <EmptyState title="No episodes yet" detail="Select one or more source chunks and adapt episode one." />
            ) : (
              <>
                <div className="episode-switcher" aria-label="Episodes">
                  {episodes.map((episode) => (
                    <button
                      type="button"
                      className={episode.id === selectedEpisodeId ? "is-active" : ""}
                      key={episode.id}
                      onClick={() => setSelectedEpisodeId(episode.id)}
                    >
                      <span>EP {String(episode.number).padStart(2, "0")}</span>
                      <strong>{episode.title}</strong>
                      <StatusPill status={episode.status} />
                    </button>
                  ))}
                </div>
                {selectedDetail ? (
                  <article className="episode-detail">
                    <div className="episode-detail__intro">
                      <span>Episode {selectedDetail.episode.number}</span>
                      <h2>{selectedDetail.episode.title}</h2>
                      <p>{selectedDetail.episode.logline}</p>
                      <div><BookOpenCheck size={15} /> {selectedDetail.episode.adaptation_notes}</div>
                    </div>
                    <div className="scene-list">
                      {selectedDetail.scenes.map((scene) => {
                        const count = panelCounts[scene.id] ?? 0;
                        return (
                          <article key={scene.id}>
                            <div className="scene-number">{String(scene.ordinal).padStart(2, "0")}</div>
                            <div className="scene-copy">
                              <div><h3>{scene.title}</h3><StatusPill status={scene.status} /></div>
                              <p>{scene.summary}</p>
                              <span>{scene.purpose}</span>
                            </div>
                            {count ? (
                              <ActionButton onClick={() => setOpenSceneId(scene.id)}>
                                Open storyboard · {count} <ChevronRight size={15} />
                              </ActionButton>
                            ) : (
                              <ActionButton
                                onClick={() => void buildStoryboard(scene.id)}
                                disabled={Boolean(busy)}
                              >
                                <Clapperboard size={15} />
                                {busy === `storyboard-${scene.id}` ? "Building…" : "Build storyboard"}
                              </ActionButton>
                            )}
                          </article>
                        );
                      })}
                    </div>
                  </article>
                ) : null}
              </>
            )}
          </div>
        </div>
      )}
    </section>
  );
}

function toMessage(error: unknown): string {
  if (error instanceof ApiError) return error.detail;
  if (error instanceof Error) return error.message;
  return "Request failed.";
}
