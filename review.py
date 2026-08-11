import os
import subprocess
import json

import requests
from openai import OpenAI


client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url="https://api.deepseek.com"
)

diff = subprocess.check_output(
    ["git", "diff", "HEAD~1", "HEAD"],
    text=True
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {
            "role": "system",
            "content": "你是一名经验丰富的软件工程师，请对下面的 Git diff 进行 Code Review，指出问题并给出改进建议。"
        },
        {
            "role": "user",
            "content": diff
        }
    ]
)

review = response.choices[0].message.content

repository = os.environ["GITHUB_REPOSITORY"]
owner, repo = repository.split("/", 1)
with open(os.environ["GITHUB_EVENT_PATH"], "r", encoding="utf-8") as f:
    event = json.load(f)
pull_number = event["pull_request"]["number"]

print(owner, repo, pull_number)
print(review)

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

print(result.status_code)