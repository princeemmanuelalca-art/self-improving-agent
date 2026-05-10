#  Self-Improving Coding Agent

An autonomous coding agent that writes, executes, and debugs Python code using **Groq LLM** and **E2B Sandbox**.

## Features

-  **Self-Improving Loop**: Automatically reflects on errors and rewrites code
-  **Secure Execution**: Runs untrusted code in E2B cloud sandboxes
-  **Fast Inference**: Uses Groq's Llama 3.3 70B (blazing fast tokens/sec)
-  **Full Logging**: Tracks every iteration, code attempt, and execution result
-  **CLI Interface**: Simple command-line usage

## Architecture

```
User Task → Groq LLM → Python Code → E2B Sandbox → stdout/stderr
                                              ↓
                                    Error? → Reflect → Retry (max 5)
                                              ↓
                                    Success → Save Solution
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Get API Keys

**Groq API Key** (free tier available):
- Sign up at [console.groq.com](https://console.groq.com)
- Create an API key

**E2B API Key** (free tier, no credit card):
- Sign up at [e2b.dev](https://e2b.dev)
- No credit card required for free tier
- Create an API key in the dashboard

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your API keys
```

## Usage

### Basic Usage

```bash
python agent.py "Write a function to check if a number is prime"
```

### Complex Tasks

```bash
python agent.py "Create a script that fetches weather data from a public API and prints a formatted forecast"
```

### Read Task from File

```bash
echo "Sort a list of dictionaries by multiple keys" > task.txt
python agent.py --file task.txt
```

## Example Output

```
 Starting agent for task: Write a function to reverse a string...
 Model: llama-3.3-70b-versatile | Max iterations: 5

============================================================
 ITERATION 1/5
============================================================
 CODE:
def reverse_string(s):
    return s[::-1]

print(reverse_string("hello"))

 STDOUT:
olleh

 Exit Code: None
 Success: True

 SUCCESS! Task completed in 1 iteration(s).
 Solution saved to: solution_20240506_143022.py
```

## Error Recovery Example

```
 ITERATION 1/5
  STDERR: NameError: name 'pd' is not defined

 ITERATION 2/5
 CODE:
import pandas as pd
# ... corrected code

 SUCCESS! Task completed in 2 iteration(s).
```

## File Structure

```
.
├── agent.py              # Main agent implementation
├── requirements.txt      # Python dependencies
├── .env.example         # Environment variables template
├── .env                 # Your API keys (gitignored)
├── README.md            # This file
└── solution_*.py        # Generated solutions
```

## How It Works

1. **Task Ingestion**: User provides a natural language coding task
2. **Code Generation**: Groq LLM generates Python code based on system prompt
3. **Sandbox Execution**: Code runs in an isolated E2B cloud sandbox
4. **Result Analysis**: Agent checks stdout, stderr, and exit codes
5. **Reflection**: If errors exist, LLM reasons about the failure and generates fixed code
6. **Iteration**: Loop continues until success or max iterations (5)
7. **Output**: Final working code saved to a timestamped `.py` file

## System Prompt Engineering

The agent uses a carefully crafted system prompt that:
- Enforces raw Python output (no markdown)
- Requires self-contained, executable code
- Mandates error reflection before rewriting
- Prioritizes in-memory solutions over file I/O

## Limitations

- Max 5 iterations (configurable in `agent.py`)
- Code must be Python-only
- No persistent state between iterations (fresh sandbox each time)
- LLM context window limits may affect very long debugging sessions

## License

MIT
