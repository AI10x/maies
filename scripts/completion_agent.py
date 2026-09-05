import os
import sys
import argparse
from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI

# Load credentials from ~/projects/email_graphs/.env
load_dotenv("/home/emmanuel/projects/email_graphs/.env", override=True)

endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
api_key = os.environ.get("AZURE_OPENAI_API_KEY")

if endpoint and "/openai/v1" in endpoint:
    base_url = f"{endpoint.split('/openai/v1', 1)[0]}/openai/v1/"
    client = OpenAI(api_key=api_key, base_url=base_url)
else:
    client = AzureOpenAI(
        api_key=api_key,
        api_version=os.environ.get("AZURE_OPENAI_API_VERSION"),
        azure_endpoint=endpoint,
    )

deployment_name = os.environ.get("DEPLOYMENT_NAME", "gpt-5.6-sol")

DEFAULT_SYSTEM_PROMPT = (
    "You are a spec/text driven completion assistant. Your task is to output the characters/spec "
    "that should immediately follow the provided prefix code, to complete the line and/or subsequent lines. "
    "Do NOT repeat the prefix, do NOT wrap your answer in markdown code blocks (like ```), "
    "and do NOT include any introductory or explanatory text. Your response will be appended "
    "directly to the prefix, so it must form a syntactically correct and logical continuation. "
    "Provide ONLY the completion content."
)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--system-prompt-file",
        help="Path to a file containing the full system prompt.",
    )
    parser.add_argument(
        "--system-prompt",
        help="System prompt for the completion model. Supports escaped newlines (\\n).",
    )
    return parser.parse_args()


args = parse_args()
if args.system_prompt_file:
    with open(args.system_prompt_file, "r", encoding="utf-8") as f:
        system_prompt = f.read()
elif args.system_prompt:
    system_prompt = args.system_prompt.replace("\\n", "\n")
else:
    system_prompt = os.environ.get("SYSTEM_PROMPT", DEFAULT_SYSTEM_PROMPT).replace("\\n", "\n")

def get_completion(context):
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {"role": "user", "content": f"Prefix code:\n{context}\n\nProvide the completion for the spec after the prefix."}
            ]
        )
        text = response.choices[0].message.content
        if not text:
            return ""

        # Clean up code blocks if the model wrapped the response in them
        if text.startswith("```"):
            lines = text.splitlines()
            if len(lines) >= 2:
                if lines[-1].startswith("```"):
                    text = "\n".join(lines[1:-1])
                else:
                    text = "\n".join(lines[1:])
        return text
    except Exception as e:
        return f"Error: {e}"

# Simple protocol: read one line of context, output completion inside delimiters
for line in sys.stdin:
    if not line:
        continue
    # Decode double-escaped newlines and backslashes
    context = line.strip().replace("\\n", "\n").replace("\\\\", "\\")
    if context == "QUIT":
        break
    completion = get_completion(context)
    # Output completion, separated by a delimiter to handle multi-line returns
    print(f"COMPLETION_START\n{completion}\nCOMPLETION_END")
    sys.stdout.flush()
