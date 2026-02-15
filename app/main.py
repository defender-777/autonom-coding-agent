import argparse
from email import message
import os
import sys

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

    chat = client.chat.completions.create(
    model="anthropic/claude-haiku-4.5",
    messages=[{"role": "user", "content": args.p}],
    tools=[
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
)

    message = chat.choices[0].message

    if message.tool_calls:
        tool_call = message.tool_calls[0]

        if tool_call.function.name == "Read":
            import json

            args = json.loads(tool_call.function.arguments)
            file_path = args["file_path"]

            with open(file_path, "r") as f:
                print(f.read())

    else:
        print(message.content)

if __name__ == "__main__":
    main()
