import { endpoint, token } from ".";
import type { CodyContextResponse } from "./CodyContextResponse";

export async function codyContext(
  query: string,
  repoNames: string[]): Promise<CodyContextResponse> {
  const response = await fetch(
    `${endpoint}/.api/cody/context`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        authorization: `token ${token}`,
      },
      body: JSON.stringify({
        query,
        repos: repoNames.map((repo) => ({ name: repo })),
      }),
    }
  );
  if (!response.ok) {
    throw new Error(
      `Failed to get context: ${response.status} ${response.statusText}`
    );
  }
  return await response.json();
}

export function formatContext(context: CodyContextResponse): string {
  const out: string[] = [];
  for (const result of context.results) {
    out.push(
      `<CONTEXT_ITEM repo="${result.blob.repository.name}" start_line="${result.startLine}" end_line="${result.endLine}" path="${result.blob.path}">`
    );
    out.push(result.chunkContent);
    out.push("</CONTEXT_ITEM>");
  }
  return out.join("\n");
}
