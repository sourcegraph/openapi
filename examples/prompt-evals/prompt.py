import os
import json

def code_reviewer(context: dict) -> str:
    with open('context.json', 'a') as f:
        json.dump(context, f)
        f.write('\n')
    # provider: dict = context['providers']
    # provider_id: str = provider['id']  # ex. openai:gpt-4o or bedrock:anthropic.claude-3-sonnet-20240229-v1:0
    # with open(f'context-{provider_id}.json', 'w') as f:
    #     f.write(json.dumps(context))
    # provider_label: str | None = provider.get('label') # exists if set in promptfoo config.
    variables: dict = context['vars'] # access the test case variables
    dir = variables['dir']
    prompt = []
    for file, content in walk_dir(dir):
        prompt.append(format_context_file(file, content))
    prompt.append("List all the functions defined in the above files.")
    return '\n'.join(prompt)

def format_context_file(filename: str, content: str) -> str:
    return f"<CONTEXT_FILE FILE_NAME={filename}>\n{content}\n</CONTEXT_FILE>"

def walk_dir(dir: str) -> list:
    file_content_pairs = []
    for root, _, files in os.walk(dir):
        for file in files:
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            file_content_pairs.append((file, content))
    return file_content_pairs

if __name__ == "__main__":
    with open('context.json', 'r') as f:
        context = json.loads(f.readline())
    # If you specify a `function_name` in the provider string, it will run that function
    # If you don't specify a `function_name` in the provider string, it will run the main
    print(code_reviewer(context))
