import type OpenAI from "openai";
import type { Credentials } from "./Credentials";
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
  client: OpenAI,
  params: ReviewParams,
  commit: CommitSearchResult
): Promise<Diagnostic[]> {
  console.log(`Reviewing commit: ${commit.label}`);
  const completion = await client.chat.completions.create({
    model: params.model,
    max_tokens: 4000,
    stream: false,
    messages: [
      {
        role: "user",
        content: `
You are a helpful coding assistant.

<AUTHOR>${commit.authorName}</AUTHOR>
<AUTHOR_DATE>${commit.authorDate}</AUTHOR_DATE>
<COMMIT_MESSAGE>${commit.message}</COMMIT_MESSAGE>
<DIFF_CONTENT>
${commit.content}
</DIFF_CONTENT>

<REVIEW_INSTRUCTION>
${params.instruction}
</REVIEW_INSTRUCTION>

Print out a list of diagnostics based on the review instruction. Each diagnostic should be formatted as XML

<DIAGNOSTIC filepath="$FILE_PATH">
Act on the instruction. For example, if it says produce a diff to fix the bug, print the diff here. If the instruction says,
come up with a test case, print the test case here. Formatted as markdown.
</DIAGNOSTIC>
`,
      },
    ],
  });
  const reply = completion.choices[0].message.content ?? "";
  return parseDiagnostic(params, commit, reply);
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
