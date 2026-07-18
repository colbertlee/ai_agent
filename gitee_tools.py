import os
import base64
from typing import Any, Dict
import requests
from dotenv import load_dotenv

load_dotenv()

GITEE_TOKEN = os.getenv("GITEE_TOKEN", "")
GITEE_USERNAME = os.getenv("GITEE_USERNAME", "colbertlee").lower()
GITEE_API_BASE = "https://gitee.com/api/v5"

def get_params():
    return {"access_token": GITEE_TOKEN} if GITEE_TOKEN else {}


def handle_gitee_list_repos(args: Dict[str, Any]) -> str:
    try:
        url = f"{GITEE_API_BASE}/user/repos"
        r = requests.get(url, params={**get_params(), "per_page": 10}, timeout=15)
        repos = r.json()
        if not isinstance(repos, list):
            return f"Error: {repos.get('message', 'Failed')}"
        return "\n".join([f"{repo['full_name']} ({repo.get('stargazers_count',0)} stars)" for repo in repos])
    except Exception as e:
        return f"Error: {str(e)}"


def handle_gitee_get_repo(args: Dict[str, Any]) -> str:
    owner, repo = args.get("owner", ""), args.get("repo", "")
    if not owner or not repo:
        return "Error: owner and repo required"
    try:
        r = requests.get(f"{GITEE_API_BASE}/repos/{owner}/{repo}", params=get_params(), timeout=15)
        data = r.json()
        if data.get("message"):
            return f"Error: {data['message']}"
        return f"{data['full_name']}\nStars: {data.get('stargazers_count',0)}\n{data.get('description','')}"
    except Exception as e:
        return f"Error: {str(e)}"


def handle_gitee_create_file(args: Dict[str, Any]) -> str:
    owner, repo, path, content = args.get("owner", ""), args.get("repo", ""), args.get("path", ""), args.get("content", "")
    if not all([owner, repo, path, content]):
        return "Error: owner, repo, path, content required"
    try:
        url = f"{GITEE_API_BASE}/repos/{owner}/{repo}/contents/{path}"
        data = {**get_params(), "message": "Update via AI Agent", "content": base64.b64encode(content.encode()).decode()}
        r = requests.post(url, json=data, timeout=15)
        return f"Success!" if "path" in r.json() else f"Error: {r.json().get('message')}"
    except Exception as e:
        return f"Error: {str(e)}"


def handle_gitee_search_repos(args: Dict[str, Any]) -> str:
    keyword = args.get("keyword", "")
    if not keyword:
        return "Error: keyword required"
    try:
        url = "https://gitee.com/api/v5/search/repositories"
        r = requests.get(url, params={**get_params(), "q": keyword, "per_page": 5}, timeout=15)
        repos = r.json()
        return "\n".join([f"{repo['full_name']} - {repo.get('stargazers_count',0)} stars" for repo in repos])
    except Exception as e:
        return f"Error: {str(e)}"
