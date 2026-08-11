import { useEffect, useRef, useState } from "react";
import { FilePlus2, Search, Sparkles, Upload } from "lucide-react";

import { ActionButton } from "../../components/ActionButton";
import { EmptyState } from "../../components/EmptyState";
import { ApiError, api } from "../../lib/api";
import type { SourceChunk, SourceDocument } from "../../lib/types";

export function SourceWorkspace({ projectId }: { projectId: string }) {
  const fileRef = useRef<HTMLInputElement>(null);
  const [documents, setDocuments] = useState<SourceDocument[]>([]);
  const [chunks, setChunks] = useState<SourceChunk[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    const [loadedDocuments, loadedChunks] = await Promise.all([
      api.listSources(projectId),
      api.listChunks(projectId),
    ]);
    setDocuments(loadedDocuments);
    setChunks(loadedChunks);
    setSelectedId((current) => current ?? loadedChunks[0]?.id ?? null);
  };

  useEffect(() => { void refresh().catch((reason) => setError(toMessage(reason))); }, [projectId]);

  const upload = async (file: File) => {
    setBusy("upload"); setError(null); setMessage(null);
    try {
      const result = await api.uploadSource(projectId, file);
      await refresh();
      setSelectedId(result.chunks[0]?.id ?? null);
      setMessage(`${result.document.filename} imported as ${result.chunks.length} chunks.`);
    } catch (reason) { setError(toMessage(reason)); }
    finally { setBusy(null); if (fileRef.current) fileRef.current.value = ""; }
  };

  const extract = async () => {
    if (!chunks.length) return;
    setBusy("extract"); setError(null); setMessage(null);
    try {
      const result = await api.extractCanon(projectId);
      setMessage(`Canon extraction ${result.job.status}: ${chunks.length} chunks processed.`);
    } catch (reason) { setError(toMessage(reason)); }
    finally { setBusy(null); }
  };

  const filtered = chunks.filter((chunk) =>
    `${chunk.heading ?? ""} ${chunk.text}`.toLowerCase().includes(query.toLowerCase()),
  );
  const selected = chunks.find((chunk) => chunk.id === selectedId) ?? filtered[0] ?? null;

  return (
    <section className="standard-workspace source-workspace">
      <header className="workspace-title workspace-title--row">
        <div><span>Evidence-preserving ingestion</span><h1>Source</h1><p>Import TXT or Markdown, inspect sections, then extract canon.</p></div>
        <div className="workspace-actions">
          <input ref={fileRef} className="visually-hidden" type="file" accept=".txt,.md,text/plain,text/markdown" onChange={(event) => { const file = event.target.files?.[0]; if (file) void upload(file); }} />
          <ActionButton onClick={() => fileRef.current?.click()} disabled={Boolean(busy)}><Upload size={16} /> {busy === "upload" ? "Importing…" : "Import source"}</ActionButton>
          <ActionButton tone="primary" onClick={extract} disabled={!chunks.length || Boolean(busy)}><Sparkles size={16} /> {busy === "extract" ? "Extracting…" : "Extract canon"}</ActionButton>
        </div>
      </header>
      {message ? <div className="inline-message">{message}</div> : null}
      {error ? <div className="inline-message inline-message--error">{error}</div> : null}
      {!documents.length ? (
        <EmptyState title="No source material" detail="Import an original or public-domain TXT or Markdown story." />
      ) : (
        <div className="source-layout">
          <aside className="source-list">
            <div className="source-document"><FilePlus2 size={16} /><div><strong>{documents[0]?.filename}</strong><span>{chunks.length} chunks</span></div></div>
            <label className="search-field"><Search size={15} /><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search chunks" /></label>
            <div className="chunk-list">
              {filtered.map((chunk) => <button className={selected?.id === chunk.id ? "is-active" : ""} type="button" key={chunk.id} onClick={() => setSelectedId(chunk.id)}><span>{String(chunk.ordinal).padStart(2, "0")}</span><div><strong>{chunk.heading || `Chunk ${chunk.ordinal}`}</strong><p>{chunk.text.slice(0, 88)}</p></div></button>)}
            </div>
          </aside>
          <article className="source-preview">
            {selected ? <><div className="preview-heading"><span>Chunk {selected.ordinal}</span><strong>Offsets {selected.start_offset}–{selected.end_offset}</strong></div><h2>{selected.heading || `Chunk ${selected.ordinal}`}</h2><pre>{selected.text}</pre></> : null}
          </article>
        </div>
      )}
    </section>
  );
}

function toMessage(error: unknown): string {
  return error instanceof ApiError ? error.detail : error instanceof Error ? error.message : "Request failed.";
}
