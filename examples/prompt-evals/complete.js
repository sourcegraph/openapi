const fs = require('node:fs')
const fetch = require('node-fetch')

const endpoint = process.env.SRC_ENDPOINT
const token = process.env.SRC_ACCESS_TOKEN

if (!endpoint) {
    throw new Error("Missing environment variable SRC_ENDPOINT")
}
if (!token) {
    throw new Error("Missing environment variable SRC_ACCESS_TOKEN")
}

const modelName = process.argv[2]
if (!modelName) {
    throw new Error("Missing model")
}
const models = [
    "anthropic::2023-06-01::claude-3.5-sonnet",
    "anthropic::2023-06-01::claude-3-opus",
    "anthropic::2023-06-01::claude-3-haiku",
    "fireworks::v1::starcoder",
    "fireworks::v1::deepseek-coder-v2-lite-base",
    "google::v1::gemini-1.5-pro",
    "google::v1::gemini-1.5-flash",
    "openai::2024-02-01::gpt-4o",
    "openai::2024-02-01::cody-chat-preview-001",
    "openai::2024-02-01::cody-chat-preview-002",
]
const byName = new Map()
for (const model of models) {
    const [, , name] = model.split('::')
    byName.set(name, model)
}

function log(msg) {
    fs.writeFileSync('log.txt', `${msg}\n`, { flag: 'a' })
}
// log(JSON.stringify(process.argv))


const prompt = process.argv[3]
if (!prompt) {
    throw new Error("Missing prompt")
}
async function main() {
    const model = byName.get(modelName)
    if (!model) {
        throw new Error(`Unknown model ${modelName}`)
    }
    const requestBody = {
                model,
                max_tokens: 4000,
                messages: [
                    {
                        role: 'user',
                        content: prompt
                    }
                ]
            }
    const response = await fetch(
        `${endpoint}/.api/llm/chat/completions`,
        {
            method: 'POST',
            headers: {
                Authorization: `token ${token}`,
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestBody)
        }
    )
    if (!response.ok) {
        const body = await response.text()
        throw new Error(`Failed to fetch: ${response.status} ${response.statusText} ${body}`)
    }
    const json = await response.json()
    const reply = json.choices[0].message.content
    console.log(reply)

}

main().then(() => process.exit(0)).catch(error => {
    console.error(error)
    process.exit(1)
})

