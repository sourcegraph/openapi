use futures::stream::StreamExt;
use reqwest::header::{HeaderMap, HeaderValue, AUTHORIZATION, CONTENT_TYPE};
use reqwest::Client;
use serde_json::{json, Value};
use std::env;
use std::error::Error;
use std::process;
use structopt::StructOpt;

#[derive(StructOpt, Debug)]
#[structopt(name = "cody_chat")]
struct Opt {
    #[structopt(long = "context-repo", help = "Optional: Specify context repositories")]
    context_repo: Vec<String>,

    #[structopt(long, required = true, help = "The message to send to Cody")]
    message: String,
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn Error>> {
    let args: Vec<String> = env::args().collect();

    if args.len() == 1 {
        Opt::clap().print_help().unwrap();
        println!();
        process::exit(0);
    }

    let opt = Opt::from_args();

    let access_token = env::var("SRC_ACCESS_TOKEN")
        .expect("Error: SRC_ACCESS_TOKEN environment variable is not set.");
    let endpoint =
        env::var("SRC_ENDPOINT").expect("Error: SRC_ENDPOINT environment variable is not set.");

    let graphql_url = format!("{}/.api/graphql", endpoint);
    let chat_completions_url = format!(
        "{}/.api/completions/stream?api-version=1&client-name=jetbrains&client-version=6.0.0-SNAPSHOT'",
        endpoint
    );

    let mut headers = HeaderMap::new();
    headers.insert(CONTENT_TYPE, HeaderValue::from_static("application/json"));
    headers.insert(
        AUTHORIZATION,
        HeaderValue::from_str(&format!("token {}", access_token))?,
    );

    cody_chat(
        &opt.context_repo,
        &opt.message,
        &graphql_url,
        &chat_completions_url,
        &headers,
    )
    .await?;

    Ok(())
}

async fn cody_chat(
    repo_names: &[String],
    query: &str,
    graphql_url: &str,
    chat_completions_url: &str,
    headers: &HeaderMap,
) -> Result<(), Box<dyn Error>> {
    let final_prompt = if !repo_names.is_empty() {
        let context = get_repo_context(repo_names, query, graphql_url, headers).await?;
        format!(
            r#"
        You are a helpful assistant.
        You are given the following context:
        {}
        You are also given the following query:
        {}
        You need to answer the query based on the context.
        "#,
            context, query
        )
    } else {
        format!(
            r#"
        You are a helpful assistant.
        You are given the following query:
        {}
        Please provide an answer to the query.
        "#,
            query
        )
    };

    let response = chat_completions(&final_prompt, chat_completions_url, headers).await?;
    println!("{}", response);

    Ok(())
}

async fn get_repo_context(
    repo_names: &[String],
    query: &str,
    graphql_url: &str,
    headers: &HeaderMap,
) -> Result<String, Box<dyn Error>> {
    if repo_names.is_empty() {
        return Ok(String::new());
    }

    let repo_ids = get_repo_ids(repo_names, graphql_url, headers).await?;

    let context_search_query = r#"
    query GetCodyContext($repos: [ID!]!, $query: String!, $codeResultsCount: Int!, $textResultsCount: Int!) {
        getCodyContext(repos: $repos, query: $query, codeResultsCount: $codeResultsCount, textResultsCount: $textResultsCount) {
            ...on FileChunkContext {
                blob {
                    path
                    repository {
                      id
                      name
                    }
                    commit {
                      oid
                    }
                    url
                  }
                  startLine
                  endLine
                  chunkContent
            }
        }
    }
    "#;

    let variables = json!({
        "repos": repo_ids.values().collect::<Vec<_>>(),
        "query": query,
        "codeResultsCount": 10,
        "textResultsCount": 5,
    });

    let client = Client::new();
    let response = client
        .post(graphql_url)
        .headers(headers.clone())
        .json(&json!({
            "query": context_search_query,
            "variables": variables,
        }))
        .send()
        .await?;

    if response.status().is_success() {
        let data: Value = response.json().await?;
        let context = data["data"]["getCodyContext"].as_array().unwrap();
        Ok(format_context(context))
    } else {
        println!("Request failed with status code: {}", response.status());
        Ok(String::new())
    }
}

fn format_context(context: &[Value]) -> String {
    let mut context_parts = vec!["<context>".to_string()];

    for result in context {
        context_parts.push("<item>".to_string());
        context_parts.push(format!(
            "<file>{}:{}-{}</file>",
            result["blob"]["path"], result["startLine"], result["endLine"]
        ));
        context_parts.push(format!("<chunk>{}</chunk>", result["chunkContent"]));
        context_parts.push("</item>".to_string());
    }

    context_parts.push("</context>".to_string());
    context_parts.join("\n")
}

async fn get_repo_ids(
    repo_names: &[String],
    graphql_url: &str,
    headers: &HeaderMap,
) -> Result<serde_json::Map<String, Value>, Box<dyn Error>> {
    let repository_ids_query = r#"
    query Repositories($names: [String!]!, $first: Int!) {
        repositories(names: $names, first: $first) {
            nodes {
                name
                id
            }
        }
    }
    "#;

    let variables = json!({
        "names": repo_names,
        "first": repo_names.len(),
    });

    let client = Client::new();
    let response = client
        .post(graphql_url)
        .headers(headers.clone())
        .json(&json!({
            "query": repository_ids_query,
            "variables": variables,
        }))
        .send()
        .await?;

    if response.status().is_success() {
        let data: Value = response.json().await?;
        let nodes = data["data"]["repositories"]["nodes"].as_array().unwrap();
        Ok(nodes
            .iter()
            .map(|node| {
                (
                    node["name"].as_str().unwrap().to_string(),
                    node["id"].clone(),
                )
            })
            .collect())
    } else {
        println!(
            "Failed to fetch repository IDs. Status code: {}",
            response.status()
        );
        Ok(serde_json::Map::new())
    }
}

async fn chat_completions(
    query: &str,
    chat_completions_url: &str,
    headers: &HeaderMap,
) -> Result<String, Box<dyn Error>> {
    let data = json!({
        "maxTokensToSample": 4000,
        "messages": [{"speaker": "human", "text": query}],
        "model": "gpt-4o",
        "temperature": 0.2,
        "topK": -1,
        "topP": -1,
        "stream": true,
    });

    let client = Client::new();
    let mut response = client
        .post(chat_completions_url)
        .headers(headers.clone())
        .json(&data)
        .send()
        .await?
        .bytes_stream();

    let mut last_response = String::new();
    let mut buffer = String::new();

    while let Some(chunk) = response.next().await {
        let chunk = chunk?;
        buffer.push_str(&String::from_utf8_lossy(&chunk));

        while let Some(pos) = buffer.find('\n') {
            let line = buffer.drain(..=pos).collect::<String>();
            if line.starts_with("data: ") {
                let data = line.trim_start_matches("data: ");
                if data != "[DONE]" {
                    if let Ok(event_data) = serde_json::from_str::<Value>(data) {
                        if let Some(completion) = event_data["completion"].as_str() {
                            last_response = completion.to_string();
                        }
                    }
                }
            }
        }
    }

    Ok(last_response)
}
