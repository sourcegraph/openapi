import type OpenAI from "openai";
import type { Credentials } from "./Credentials";
import type { CodyClient } from "./client";
import type { CommitSearchResult } from "./search";

export interface ReviewParams extends Credentials {
  instruction: string;
  model: string;
}

export interface Diagnostic {
  text: string;
  filepath: string;
  url: string;
}

export async function review(
  client: CodyClient,
  params: ReviewParams,
  commit: CommitSearchResult
): Promise<Diagnostic[]> {
  console.log(`Reviewing commit: ${commit.label}`);
  const completion = await client.getCompletions({
    model: params.model,
    message: `You are a helpful coding assistant reviewing a git commit.

<AUTHOR>${commit.authorName}</AUTHOR>
<AUTHOR_DATE>${commit.authorDate}</AUTHOR_DATE>
<COMMIT_MESSAGE>${commit.message}</COMMIT_MESSAGE>
<DIFF_CONTENT>
${commit.content}
</DIFF_CONTENT>

<REVIEW_INSTRUCTION>
${params.instruction}
</REVIEW_INSTRUCTION>

Print out a list of diagnostics based on the review instruction.
If there is nothing to act on the instruction (example: the diff is good)
then don't print a diagnostic.
Each diagnostic should be formatted as XML

<DIAGNOSTIC filepath="$FILE_PATH">
Analysis taking into account the commit details and the review instruction. 
</DIAGNOSTIC>
`,
  });
  return parseDiagnostic(params, commit, completion);
}

function parseDiagnostic(
  credentials: Credentials,
  commit: CommitSearchResult,
  llmResponse: string
): Diagnostic[] {
  const matches = llmResponse.matchAll(
    /<DIAGNOSTIC filepath="([^"]+)">([^<]+)<\/DIAGNOSTIC>/g
  );
  if (!matches) {
    return [];
  }
  const diagnostics: Diagnostic[] = [];
  for (const match of matches) {
    diagnostics.push({
      text: match[2],
      url: `${credentials.endpoint}/${commit.repository}/-/commit/${commit.oid}`,
      filepath: match[1],
    });
  }
  return diagnostics;
}
