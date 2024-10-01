import { Command } from "commander";
import dotenv from "dotenv";
import openai from "openai";
import type { Credentials } from "./Credentials";
import { codyContext, formatContext } from "./codyContext";
import { review } from "./review";
import { searchCommits } from "./search";

dotenv.config();

export const token = process.env.SRC_ACCESS_TOKEN;
if (!token) {
  throw new Error("SRC_ACCESS_TOKEN is not set");
}
export const endpoint = process.env.SRC_ENDPOINT;
if (!endpoint) {
  throw new Error("SRC_ENDPOINT is not set");
}

const credentials: Credentials = {
  accessToken: token,
  endpoint,
};

const llmClient = new openai.OpenAI({
  baseURL: `${endpoint}/.api/llm`,
  apiKey: token,
});

const command = new Command("cody")
  .addCommand(
    new Command("models").action(async () => {
      const models = await llmClient.models.list();
      console.log(models.data.map((m) => m.id).join("\n"));
    })
  )
  .addCommand(
    new Command("batch-review")
      .description(
        `
Example usage:
❯ bun run index.ts batch-review --search-query 'repo:^github\.com/sourcegraph/cody$ type:diff after:"2024-07-01" before:"2024-08-01"' --review-instruction 'A significant feature addition should be guarded a feature flag' --max-commits 20 --model google::v1::gemini-1.5-flash
`
      )
      .requiredOption("--search-query <query>")
      .requiredOption("--review-instruction <instruction>")
      .option("--context-lines <num>", "context lines", "3")
      .option("--max-commits <num>", "maximum number of commits to review", "2")
      .option(
        "--model <model>",
        "LLM model to use",
        "anthropic::2023-06-01::claude-3.5-sonnet"
      )
      .action(
        async ({
          searchQuery,
          reviewInstruction,
          contextLines,
          maxCommits,
          model,
        }) => {
          const commits = await searchCommits({
            searchQuery,
            ...credentials,
            contextLines: Number.parseInt(contextLines, 10),
          });
          const diagnostics = await Promise.all(
            commits.slice(0, Number.parseInt(maxCommits, 10)).map((commit) =>
              review(
                llmClient,
                {
                  ...credentials,
                  model,
                  instruction: reviewInstruction,
                },
                commit
              )
            )
          );
          for (const diagnostic of diagnostics.flat()) {
            console.log(diagnostic);
          }
        }
      )
  )
  .addCommand(
    new Command("context")
      .option("--repo <repo>", "repo name")
      .requiredOption("--query <query>", "query")
      .action(async ({ repo, query }) => {
        const repos = repo ? [repo] : [];
        const context = formatContext(await codyContext(query, repos));
        console.log(context);
        const finalPrompt = `
You are a helpful coding assistant.
Here is relevant context for your question:

${context}

---
Question:

${query}
`;

        // console.log(finalPrompt)
        const response = await llmClient.chat.completions.create({
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

        const reply = response.choices
          .map((choice) => choice.message.content)
          .join("\n");

        console.log("REPLY:");
        console.log(reply);
      })
  );

command.parse(process.argv);
