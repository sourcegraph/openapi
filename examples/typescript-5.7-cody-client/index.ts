import dotenv from "dotenv";
import openai from "openai";

dotenv.config();

const token = process.env.SRC_ACCESS_TOKEN;
const endpoint = process.env.SRC_ENDPOINT;

interface CodyContextResponse {
  results: Array<{
    blob: {
      url: string;
      commit: {
        oid: string;
      };
      path: string;
      repository: {
        id: string;
        name: string;
      };
    };
    startLine: number;
    endLine: number;
    chunkContent: string;
  }>;
}

async function codyContext(
  query: string,
  repoNames: string[]
): Promise<CodyContextResponse> {
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

function formatContext(context: CodyContextResponse): string {
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

const client = new openai.OpenAI({
  baseURL: `${endpoint}/.api/llm`,
  apiKey: token,
});

const query = "what is the agent?";
const context = formatContext(
  await codyContext(query, ["github.com/sourcegraph/cody"])
);

const finalPrompt = `
You are a helpful coding assistant.
Here is relevant context for your question:

${context}

---
Question:

${query}
`;
// console.log(finalPrompt)
const response = await client.chat.completions.create({
  model: "anthropic::2023-06-01::claude-3.5-sonnet",
  max_tokens: 2000,
  messages: [
    {
      role: "user",
      content: finalPrompt,
    },
  ],
  stream: false,
});


const reply = response.choices.map((choice) => choice.message.content).join("\n");

console.log("REPLY:");
console.log(reply);
