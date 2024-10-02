import type { Credentials } from "./Credentials";
import { parseSSE } from "./sse";

export interface SearchParams extends Credentials {
  searchQuery: string;
  contextLines: number;
}

export async function searchCommits(
  params: SearchParams
): Promise<CommitSearchResult[]> {
  const urlParams = new URLSearchParams({
    q: params.searchQuery,
    cl: String(params.contextLines),
  });

  let response;
  try {
    response = await fetch(
      `${params.endpoint}/.api/search/stream/?${urlParams}`,
      {
        method: "GET",
        headers: {
          Accept: "text/event-stream",
          Authorization: `token ${params.accessToken}`,
        },
      }
    );
  } catch (error) {
    console.error("Failed to fetch search results:", error);
    throw error;
  }

  if (!response.ok) {
    const errorMessage = `Failed to get search results: ${response.status} ${response.statusText}`;
    console.error(errorMessage);
    throw new Error(errorMessage);
  }

  if (!response.body) {
    const errorMessage = "No response body";
    console.error(errorMessage);
    throw new Error(errorMessage);
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const out: string[] = [];

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      const chunk = decoder.decode(value);
      process.stdout.write(".");
      out.push(chunk);
    }
  } catch (error) {
    console.error("Error reading response stream:", error);
    throw error;
  }

  process.stdout.write("\n");

  const responseBody = out.join("");
  let events;

  try {
    events = parseSSE(responseBody);
  } catch (error) {
    console.error("Error parsing SSE response:", error);
    throw error;
  }

  const commitResults: CommitSearchResult[] = [];

  for (const event of events) {
    if (event.event !== "matches") {
      continue;
    }

    for (const match of event.data as CommitSearchResult[]) {
      if (match.type === "commit") {
        commitResults.push(match);
      }
    }
  }

  return commitResults;
}

export interface CommitSearchResult {
  type: string;
  label: string;
  url: string;
  detail: string;
  repositoryID: number;
  repository: string;
  externalServiceType: string;
  oid: string;
  message: string;
  authorName: string;
  authorDate: string;
  committerName: string;
  committerDate: string;
  repoStars: number;
  repoLastFetched: string;
  content: string;
}
