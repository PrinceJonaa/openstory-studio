import { useEffect, useState } from "react";
import { ImageIcon, Layers3 } from "lucide-react";

import { EmptyState } from "../../components/EmptyState";
import { StatusPill } from "../../components/StatusPill";
import { api } from "../../lib/api";
import type { RenderVersion } from "../../lib/types";

interface RenderAsset {
  render: RenderVersion;
  episodeNumber: number;
  episodeTitle: string;
  sceneOrdinal: number;
  sceneTitle: string;
  panelOrdinal: number;
  action: string;
}

export function AssetsWorkspace({ projectId }: { projectId: string }) {
  const [assets, setAssets] = useState<RenderAsset[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    api.listEpisodes(projectId)
      .then(async (episodes) => {
        const details = await Promise.all(episodes.map((episode) => api.getEpisode(episode.id)));
        const sceneRecords = await Promise.all(
          details.flatMap((detail) =>
            detail.scenes.map(async (scene) => ({
              detail,
              scene,
              panels: await api.getStoryboard(scene.id),
            })),
          ),
        );
        const panelRecords = await Promise.all(
          sceneRecords.flatMap(({ detail, scene, panels }) =>
            panels.map(async (panel) => ({
              detail,
              scene,
              panel,
              renders: await api.listPanelRenders(panel.id),
            })),
          ),
        );
        if (!active) return;
        setAssets(
          panelRecords.flatMap(({ detail, scene, panel, renders }) =>
            renders.map((render) => ({
              render,
              episodeNumber: detail.episode.number,
              episodeTitle: detail.episode.title,
              sceneOrdinal: scene.ordinal,
              sceneTitle: scene.title,
              panelOrdinal: panel.ordinal,
              action: panel.action,
            })),
          ),
        );
      })
      .catch((reason: unknown) => {
        if (active) setError(reason instanceof Error ? reason.message : "Unable to load assets.");
      })
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [projectId]);

  if (loading) return <div className="desk-state">Loading production assets…</div>;

  return (
    <section className="standard-workspace assets-workspace">
      <header className="workspace-title">
        <span>Versioned production output</span>
        <h1>Assets</h1>
        <p>Every regeneration creates another addressable version. Approved work is never overwritten.</p>
      </header>
      {error ? <div className="inline-message inline-message--error">{error}</div> : null}
      {!assets.length ? (
        <EmptyState title="No rendered assets" detail="Render storyboard placeholders to create the first production versions." />
      ) : (
        <div className="asset-grid">
          {assets.map((asset) => (
            <article className="asset-card" key={asset.render.id}>
              <div className="asset-image">
                <img
                  src={api.getRenderFileUrl(asset.render.id)}
                  alt={`Episode ${asset.episodeNumber}, scene ${asset.sceneOrdinal}, panel ${asset.panelOrdinal}`}
                />
                <span>v{String(asset.render.version).padStart(3, "0")}</span>
              </div>
              <div className="asset-card__body">
                <div className="asset-card__eyebrow">
                  <span><ImageIcon size={13} /> Panel {asset.panelOrdinal}</span>
                  <StatusPill status={asset.render.status} />
                </div>
                <h2>{asset.sceneTitle}</h2>
                <p>{asset.action}</p>
                <footer>
                  <span><Layers3 size={13} /> Episode {asset.episodeNumber} · {asset.episodeTitle}</span>
                  <strong>{asset.render.provider}</strong>
                </footer>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
