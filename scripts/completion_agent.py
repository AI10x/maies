# SPDX-FileCopyrightText: 2020 Ilaï Deutel & Kibi Contributors
# SPDX-License-Identifier: MIT OR Apache-2.0

import argparse
import os
import sys

from openai import AzureOpenAI, OpenAI


DEFAULT_SYSTEM_PROMPT = (
    "You are a spec/text driven completion assistant. Output only the characters "
    "that should immediately follow the provided prefix. Do not repeat the prefix, "
    "use Markdown fences, or add explanatory text."
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--system-prompt-file")
    parser.add_argument("--system-prompt")
    return parser.parse_args()


def get_system_prompt(args):
    if args.system_prompt_file:
        with open(args.system_prompt_file, encoding="utf-8") as prompt_file:
            return prompt_file.read()
    if args.system_prompt:
        return args.system_prompt.replace("\\n", "\n")
    if prompt_path := os.environ.get("MAIES_SYSTEM_PROMPT_FILE"):
        with open(prompt_path, encoding="utf-8") as prompt_file:
            return prompt_file.read()
    return os.environ.get("MAIES_SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT).replace("\\n", "\n")


def create_client():
    endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
    azure_key = os.environ.get("AZURE_OPENAI_API_KEY")
    if endpoint:
        return AzureOpenAI(
            api_key=azure_key,
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=endpoint,
        )
    options = {"api_key": os.environ.get("OPENAI_API_KEY")}
    if base_url := os.environ.get("OPENAI_BASE_URL"):
        options["base_url"] = base_url
    return OpenAI(**options)


def complete(client, model, system_prompt, context):
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Prefix code:\n{context}"},
        ],
    )
    text = response.choices[0].message.content or ""
    if text.startswith("```"):
        lines = text.splitlines()
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:])
    return text


def write_response(status, request_id, payload):
    encoded = payload.encode("utf-8")
    sys.stdout.buffer.write(f"{status} {request_id} {len(encoded)}\n".encode())
    sys.stdout.buffer.write(encoded)
    sys.stdout.buffer.flush()


def main():
    args = parse_args()
    system_prompt = get_system_prompt(args)
    model = os.environ.get("MAIES_AI_MODEL") or os.environ.get("DEPLOYMENT_NAME")
    if not model:
        raise RuntimeError("Set MAIES_AI_MODEL to an OpenAI model or Azure deployment name")
    client = create_client()

    while header := sys.stdin.buffer.readline():
        request_id, length = header.split()
        context = sys.stdin.buffer.read(int(length)).decode("utf-8")
        request_id = request_id.decode()
        try:
            write_response("OK", request_id, complete(client, model, system_prompt, context))
        except Exception as error:
            write_response("ERR", request_id, str(error))


if __name__ == "__main__":
    main()
