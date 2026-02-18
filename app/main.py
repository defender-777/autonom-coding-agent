import argparse
import os
import json
import subprocess

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", required=True)
    args = parser.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    # ✅ Advertise ALL tools
    tools = [
        {
            "type": "function",
            "function": {
                "name": "Read",
                "description": "Read and return the contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"}
                    },
                    "required": ["file_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "Write",
                "description": "Write content to a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string"},
                        "content": {"type": "string"}
                    },
                    "required": ["file_path", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "Bash",
                "description": "Execute a shell command",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string"}
                    },
                    "required": ["command"]
                }
            }
        }
    ]

    messages = [{"role": "user", "content": args.p}]

    # ✅ AGENT LOOP
    while True:

        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=tools
        )

        message = chat.choices[0].message
        messages.append(message)

        if message.tool_calls:

            for tool_call in message.tool_calls:

                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)

                # -------------------------
                # READ TOOL
                # -------------------------
                if tool_name == "Read":
                    file_path = tool_args["file_path"]

                    with open(file_path, "r") as f:
                        content = f.read()

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": content
                    })

                # -------------------------
                # WRITE TOOL
                # -------------------------
                elif tool_name == "Write":
                    file_path = tool_args["file_path"]
                    content = tool_args["content"]

                    with open(file_path, "w") as f:
                        f.write(content)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": "File written successfully"
                    })

                # -------------------------
                # BASH TOOL
                # -------------------------
                elif tool_name == "Bash":
                    command = tool_args["command"]

                    try:
                        result = subprocess.run(
                            command,
                            shell=True,
                            capture_output=True,
                            text=True
                        )

                        output = result.stdout if result.stdout else result.stderr

                        if not output:
                            output = "Command executed successfully."

                    except Exception as e:
                        output = str(e)

                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": output
                    })

        else:
            print(message.content)
            break


if __name__ == "__main__":
    main()
