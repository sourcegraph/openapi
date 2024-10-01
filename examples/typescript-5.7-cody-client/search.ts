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
  console.log({ url: urlParams.toString() });
  const response = await fetch(
    `${params.endpoint}/.api/search/stream/?${urlParams}`,
    {
      method: "GET",
      headers: {
        Accept: "text/event-stream",
        Authorization: `token ${params.accessToken}`,
      },
    }
  );

  if (!response.ok) {
    throw new Error(
      `Failed to get search results: ${response.status} ${response.statusText}`
    );
  }

  if (!response.body) {
    throw new Error("No response body");
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  const out: string[] = [];
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    const chunk = decoder.decode(value);
    process.stdout.write(".");
    // console.log(chunk);
    out.push(chunk);
  }
  process.stdout.write("\n");
  const responseBody = out.join("");
  const events = parseSSE(responseBody);
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
  for (const commitResult of commitResults) {
    console.log("===============");
    console.log(commitResult.content);
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
