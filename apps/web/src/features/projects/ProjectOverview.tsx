import { useEffect, useState } from "react";
import { ArrowRight, BookOpenText, Clapperboard, FileText, ListChecks } from "lucide-react";

import { ActionButton } from "../../components/ActionButton";
import { api } from "../../lib/api";
import type { Project } from "../../lib/types";
import type { AppRoute } from "../../app/routes";

interface ProjectOverviewProps {
  project: Project;
  onNavigate: (route: AppRoute) => void;
}

export function ProjectOverview({ project, onNavigate }: ProjectOverviewProps) {
  const [counts, setCounts] = useState({ sources: 0, entities: 0, episodes: 0, jobs: 0 });

  useEffect(() => {
    let active = true;
    Promise.all([
      api.listSources(project.id),
      api.listEntities(project.id),
      api.listEpisodes(project.id),
      api.listJobs(project.id),
    ]).then(([sources, entities, episodes, jobs]) => {
      if (active) setCounts({ sources: sources.length, entities: entities.length, episodes: episodes.length, jobs: jobs.length });
    }).catch(() => undefined);
    return () => { active = false; };
  }, [project.id]);

  const next = counts.sources === 0
    ? { title: "Import the source story", detail: "TXT and Markdown create evidence-addressable chunks.", route: "source" as AppRoute }
    : counts.entities === 0
      ? { title: "Extract canon", detail: "Create entities and facts with exact source evidence.", route: "source" as AppRoute }
      : counts.episodes === 0
        ? { title: "Adapt episode one", detail: "Select chunks and turn them into visual scenes.", route: "episodes" as AppRoute }
        : { title: "Open the storyboard desk", detail: "Review scenes, render placeholders, and approve production state.", route: "episodes" as AppRoute };

  return (
    <section className="standard-workspace overview-workspace">
      <header className="workspace-title">
        <span>Production overview</span>
        <h1>{project.name}</h1>
        <p>{project.description || "A local-first narrative production workspace."}</p>
      </header>
      <div className="metric-grid">
        <Metric icon={<FileText size={19} />} label="Sources" value={counts.sources} />
        <Metric icon={<BookOpenText size={19} />} label="Canon entities" value={counts.entities} />
        <Metric icon={<Clapperboard size={19} />} label="Episodes" value={counts.episodes} />
        <Metric icon={<ListChecks size={19} />} label="Jobs" value={counts.jobs} />
      </div>
      <div className="next-action-card">
        <div>
          <span>Suggested next</span>
          <h2>{next.title}</h2>
          <p>{next.detail}</p>
        </div>
        <ActionButton tone="primary" onClick={() => onNavigate(next.route)}>
          Continue <ArrowRight size={16} />
        </ActionButton>
      </div>
      <div className="principle-grid">
        <article><strong>Canon survives model swaps</strong><p>Models are replaceable providers; story state stays in SQLite and the project workspace.</p></article>
        <article><strong>Evidence stays attached</strong><p>Every extracted fact points back to an exact source chunk and confidence.</p></article>
        <article><strong>Humans hold authority</strong><p>Draft, review, approved, locked, and revise states remain explicit.</p></article>
      </div>
    </section>
  );
}

function Metric({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return <article className="metric-card"><span>{icon}</span><strong>{value}</strong><p>{label}</p></article>;
}
