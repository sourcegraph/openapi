import re
from typing import Dict, Union, TypedDict, List, Optional, Tuple
from dataclasses import dataclass
import tempfile
import shutil
import subprocess

@dataclass
class GradingResult:
    pass_: bool
    score: float
    reason: str
    component_results: Optional[List["GradingResult"]] = None
    named_scores: Optional[Dict[str, float]] = None

def score_bool(ok: bool) -> float:
    return 1.0 if ok else 0.0

def boolean_grading_result(name: str, ok: bool, stdout: str) -> GradingResult:
    reason = name if ok else f"{name} - {stdout}"
    return {
        "pass": ok,
        "score": score_bool(ok),
        "reason": reason,
    }

def get_assert(output: str, context) -> Union[bool, float, GradingResult]:
    prototype_dir = context['vars']['dir']
    temp_dir = create_temp_dir(prototype_dir)
    test_cases = parse_test_cases(output)
    write_test_cases(temp_dir, test_cases)
    install_ok, install_out = exec_command(temp_dir, ["mvn", "install", "-DskipTests=true", "-Dmaven.compile.skip=true"])
    compile_ok, compile_out = exec_command(temp_dir, ["mvn", "test-compile"]) if install_ok else False
    test_ok, test_out = exec_command(temp_dir, ["mvn", "test"]) if compile_ok else False
    final_pass_scores = [install_ok, compile_ok, test_ok]
    max_score = len(final_pass_scores)
    final_score = sum([1.0 if ok else 0.0 for ok in final_pass_scores]) / max_score
    return {
        "pass": test_ok,
        "score": final_score,
        "reason": f"Java Composite Test metrics {temp_dir}",
        "componentResults": [
            boolean_grading_result("mvn install", install_ok, install_out),
            boolean_grading_result("mvn test-compile", compile_ok, compile_out),
            boolean_grading_result("mvn test", test_ok, test_out),
        ],
    }

def create_temp_dir(prototype_dir: str) -> str:
    temp_dir = tempfile.mkdtemp()
    shutil.copytree(prototype_dir, temp_dir, dirs_exist_ok=True)
    return temp_dir


class TestCase(TypedDict):
    filename: str
    code: str


def parse_test_cases(output: str) -> list[TestCase]:
    test_cases: List[TestCase] = []
    pattern = r'<TEST_FILE filename="([^"]+)">(.*?)</TEST_FILE>'
    matches = re.finditer(pattern, output, re.DOTALL)

    for match in matches:
        filename = match.group(1)
        code = match.group(2).strip()
        test_case: TestCase = {"filename": filename, "code": code}
        test_cases.append(test_case)

    return test_cases

def write_test_cases(temp_dir: str, test_cases: List[TestCase]) -> None:
    for test_case in test_cases:
        if isinstance(test_case, str):
            raise ValueError(test_case)
        print("TEST_CASE")
        print(test_case)
        print(test_case.keys())
        filename = test_case["filename"]
        code = test_case["code"]
        with open(f"{temp_dir}/{filename}", "w") as file:
            file.write(code)

def exec_command(working_dir: str, args: List[str]) -> Tuple[bool, str]:
    try:
        subprocess.run(args, cwd=working_dir, check=True, capture_output=True, text=True)
        return (True, "")
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {' '.join(args)}")
        print(f"Working directory: {working_dir}")
        print(f"Exit code: {e.returncode}")
        print(f"Stdout: {e.stdout}")
        print(f"Stderr: {e.stderr}")
        return (False, e.stdout + e.stderr)
