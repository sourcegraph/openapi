import os
import json

def code_reviewer(context: dict) -> str:
    with open('context.json', 'a') as f:
        json.dump(context, f)
        f.write('\n')
    variables: dict = context['vars']
    instruction = "List all the functions defined in the above files."
    return format_directory(variables['dir'], instruction)

def generate_java_test(context: dict) -> str:
    variables: dict = context['vars']
    instruction = """Write a single JUnit 5 test case for the code in the above files.

                     The quality of this test case will be measured by
                     - Whether it compiles
                     - Whether the test passes
                     - A mutation testing score
                     A good test cases compiles successfully, passes, and has a high mutation testing score.

                     Rules of thumb:
                     - Make sure to create separate test cases for separate features.
                     - It's OK to create multiple test files, one test file per main file.

                     In the name of the test file, include the enclosing directory names. For example, the path src/main/java/foo/Foo.java
                     should have an accompanying test file src/test/java/foo/FooTest.java

                     Print the response in the following XML format:
                     <TEST_FILE filename="$NAME_OF_THE_TEST_FILE">
                     $CONTENTS_OF_THE_TEST_FILE
                     </TEST_FILE>
                     """
    dir = os.path.join(variables['dir'], 'src', 'main', 'java')
    return format_directory(dir, instruction)

def format_directory(dir: str, instruction: str) -> str:
    prompt = []
    for file, content in walk_dir(dir):
        prompt.append(format_context_file(file, content))
    prompt.append(instruction)
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
