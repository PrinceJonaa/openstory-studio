import { useEffect, useState } from "react";
import { CheckCircle2, CircleDashed, ListChecks, XCircle } from "lucide-react";

import { EmptyState } from "../../components/EmptyState";
import { api } from "../../lib/api";
import type { Job } from "../../lib/types";

export function JobsWorkspace({ projectId }: { projectId: string }) {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  useEffect(() => { let active = true; api.listJobs(projectId).then((items) => active && setJobs(items)).finally(() => active && setLoading(false)); return () => { active = false; }; }, [projectId]);
  if (loading) return <div className="desk-state">Loading jobs…</div>;
  return <section className="standard-workspace jobs-workspace"><header className="workspace-title"><span>Observable model work</span><h1>Jobs</h1><p>Queued, running, succeeded, and failed work remains visible.</p></header>{!jobs.length ? <EmptyState title="No jobs yet" detail="Extraction, adaptation, storyboard, render, and export work appears here." /> : <div className="jobs-table"><div className="jobs-table__head"><span>Kind</span><span>Status</span><span>Progress</span><span>Result</span></div>{[...jobs].reverse().map((job) => <article key={job.id}><div><ListChecks size={16} /><strong>{job.kind.replaceAll("_", " ")}</strong></div><span className={`job-status job-status--${job.status}`}>{job.status === "succeeded" ? <CheckCircle2 size={14} /> : job.status === "failed" ? <XCircle size={14} /> : <CircleDashed size={14} />}{job.status}</span><div className="job-progress"><span><i style={{ width: `${job.progress_total ? (job.progress_current / job.progress_total) * 100 : 0}%` }} /></span><small>{job.progress_current}/{job.progress_total ?? "—"}</small></div><p>{job.error || (job.status === "succeeded" ? "Completed" : "Waiting")}</p></article>)}</div>}</section>;
}
