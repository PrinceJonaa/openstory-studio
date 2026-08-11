import { useEffect, useMemo, useState } from "react";
import { BookOpenText, Link2, MapPin, UserRound } from "lucide-react";

import { EmptyState } from "../../components/EmptyState";
import { api } from "../../lib/api";
import type { CanonEntity, CanonFact, SourceChunk } from "../../lib/types";

type CanonTab = "entities" | "facts";

export function CanonWorkspace({ projectId }: { projectId: string }) {
  const [tab, setTab] = useState<CanonTab>("entities");
  const [entities, setEntities] = useState<CanonEntity[]>([]);
  const [facts, setFacts] = useState<CanonFact[]>([]);
  const [chunks, setChunks] = useState<SourceChunk[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    Promise.all([api.listEntities(projectId), api.listFacts(projectId), api.listChunks(projectId)])
      .then(([loadedEntities, loadedFacts, loadedChunks]) => {
        if (!active) return;
        setEntities(loadedEntities); setFacts(loadedFacts); setChunks(loadedChunks);
        setSelectedId(loadedEntities[0]?.id ?? loadedFacts[0]?.id ?? null);
      })
      .finally(() => active && setLoading(false));
    return () => { active = false; };
  }, [projectId]);

  const entityById = useMemo(() => Object.fromEntries(entities.map((entity) => [entity.id, entity])), [entities]);
  const chunkById = useMemo(() => Object.fromEntries(chunks.map((chunk) => [chunk.id, chunk])), [chunks]);
  const selectedEntity = tab === "entities" ? entities.find((entity) => entity.id === selectedId) ?? entities[0] : null;
  const selectedFact = tab === "facts" ? facts.find((fact) => fact.id === selectedId) ?? facts[0] : null;
  const entityFacts = selectedEntity ? facts.filter((fact) => fact.subject_entity_id === selectedEntity.id || fact.object_entity_id === selectedEntity.id) : [];

  if (loading) return <div className="desk-state">Loading canon…</div>;
  if (!entities.length && !facts.length) return <section className="standard-workspace"><header className="workspace-title"><span>Temporal story graph</span><h1>Canon</h1></header><EmptyState title="Canon is empty" detail="Extract canon from the Source workspace first." /></section>;

  return (
    <section className="standard-workspace canon-workspace">
      <header className="workspace-title"><span>Temporal story graph</span><h1>Canon</h1><p>Every belief remains linked to the exact source evidence that supports it.</p></header>
      <div className="tab-bar" role="tablist"><button type="button" role="tab" aria-selected={tab === "entities"} onClick={() => { setTab("entities"); setSelectedId(entities[0]?.id ?? null); }}>Entities <span>{entities.length}</span></button><button type="button" role="tab" aria-selected={tab === "facts"} onClick={() => { setTab("facts"); setSelectedId(facts[0]?.id ?? null); }}>Facts <span>{facts.length}</span></button></div>
      <div className="canon-layout">
        <div className="canon-list">
          {tab === "entities" ? entities.map((entity) => <button type="button" className={selectedEntity?.id === entity.id ? "is-active" : ""} key={entity.id} onClick={() => setSelectedId(entity.id)}>{entity.kind === "character" ? <UserRound size={17} /> : entity.kind === "location" ? <MapPin size={17} /> : <BookOpenText size={17} />}<div><strong>{entity.canonical_name}</strong><span>{entity.kind} · {facts.filter((fact) => fact.subject_entity_id === entity.id || fact.object_entity_id === entity.id).length} facts</span></div></button>) : facts.map((fact) => <button type="button" className={selectedFact?.id === fact.id ? "is-active" : ""} key={fact.id} onClick={() => setSelectedId(fact.id)}><Link2 size={17} /><div><strong>{entityById[fact.subject_entity_id]?.canonical_name ?? "Unknown"} · {fact.predicate}</strong><span>{Math.round(fact.confidence * 100)}% confidence</span></div></button>)}
        </div>
        <article className="canon-detail">
          {selectedEntity ? <><span className="eyebrow">{selectedEntity.kind}</span><h2>{selectedEntity.canonical_name}</h2><p>{selectedEntity.summary || "No summary recorded."}</p>{selectedEntity.aliases.length ? <div className="detail-block"><strong>Aliases</strong><p>{selectedEntity.aliases.join(", ")}</p></div> : null}<h3>Provenance</h3>{entityFacts.map((fact) => <FactEvidence fact={fact} entities={entityById} chunk={chunkById[fact.source_chunk_id]} key={fact.id} />)}</> : null}
          {selectedFact ? <><span className="eyebrow">Canon fact</span><h2>{entityById[selectedFact.subject_entity_id]?.canonical_name ?? "Unknown"} · {selectedFact.predicate}</h2><FactEvidence fact={selectedFact} entities={entityById} chunk={chunkById[selectedFact.source_chunk_id]} /><div className="detail-block"><strong>Temporal validity</strong><p>{selectedFact.valid_from_ordinal ?? "Beginning"} → {selectedFact.valid_to_ordinal ?? "Open-ended"}</p></div></> : null}
        </article>
      </div>
    </section>
  );
}

function FactEvidence({ fact, entities, chunk }: { fact: CanonFact; entities: Record<string, CanonEntity>; chunk?: SourceChunk }) {
  const object = fact.object_entity_id ? entities[fact.object_entity_id]?.canonical_name : JSON.stringify(fact.value);
  return <div className="fact-evidence"><div><strong>{fact.predicate}</strong><span>{object}</span></div><blockquote>{fact.evidence}</blockquote><footer><span>{chunk?.heading ?? `Chunk ${chunk?.ordinal ?? "—"}`}</span><span>Offsets {chunk?.start_offset ?? "—"}–{chunk?.end_offset ?? "—"}</span><span>{Math.round(fact.confidence * 100)}%</span></footer></div>;
}
