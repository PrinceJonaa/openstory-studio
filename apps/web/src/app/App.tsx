import { FormEvent, useEffect, useState } from "react";
import { BookMarked, Database, HardDrive, ShieldCheck, Sparkles } from "lucide-react";

import { ActionButton } from "../components/ActionButton";
import { AppNav } from "../components/AppNav";
import { AssetsWorkspace } from "../features/assets/AssetsWorkspace";
import { CanonWorkspace } from "../features/canon/CanonWorkspace";
import { EpisodeWorkspace } from "../features/episodes/EpisodeWorkspace";
import { JobsWorkspace } from "../features/jobs/JobsWorkspace";
import { ProjectOverview } from "../features/projects/ProjectOverview";
import { SourceWorkspace } from "../features/source/SourceWorkspace";
import { ApiError, api } from "../lib/api";
import type { Project, TargetFormat } from "../lib/types";
import type { AppRoute } from "./routes";

const LAST_PROJECT_KEY = "openstory:last-project";

export function App() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [route, setRoute] = useState<AppRoute>("overview");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api.listProjects()
      .then((loaded) => {
        if (!active) return;
        setProjects(loaded);
        const remembered = localStorage.getItem(LAST_PROJECT_KEY);
        const selected = loaded.find((project) => project.id === remembered) ?? loaded[0] ?? null;
        setSelectedProjectId(selected?.id ?? null);
      })
      .catch((reason: unknown) => active && setError(toMessage(reason)))
      .finally(() => active && setLoading(false));
    return () => {
      active = false;
    };
  }, []);

  const selectProject = (projectId: string) => {
    setSelectedProjectId(projectId);
    setRoute("overview");
    localStorage.setItem(LAST_PROJECT_KEY, projectId);
  };

  const project = projects.find((item) => item.id === selectedProjectId) ?? null;

  const addProject = (created: Project) => {
    setProjects((current) => [...current, created]);
    selectProject(created.id);
  };

  if (loading) return <div className="app-loading"><BookMarked size={28} /><span>Opening OpenStory Studio…</span></div>;

  if (!project) {
    return <CreateProjectScreen onCreated={addProject} initialError={error} />;
  }

  return (
    <div className="app-shell">
      <AppNav active={route} onChange={setRoute} />
      <div className="app-frame">
        <header className="app-topbar">
          <label>
            <span>Project</span>
            <select value={project.id} onChange={(event) => selectProject(event.target.value)}>
              {projects.map((item) => <option value={item.id} key={item.id}>{item.name}</option>)}
            </select>
          </label>
          <div className="local-state"><HardDrive size={15} /><span>Local workspace</span><i /></div>
        </header>
        <main className="app-main">
          {route === "overview" ? <ProjectOverview project={project} onNavigate={setRoute} /> : null}
          {route === "source" ? <SourceWorkspace projectId={project.id} /> : null}
          {route === "canon" ? <CanonWorkspace projectId={project.id} /> : null}
          {route === "episodes" ? (
            <EpisodeWorkspace
              projectId={project.id}
              projectName={project.name}
              targetFormat={project.target_format}
            />
          ) : null}
          {route === "assets" ? <AssetsWorkspace projectId={project.id} /> : null}
          {route === "jobs" ? <JobsWorkspace projectId={project.id} /> : null}
        </main>
      </div>
    </div>
  );
}

function CreateProjectScreen({
  onCreated,
  initialError,
}: {
  onCreated: (project: Project) => void;
  initialError: string | null;
}) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [targetFormat, setTargetFormat] = useState<TargetFormat>("storyboard");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(initialError);

  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!name.trim() || busy) return;
    setBusy(true);
    setError(null);
    try {
      const created = await api.createProject({
        name: name.trim(),
        description: description.trim(),
        target_format: targetFormat,
      });
      localStorage.setItem(LAST_PROJECT_KEY, created.id);
      onCreated(created);
    } catch (reason) {
      setError(toMessage(reason));
    } finally {
      setBusy(false);
    }
  };

  return (
    <main className="create-project-screen">
      <section className="create-project-story">
        <div className="create-brand"><BookMarked size={24} /><span>OpenStory Studio</span></div>
        <div>
          <span className="eyebrow">Local-first narrative production</span>
          <h2>Story state that outlives every model.</h2>
          <p>Move from source evidence to canon, episodes, scenes, storyboards, and approved assets in one durable workspace.</p>
        </div>
        <div className="create-principles">
          <span><Database size={17} /><strong>Persistent canon</strong></span>
          <span><ShieldCheck size={17} /><strong>Human approval</strong></span>
          <span><Sparkles size={17} /><strong>Replaceable providers</strong></span>
        </div>
      </section>
      <section className="create-project-form-wrap">
        <form className="create-project-form" onSubmit={(event) => void submit(event)}>
          <span>Start locally</span>
          <h1>Create your story workspace</h1>
          <p>The project folder, SQLite state, and generated assets stay under your control.</p>
          <label>
            <span>Project name</span>
            <input aria-label="Project name" value={name} onChange={(event) => setName(event.target.value)} placeholder="The Glass Orchard" required />
          </label>
          <label>
            <span>Description</span>
            <textarea aria-label="Description" value={description} onChange={(event) => setDescription(event.target.value)} placeholder="A concise production brief…" rows={3} />
          </label>
          <label>
            <span>First target format</span>
            <select value={targetFormat} onChange={(event) => setTargetFormat(event.target.value as TargetFormat)}>
              <option value="storyboard">Storyboard</option>
              <option value="comic">Comic</option>
              <option value="webtoon">Webtoon</option>
              <option value="anime">Anime</option>
              <option value="film">Film</option>
            </select>
          </label>
          {error ? <div className="inline-message inline-message--error">{error}</div> : null}
          <ActionButton tone="primary" type="submit" disabled={busy || !name.trim()}>
            {busy ? "Creating…" : "Create project"}
          </ActionButton>
        </form>
      </section>
    </main>
  );
}

function toMessage(error: unknown): string {
  if (error instanceof ApiError) return error.detail;
  if (error instanceof Error) return error.message;
  return "Request failed.";
}
