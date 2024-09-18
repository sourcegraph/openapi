import requests
import os
import argparse


access_token = os.getenv('SRC_ACCESS_TOKEN')
if not access_token:
    raise ValueError("Error: SRC_ACCESS_TOKEN environment variable is not set.")
endpoint = os.getenv('SRC_ENDPOINT')
if not endpoint:
    raise ValueError("Error: SRC_ENDPOINT environment variable is not set.")
# GraphQL endpoint URL
graphql_url = endpoint + "/.api/graphql"
chat_completions_url = endpoint + "/.api/completions/stream?api-version=1&client-name=jetbrains&client-version=6.0.0-SNAPSHOT'"
# Headers
headers = {
    "Content-Type": "application/json",
    "Authorization": f"token {access_token}"
}

def format_context(context):
    """
    Format the context for the given repositories and query.
    
    :param context: The context to format
    :return: The formatted context (string)
    """

    context_parts = []
    context_parts.append("<context>")
    for result in context:
        context_parts.append("<item>")
        context_parts.append(f"<file>{result['blob']['path']}:{result['startLine']}-{result['endLine']}</file>")
        context_parts.append(f"<chunk>{result['chunkContent']}</chunk>")
        context_parts.append("</item>")
    context_parts.append("</context>")

    formatted_context = "\n".join(context_parts)

    return formatted_context

def get_repo_context(repo_names, query, code_results_count=10, text_results_count=5):
    """
    Get repository context using a GraphQL query.
    
    :param repos: List of repository IDs
    :param query: Search query string
    :param code_results_count: Number of code results to return (default: 10)
    :param text_results_count: Number of text results to return (default: 5)
    :return: JSON response containing the repository context
    """
    CONTEXT_SEARCH_QUERY = """
    query GetCodyContext($repos: [ID!]!, $query: String!, $codeResultsCount: Int!, $textResultsCount: Int!, $filePatterns: [String!]) {
        getCodyContext(repos: $repos, query: $query, codeResultsCount: $codeResultsCount, textResultsCount: $textResultsCount, filePatterns: $filePatterns) {
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
    """
    if not repo_names:
        return ""
    repo_ids = get_repo_ids(repo_names)

    variables = {
        "repos": list(repo_ids.values()),
        "query": query,
        "codeResultsCount": code_results_count,
        "textResultsCount": text_results_count,
        "filePatterns": []
    }

    response = requests.post(graphql_url, json={"query": CONTEXT_SEARCH_QUERY, "variables": variables}, headers=headers)
    
    if response.status_code == 200:
        return format_context(response.json()['data']['getCodyContext'])
    else:
        print(f"Request failed with status code: {response.status_code}")
        return None


def get_repo_ids(repo_names):
    """
    Convert repository names to their corresponding IDs using a GraphQL query.
    
    :param repo_names: List of repository names
    :return: Dictionary mapping repository names to their IDs
    """
    REPOSITORY_IDS_QUERY = """
    query Repositories($names: [String!]!, $first: Int!) {
        repositories(names: $names, first: $first) {
            nodes {
                name
                id
            }
        }
    }
    """
    
    variables = {
        "names": repo_names,
        "first": len(repo_names)
    }
    
    response = requests.post(
        graphql_url,
        json={"query": REPOSITORY_IDS_QUERY, "variables": variables},
        headers=headers
    )
    
    if response.status_code == 200:
        data = response.json()
        return {node['name']: node['id'] for node in data['data']['repositories']['nodes']}
    else:
        print(f"Failed to fetch repository IDs. Status code: {response.status_code}")
        return {}


def chat_completions(query):
    """
    Send a chat completion request to the Sourcegraph API.

    :param query: The user's query (string)
    :return: The completion response (string)
    """
    data = {
        'maxTokensToSample': 4000,
        'messages': [
            {
                'speaker': 'human',
                'text': query
            }
        ],
        'model': 'gpt-4o',
        'temperature': 0.2,
        'topK': -1,
        'topP': -1,
        'stream': False
    }

    response = requests.post(chat_completions_url, headers=headers, json=data)

    if response.status_code == 200:
        return response.json().get('completion', '')
    else:
        print(f"Request failed with status code: {response.status_code}")
        return None



def cody_chat(repo_names, query):
    """
    Get context for the given repositories and query, then print it out.
    
    :param repo_names: List of repository names (strings)
    :param query: Natural language query (string)
    """
    context = get_repo_context(
        repo_names=repo_names,
        query=query,
    )
    final_prompt = f"""
    You are a helpful assistant.
    You are given the following context:
    {context}
    You are also given the following query:
    {query}
    You need to answer the query based on the context.
    """

    response = chat_completions(final_prompt)
    print(response)
    


def main():
    parser = argparse.ArgumentParser(description="Cody Chat CLI")
    parser.add_argument('--context-repo', action='append', help='Repository name (can be used multiple times)')
    parser.add_argument('--message', type=str, help='Query message')

    args = parser.parse_args()

    if not args.message:
        raise ValueError("Error: --message argument is required.")

    if not args.context_repo:
        raise ValueError("Error: --context-repo argument is required.")

    repo_names = args.context_repo
    query = args.message
    cody_chat(repo_names, query)

if __name__ == "__main__":
    main()
