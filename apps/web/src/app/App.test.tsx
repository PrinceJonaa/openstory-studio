import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";

import { api } from "../lib/api";
import type { Project } from "../lib/types";
import { App } from "./App";

vi.mock("../lib/api", () => ({
  api: {
    listProjects: vi.fn(),
    createProject: vi.fn(),
  },
}));

vi.mock("../features/projects/ProjectOverview", () => ({
  ProjectOverview: ({ project }: { project: Project }) => <h1>{project.name}</h1>,
}));

const project: Project = {
  id: "project-1",
  name: "The Glass Orchard",
  slug: "the-glass-orchard",
  description: "An orchard at the edge of winter.",
  target_format: "storyboard",
  created_at: "2026-08-10T00:00:00Z",
  updated_at: "2026-08-10T00:00:00Z",
};

beforeEach(() => {
  localStorage.clear();
  vi.mocked(api.listProjects).mockResolvedValue([]);
  vi.mocked(api.createProject).mockResolvedValue(project);
});

it("creates the first local project and opens its overview", async () => {
  const user = userEvent.setup();
  render(<App />);

  expect(await screen.findByRole("heading", { name: "Create your story workspace" })).toBeVisible();
  await user.type(screen.getByLabelText("Project name"), "The Glass Orchard");
  await user.type(screen.getByLabelText("Description"), "An orchard at the edge of winter.");
  await user.click(screen.getByRole("button", { name: "Create project" }));

  await waitFor(() =>
    expect(api.createProject).toHaveBeenCalledWith({
      name: "The Glass Orchard",
      description: "An orchard at the edge of winter.",
      target_format: "storyboard",
    }),
  );
  expect(await screen.findByRole("heading", { name: "The Glass Orchard" })).toBeVisible();
  expect(localStorage.getItem("openstory:last-project")).toBe("project-1");
});
