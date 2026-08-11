import os
import subprocess
import json

import requests
from openai import OpenAI

with open("prompts/review.md", "r", encoding="utf-8") as f:
    system_prompt = f.read()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

def get_git_diff():
    base_ref = os.environ["GITHUB_BASE_REF"]

    subprocess.run(
        ["git", "fetch", "origin", base_ref],
        check=True
    )

    return subprocess.check_output(
        ["git", "diff", f"origin/{base_ref}...HEAD"],
        text=True
    )

def get_ai_review(diff):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": diff
            }
        ]
    )

    return response.choices[0].message.content


def post_comment(review):
    repository = os.environ["GITHUB_REPOSITORY"]
    owner, repo = repository.split("/", 1)
    with open(os.environ["GITHUB_EVENT_PATH"], "r", encoding="utf-8") as f:
        event = json.load(f)
    pull_number = event["pull_request"]["number"]

    print(review[:500])

    token = os.environ["GITHUB_TOKEN"]

    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json"
    }

    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{pull_number}/comments"

    result = requests.post(
        url,
        headers=headers,
        json={"body": review}
    )

    if result.status_code == 201:
        print("✅ Review comment posted successfully")
    else:
        print(f"❌ Failed: {result.status_code}")
        print(result.text)



def main():
    diff = get_git_diff()

    review = get_ai_review(diff)

    post_comment(review)

if __name__ == "__main__":
    main()