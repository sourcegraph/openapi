import type { Credentials } from "./Credentials";

export class CodyClient {
  constructor(private readonly credentials: Credentials) {}

  public async getCompletions(params: {
    message: string;
    model: string;
  }): Promise<string> {
    const url = `${this.credentials.endpoint}/.api/completions/stream?api-version=1&client-name=openapi-examples&client-version=1.0.0`;
    console.log({ url });
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        authorization: `token ${this.credentials.accessToken}`,
      },
      body: JSON.stringify({
        model: params.model,
        maxTokensToSample: 4000,
        stream: false,
        messages: [
          {
            speaker: "human",
            text: params.message,
          },
        ],
      }),
    });
    if (!response.ok) {
      const body = await response.text();
      throw new Error(
        `Failed to get completions: ${response.status} ${response.statusText} ${body}`
      );
    }
    const json = await response.json();
    return json.completion;
  }
}
