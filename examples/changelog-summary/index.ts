import { createTwoFilesPatch } from "diff";

const query = `
query RepositoryComparisonCommits($repoName: String!, $base: String, $head: String, $first: Int, $path: String) {
    repository(name: $repoName) {
      comparison(base: $base, head: $head) {
        commits(first: $first, path: $path) {
          nodes {
            ...Commit
          }
          pageInfo {
            hasNextPage
          }
        }
      }
    }
  }
  
  fragment Commit on GitCommit {
    id
    abbreviatedOID
    canonicalURL
    subject
    body
    diff {
      fileDiffs {
        nodes {
          oldFile {
            path
            content
          }
          newFile {
            path
            content
          }
        }
      }
    }
  }
`;

interface RepositoryComparisonCommitsResponse {
	data: {
		repository: {
			comparison: {
				commits: {
					nodes: Array<{
						id: string;
						abbreviatedOID: string;
						canonicalURL: string;
						subject: string;
						body: string | null;
						diff: {
							fileDiffs: {
								nodes: Array<{
									oldFile?: {
										path?: string;
										content?: string;
									};
									newFile?: {
										path?: string;
										content?: string;
									};
								}>;
							};
						};
					}>;
					pageInfo: {
						hasNextPage: boolean;
					};
				};
			};
		};
	};
}

const endpoint = process.env.SRC_ENDPOINT;
const accessToken = process.env.SRC_ACCESS_TOKEN;
if (!endpoint || !accessToken) {
	throw new Error("SRC_ENDPOINT and SRC_ACCESS_TOKEN must be set");
}

async function fetchGraphQL<T>(
	query: string,
	variables: Record<string, unknown>,
): Promise<T> {
	const response = await fetch(`${endpoint}/.api/graphql`, {
		method: "POST",
		headers: {
			"Content-Type": "application/json",
			Authorization: `token ${accessToken}`,
		},
		body: JSON.stringify({ query, variables }),
	});
	if (!response.ok) {
		throw new Error(
			`Failed to fetch GraphQL data: ${response.statusText}\n${await response.text()}`,
		);
	}
	return response.json() as Promise<T>;
}

const commits = await fetchGraphQL<RepositoryComparisonCommitsResponse>(query, {
	base: "vscode-v1.36.3",
	first: 10,
	head: "vscode-v1.38.0",
	path: "",
	repoName: "github.com/sourcegraph/cody",
});

function unifiedDiff(commits: RepositoryComparisonCommitsResponse): string {
	const out: string[] = [];
	for (const commit of commits.data.repository.comparison.commits.nodes) {
		for (const fileDiff of commit.diff.fileDiffs.nodes) {
			const patch = createTwoFilesPatch(
				fileDiff?.oldFile?.path ?? "",
				fileDiff?.newFile?.path ?? "",
				fileDiff?.oldFile?.content ?? "",
				fileDiff?.newFile?.content ?? "",
			);
			out.push(patch);
		}
	}
	return out.join("\n");
}

console.log(unifiedDiff(commits));
