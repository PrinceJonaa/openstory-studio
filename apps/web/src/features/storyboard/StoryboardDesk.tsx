import { useEffect, useMemo, useState } from "react";
import {
  CheckCircle2,
  ChevronDown,
  ChevronRight,
  Film,
  ImageIcon,
  MapPin,
  MessageCircle,
  Sparkles,
  Users,
  WandSparkles,
  X,
} from "lucide-react";

import { ActionButton } from "../../components/ActionButton";
import { EmptyState } from "../../components/EmptyState";
import { StatusPill } from "../../components/StatusPill";
import { ApiError, api } from "../../lib/api";
import type {
  CanonEntity,
  CanonFact,
  EpisodeDetail,
  ProductionStatus,
  RenderVersion,
  SourceChunk,
  StoryboardPanel,
} from "../../lib/types";
import {
  ViewPreferences,
  loadViewSettings,
  type ViewSettings,
} from "./ViewPreferences";

interface StoryboardDeskProps {
  projectId: string;
  episodeId: string;
  sceneId: string;
  projectName?: string;
}

const NEXT_STATUSES: Partial<Record<ProductionStatus, ProductionStatus[]>> = {
  draft: ["review"],
  review: ["approved", "revise"],
  approved: ["locked", "revise"],
  revise: ["draft", "review"],
};

function readableError(error: unknown): string {
  if (error instanceof ApiError) return error.detail;
  if (error instanceof Error) return error.message;
  return "Something went wrong.";
}

export function StoryboardDesk({
  projectId,
  episodeId,
  sceneId,
  projectName = "Project",
}: StoryboardDeskProps) {
  const [episode, setEpisode] = useState<EpisodeDetail | null>(null);
  const [panels, setPanels] = useState<StoryboardPanel[]>([]);
  const [renders, setRenders] = useState<Record<string, RenderVersion[]>>({});
  const [entities, setEntities] = useState<CanonEntity[]>([]);
  const [facts, setFacts] = useState<CanonFact[]>([]);
  const [chunks, setChunks] = useState<SourceChunk[]>([]);
  const [selectedPanelId, setSelectedPanelId] = useState<string | null>(null);
  const [view, setView] = useState<ViewSettings>(() => loadViewSettings(projectId));
  const [evidenceOpen, setEvidenceOpen] = useState(true);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    Promise.all([
      api.getEpisode(episodeId),
      api.getStoryboard(sceneId),
      api.listEntities(projectId),
      api.listFacts(projectId),
      api.listChunks(projectId),
    ])
      .then(async ([episodeDetail, loadedPanels, loadedEntities, loadedFacts, loadedChunks]) => {
        const renderPairs = await Promise.all(
          loadedPanels.map(async (panel) => [panel.id, await api.listPanelRenders(panel.id)] as const),
        );
        if (!active) return;
        setEpisode(episodeDetail);
        setPanels(loadedPanels);
        setEntities(loadedEntities);
        setFacts(loadedFacts);
        setChunks(loadedChunks);
        setRenders(Object.fromEntries(renderPairs));
        setSelectedPanelId((current) => current ?? loadedPanels[0]?.id ?? null);
      })
      .catch((reason) => active && setError(readableError(reason)))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, [episodeId, projectId, sceneId]);

  const scene = episode?.scenes.find((item) => item.id === sceneId) ?? null;
  const selectedPanel = selectedPanelId
    ? panels.find((panel) => panel.id === selectedPanelId) ?? null
    : null;
  const entityById = useMemo(
    () => Object.fromEntries(entities.map((entity) => [entity.id, entity])),
    [entities],
  );
  const chunkById = useMemo(
    () => Object.fromEntries(chunks.map((chunk) => [chunk.id, chunk])),
    [chunks],
  );
  const reviewPanels = panels.filter((panel) => panel.status === "review");
  const unlockedPanels = panels.filter((panel) => panel.status !== "locked");

  const selectedEvidence = useMemo(() => {
    if (!selectedPanel) return [];
    const ids = new Set([
      ...selectedPanel.character_entity_ids,
      ...(selectedPanel.location_entity_id ? [selectedPanel.location_entity_id] : []),
    ]);
    return facts.filter(
      (fact) => ids.has(fact.subject_entity_id) || (fact.object_entity_id ? ids.has(fact.object_entity_id) : false),
    );
  }, [facts, selectedPanel]);

  const updatePanelLocally = (updated: StoryboardPanel) => {
    setPanels((current) => current.map((panel) => (panel.id === updated.id ? updated : panel)));
  };

  const batchApprove = async () => {
    if (!reviewPanels.length || busy) return;
    setBusy("approve");
    setError(null);
    const results = await Promise.allSettled(
      reviewPanels.map((panel) => api.updatePanelStatus(panel.id, "approved")),
    );
    const approved = results.flatMap((result) => (result.status === "fulfilled" ? [result.value] : []));
    approved.forEach(updatePanelLocally);
    const failed = results.length - approved.length;
    setNotice(`${approved.length} panel${approved.length === 1 ? "" : "s"} approved${failed ? `; ${failed} failed` : ""}.`);
    setBusy(null);
  };

  const batchRender = async () => {
    if (!unlockedPanels.length || busy) return;
    setBusy("batch-render");
    setError(null);
    const results = await Promise.allSettled(unlockedPanels.map((panel) => api.renderPanel(panel.id)));
    const successful = results.flatMap((result) => (result.status === "fulfilled" ? [result.value.result] : []));
    setRenders((current) => {
      const next = { ...current };
      successful.forEach((render) => {
        next[render.panel_id] = [...(next[render.panel_id] ?? []), render];
      });
      return next;
    });
    const renderedIds = new Set(successful.map((render) => render.panel_id));
    setPanels((current) => current.map((panel) => (
      renderedIds.has(panel.id) ? { ...panel, render_status: "rendered" } : panel
    )));
    const failed = results.length - successful.length;
    setNotice(`${successful.length} panel${successful.length === 1 ? "" : "s"} rendered${failed ? `; ${failed} failed` : ""}.`);
    setBusy(null);
  };

  const renderAll = async () => {
    if (busy) return;
    setBusy("render-all");
    setError(null);
    try {
      const result = await api.renderScene(sceneId);
      setRenders((current) => {
        const next = { ...current };
        result.result.forEach((render) => {
          next[render.panel_id] = [...(next[render.panel_id] ?? []), render];
        });
        return next;
      });
      const renderedIds = new Set(result.result.map((render) => render.panel_id));
      setPanels((current) => current.map((panel) => (
        renderedIds.has(panel.id) ? { ...panel, render_status: "rendered" } : panel
      )));
      setNotice(`${result.result.length} placeholders rendered.`);
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setBusy(null);
    }
  };

  const changeSelectedStatus = async (status: ProductionStatus) => {
    if (!selectedPanel || busy) return;
    setBusy(`status-${selectedPanel.id}`);
    setError(null);
    try {
      updatePanelLocally(await api.updatePanelStatus(selectedPanel.id, status));
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setBusy(null);
    }
  };

  const renderSelected = async () => {
    if (!selectedPanel || busy) return;
    setBusy(`render-${selectedPanel.id}`);
    setError(null);
    try {
      const result = await api.renderPanel(selectedPanel.id);
      setRenders((current) => ({
        ...current,
        [selectedPanel.id]: [...(current[selectedPanel.id] ?? []), result.result],
      }));
      updatePanelLocally({ ...selectedPanel, render_status: "rendered" });
      setNotice(`Panel ${selectedPanel.ordinal} rendered as version ${result.result.version}.`);
    } catch (reason) {
      setError(readableError(reason));
    } finally {
      setBusy(null);
    }
  };

  if (loading) {
    return <div className="desk-state">Loading storyboard desk…</div>;
  }
  if (error && !episode) {
    return <div className="desk-state desk-state--error">{error}</div>;
  }
  if (!episode || !scene) {
    return <div className="desk-state">Scene not found.</div>;
  }
  if (!panels.length) {
    return <EmptyState title="No storyboard yet" detail="Build this scene into visual panels to open the desk." />;
  }

  return (
    <section className={`storyboard-desk layout-${view.layout}`}>
      <div className="desk-breadcrumbs">
        <span>{projectName}</span><ChevronRight size={14} /><span>Episode {episode.episode.number}</span>
        <ChevronRight size={14} /><span>Scene {scene.ordinal} · {scene.title}</span>
      </div>
      <header className="desk-header">
        <div>
          <h1>Scene {scene.ordinal} · {scene.title}</h1>
          <div className="desk-meta">
            <span>{panels.length} panels</span><i />
            <span className="review-count">{reviewPanels.length} need review</span><i />
            <span>Version {Math.max(1, ...Object.values(renders).flat().map((render) => render.version))}</span>
          </div>
        </div>
        <div className="desk-actions">
          <ViewPreferences projectId={projectId} settings={view} onChange={setView} />
          <button className="toolbar-button toolbar-button--teal" type="button" onClick={batchApprove} disabled={!reviewPanels.length || Boolean(busy)}>
            <CheckCircle2 size={17} /> Batch approve ({reviewPanels.length})
          </button>
          <button className="toolbar-button" type="button" onClick={batchRender} disabled={!unlockedPanels.length || Boolean(busy)}>
            <Film size={17} /> Batch render ({unlockedPanels.length})
          </button>
          <ActionButton tone="primary" onClick={renderAll} disabled={Boolean(busy)}>
            <Sparkles size={17} /> {busy === "render-all" ? "Rendering…" : "Render all placeholders"}<ChevronDown size={15} />
          </ActionButton>
        </div>
      </header>

      {error ? <div className="inline-message inline-message--error">{error}</div> : null}
      {notice ? <div className="inline-message">{notice}</div> : null}

      <div className="desk-workspace">
        <div className="panel-grid" aria-label="Storyboard panels">
          {panels.map((panel) => {
            const panelRenders = renders[panel.id] ?? [];
            const latestRender = panelRenders.at(-1);
            const characterNames = panel.character_entity_ids.map((id) => entityById[id]?.canonical_name ?? "Unknown");
            const locationName = panel.location_entity_id ? entityById[panel.location_entity_id]?.canonical_name : null;
            return (
              <article
                className={`panel-card ${selectedPanel?.id === panel.id ? "is-selected" : ""}`}
                key={panel.id}
                data-testid="panel-card"
              >
                <button className="panel-card__select" type="button" aria-label={`Select panel ${panel.ordinal}`} onClick={() => setSelectedPanelId(panel.id)}>
                  <span className="panel-number">{panel.ordinal}</span>
                  {view.visibleFields.status ? <StatusPill status={panel.status} /> : null}
                  <div className="panel-image">
                    {latestRender ? (
                      <img src={api.getRenderFileUrl(latestRender.id)} alt={`Rendered storyboard panel ${panel.ordinal}`} />
                    ) : (
                      <EmptyState compact title="Unrendered panel" detail="Render a placeholder to preview framing." />
                    )}
                  </div>
                  <div className="panel-card__body">
                    {view.visibleFields.shotType ? <strong>{panel.shot_type}</strong> : null}
                    {view.visibleFields.action ? <p>{panel.action}</p> : null}
                    {view.visibleFields.dialogue && panel.dialogue.length ? <p className="panel-secondary"><MessageCircle size={13} /> {panel.dialogue.map((line) => `${line.speaker_name}: ${line.text}`).join(" · ")}</p> : null}
                    {view.visibleFields.characters && characterNames.length ? <p className="panel-secondary"><Users size={13} /> {characterNames.join(", ")}</p> : null}
                    {view.visibleFields.location && locationName ? <p className="panel-secondary"><MapPin size={13} /> {locationName}</p> : null}
                    {view.visibleFields.continuityFlags ? <span className="continuity-line">Continuity · clear</span> : null}
                  </div>
                </button>
              </article>
            );
          })}
        </div>

        {selectedPanel ? (
          <aside className="panel-inspector" aria-label={`Panel ${selectedPanel.ordinal} inspector`}>
            <div className="inspector-heading">
              <h2>Panel {selectedPanel.ordinal}</h2>
              <button type="button" aria-label="Close inspector" onClick={() => setSelectedPanelId(null)}><X size={19} /></button>
            </div>
            <InspectorRow icon={<ImageIcon size={15} />} label="Shot type" value={`${selectedPanel.shot_type} · ${selectedPanel.framing}`} />
            <InspectorRow icon={<WandSparkles size={15} />} label="Action" value={selectedPanel.action} />
            <InspectorRow icon={<MessageCircle size={15} />} label="Dialogue" value={selectedPanel.dialogue.length ? selectedPanel.dialogue.map((line) => `${line.speaker_name}: ${line.text}`).join(" · ") : "—"} />
            <InspectorRow icon={<Users size={15} />} label="Characters" value={selectedPanel.character_entity_ids.map((id) => entityById[id]?.canonical_name ?? "Unknown").join(", ") || "—"} />
            <InspectorRow icon={<MapPin size={15} />} label="Location" value={selectedPanel.location_entity_id ? entityById[selectedPanel.location_entity_id]?.canonical_name ?? "Unknown" : "Unspecified"} />
            <div className="inspector-row inspector-row--stacked">
              <span>Approval</span>
              <select value={selectedPanel.status} onChange={(event) => void changeSelectedStatus(event.target.value as ProductionStatus)} disabled={!NEXT_STATUSES[selectedPanel.status]?.length || Boolean(busy)} aria-label="Panel approval status">
                <option value={selectedPanel.status}>{selectedPanel.status}</option>
                {(NEXT_STATUSES[selectedPanel.status] ?? []).map((status) => <option key={status} value={status}>{status}</option>)}
              </select>
            </div>
            <ActionButton className="inspector-render" onClick={() => void renderSelected()} disabled={Boolean(busy)}>
              <Sparkles size={16} /> {busy === `render-${selectedPanel.id}` ? "Rendering…" : selectedPanel.render_status === "rendered" ? "Regenerate" : "Render"}
            </ActionButton>

            <section className="evidence-card">
              <button className="evidence-card__toggle" type="button" aria-expanded={evidenceOpen} onClick={() => setEvidenceOpen((value) => !value)}>
                <span>Source evidence</span><ChevronDown size={17} />
              </button>
              {evidenceOpen ? (
                <div className="evidence-list">
                  {selectedEvidence.length ? selectedEvidence.slice(0, 3).map((fact) => {
                    const chunk = chunkById[fact.source_chunk_id];
                    return <div className="evidence-item" key={fact.id}><strong>{chunk?.heading ?? `Chunk ${chunk?.ordinal ?? "—"}`}</strong><p>{fact.evidence}</p><span>{Math.round(fact.confidence * 100)}% confidence · offsets {chunk?.start_offset ?? "—"}–{chunk?.end_offset ?? "—"}</span></div>;
                  }) : <p className="evidence-empty">No directly linked canon evidence for this panel.</p>}
                </div>
              ) : null}
            </section>
          </aside>
        ) : null}
      </div>

      <div className="suggested-next">
        <span className="suggested-next__icon"><Sparkles size={18} /></span>
        <div><strong>Suggested next</strong><span>Review the {reviewPanels.length} unapproved panels.</span></div>
        <ActionButton tone="quiet" onClick={() => setSelectedPanelId(reviewPanels[0]?.id ?? panels[0]?.id ?? null)}>Review unapproved ({reviewPanels.length}) <ChevronRight size={16} /></ActionButton>
      </div>
      <div className="desk-batchbar">
        <div><span>{panels.length} selected</span><span>{reviewPanels.length} need review</span></div>
        <section>
          <button aria-label={`Batch approve selected panels (${reviewPanels.length})`} type="button" onClick={() => void batchApprove()} disabled={!reviewPanels.length || Boolean(busy)}><CheckCircle2 size={15} /> Batch approve ({reviewPanels.length})</button>
          <button aria-label={`Batch render selected panels (${unlockedPanels.length})`} type="button" onClick={() => void batchRender()} disabled={!unlockedPanels.length || Boolean(busy)}><Film size={15} /> Batch render ({unlockedPanels.length})</button>
        </section>
      </div>
    </section>
  );
}

function InspectorRow({ icon, label, value }: { icon: React.ReactNode; label: string; value: string }) {
  return <div className="inspector-row"><span>{label}</span><div>{icon}<p>{value}</p></div></div>;
}
