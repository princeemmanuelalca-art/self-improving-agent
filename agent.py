#!/usr/bin/env python3
"""
Self-Improving Coding Agent
Uses Groq LLM + E2B Sandbox for autonomous code generation and execution.
"""

import os
import sys
import asyncio
import json
import argparse
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from groq import AsyncGroq
from e2b_code_interpreter import Sandbox

# Load environment variables
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
E2B_API_KEY = os.getenv("E2B_API_KEY")

if not GROQ_API_KEY or not E2B_API_KEY:
    print("❌ Missing API keys. Set GROQ_API_KEY and E2B_API_KEY in .env")
    sys.exit(1)

# Configuration
MODEL = "llama-3.3-70b-versatile"
MAX_ITERATIONS = 5

SYSTEM_PROMPT = """You are an expert Python coding agent. Your job is to write correct, efficient Python code to solve the given task.

RULES:
1. Write ONLY Python code in your response (no markdown fences, no explanations outside code).
2. If the task requires input, use sample data or mock inputs.
3. The code must be self-contained and executable.
4. If you receive an error from a previous attempt, first REASON about what went wrong, then fix it.
5. Do not use external files unless necessary; prefer in-memory solutions.
6. Print the final result/output so it can be verified.

When reflecting on errors:
- Analyze the error message carefully
- Identify the root cause (syntax, logic, import, algorithm)
- Propose a concrete fix
- Then write the corrected code

Output format: Only raw Python code."""

REFLECTION_PROMPT = """The previous code execution failed. Here is the error/output:

{output}

Please REASON about what went wrong and why, then write the corrected Python code.
Follow the same rules as before. Output only raw Python code."""


class CodingAgent:
    def __init__(self):
        self.groq = AsyncGroq(api_key=GROQ_API_KEY)
        self.iteration = 0
        self.history = []

    async def generate_code(self, task: str, error_context: Optional[str] = None) -> str:
        """Generate Python code using Groq LLM."""
        if error_context:
            content = REFLECTION_PROMPT.format(output=error_context) + f"

Original task: {task}"
        else:
            content = task

        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": content}
        ]

        # Add history for context
        for past in self.history:
            messages.append({"role": "user", "content": f"Previous attempt {past['iteration']}:
{past['code']}"})
            messages.append({"role": "assistant", "content": f"Result: {past['result']}"})

        response = await self.groq.chat.completions.create(
            model=MODEL,
            messages=messages,
            temperature=0.2,
            max_tokens=4096,
        )

        code = response.choices[0].message.content.strip()

        # Clean up markdown fences if LLM added them
        if code.startswith("```python"):
            code = code[9:]
        if code.startswith("```"):
            code = code[3:]
        if code.endswith("```"):
            code = code[:-3]

        return code.strip()

    async def execute_code(self, code: str) -> dict:
        """Execute code in E2B sandbox and return results."""
        with Sandbox(api_key=E2B_API_KEY) as sandbox:
            execution = sandbox.run_code(code)

            stdout = "
".join([line for line in execution.logs.stdout]) if execution.logs.stdout else ""
            stderr = "
".join([line for line in execution.logs.stderr]) if execution.logs.stderr else ""

            return {
                "stdout": stdout,
                "stderr": stderr,
                "exit_code": execution.results[0].error if execution.results else None,
                "success": execution.results[0].error is None if execution.results else True,
            }

    def log_iteration(self, iteration: int, code: str, result: dict):
        """Log iteration details."""
        print(f"
{'='*60}")
        print(f"🔁 ITERATION {iteration}/{MAX_ITERATIONS}")
        print(f"{'='*60}")
        print(f"📝 CODE:
{code[:500]}{'...' if len(code) > 500 else ''}")
        print(f"
📤 STDOUT:
{result['stdout'][:300]}{'...' if len(result['stdout']) > 300 else ''}")
        if result['stderr']:
            print(f"
⚠️  STDERR:
{result['stderr'][:300]}{'...' if len(result['stderr']) > 300 else ''}")
        print(f"
🔢 Exit Code: {result['exit_code']}")
        print(f"✅ Success: {result['success']}")

    async def solve(self, task: str) -> dict:
        """Main agent loop: generate → execute → reflect → repeat."""
        print(f"🚀 Starting agent for task: {task[:80]}...")
        print(f"🤖 Model: {MODEL} | Max iterations: {MAX_ITERATIONS}")

        last_error = None

        for i in range(1, MAX_ITERATIONS + 1):
            self.iteration = i

            # Generate code
            code = await self.generate_code(task, last_error)

            # Execute code
            result = await self.execute_code(code)

            # Log
            self.log_iteration(i, code, result)
            self.history.append({"iteration": i, "code": code, "result": result})

            # Check success
            if result["success"] and not result["stderr"]:
                print(f"
🎉 SUCCESS! Task completed in {i} iteration(s).")
                return {
                    "success": True,
                    "iterations": i,
                    "code": code,
                    "stdout": result["stdout"],
                    "task": task,
                }

            # Prepare error context for next iteration
            last_error = f"STDOUT: {result['stdout']}
STDERR: {result['stderr']}
Exit Code: {result['exit_code']}"

        print(f"
❌ FAILED! Max iterations ({MAX_ITERATIONS}) reached.")
        return {
            "success": False,
            "iterations": MAX_ITERATIONS,
            "code": code,
            "stdout": result["stdout"],
            "stderr": result["stderr"],
            "task": task,
        }


async def main():
    parser = argparse.ArgumentParser(description="Self-Improving Coding Agent")
    parser.add_argument("task", nargs="?", help="Coding task description")
    parser.add_argument("--file", "-f", help="Read task from file")
    args = parser.parse_args()

    if args.file:
        with open(args.file, "r") as f:
            task = f.read().strip()
    elif args.task:
        task = args.task
    else:
        print("Usage: python agent.py \"your coding task\" OR python agent.py --file task.txt")
        sys.exit(1)

    agent = CodingAgent()
    result = await agent.solve(task)

    # Save result
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"solution_{timestamp}.py"
    with open(filename, "w") as f:
        f.write(f"# Task: {result['task']}\n")
        f.write(f"# Solved in {result['iterations']} iteration(s)\n")
        f.write(f"# Success: {result['success']}\n\n")
        f.write(result["code"])

    print(f"
💾 Solution saved to: {filename}")

    if result["success"]:
        print(f"
✅ Final Output:
{result['stdout']}")
    else:
        print(f"
❌ Final Error:
{result.get('stderr', 'Unknown error')}")


if __name__ == "__main__":
    asyncio.run(main())
