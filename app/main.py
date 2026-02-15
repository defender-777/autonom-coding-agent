import argparse
import os
import sys
import json

from openai import OpenAI

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    # ✅ Define tools OUTSIDE the loop
    tools = [
        {
            "type": "function",
            "function": {
                "name": "Read",
                "description": "Read and return the contents of a file",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "The path to the file to read"
                        }
                    },
                    "required": ["file_path"]
                }
            }
        }
    ]

    # ✅ Initialize conversation memory
    messages = [{"role": "user", "content": args.p}]

    # ✅ AGENT LOOP
    while True:

        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=tools
        )

        message = chat.choices[0].message

        # Store assistant response
        messages.append(message)

        # ✅ Check if model wants to use a tool
        if message.tool_calls:

            for tool_call in message.tool_calls:

                if tool_call.function.name == "Read":

                    tool_args = json.loads(tool_call.function.arguments)
                    file_path = tool_args["file_path"]

                    with open(file_path, "r") as f:
                        content = f.read()

                    # Send tool result BACK to model
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": content
                    })

        else:
            # ✅ Final answer — exit loop
            print(message.content)
            break


if __name__ == "__main__":
    main()
