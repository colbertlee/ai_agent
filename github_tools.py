import os
import base64
import json
from typing import Any, Dict
import requests
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN", "")
GITHUB_API_BASE = "https://api.github.com"

def get_headers():
    h = {"Accept": "application/vnd.github.v3+json"}
    if GITHUB_TOKEN:
        h["Authorization"] = f"token {GITHUB_TOKEN}"
    return h


def handle_github_list_repos(args: Dict[str, Any]) -> str:
    try:
        url = f"{GITHUB_API_BASE}/user/repos"
        r = requests.get(url, headers=get_headers(), params={"per_page": 10}, timeout=10)
        repos = r.json()
        if not isinstance(repos, list):
            return f"Error: {repos.get('message', 'Failed')}"
        return "\n".join([f"{repo['full_name']} ({repo.get('stargazers_count',0)} stars)" for repo in repos])
    except Exception as e:
        return f"Error: {str(e)}"


def handle_github_get_repo(args: Dict[str, Any]) -> str:
    owner, repo = args.get("owner", ""), args.get("repo", "")
    if not owner or not repo:
        return "Error: owner and repo required"
    try:
        r = requests.get(f"{GITHUB_API_BASE}/repos/{owner}/{repo}", headers=get_headers(), timeout=10)
        data = r.json()
        if "message" in data:
            return f"Error: {data['message']}"
        return f"{data['full_name']}\nStars: {data.get('stargazers_count',0)}\nForks: {data.get('forks_count',0)}\n{data.get('description','')}"
    except Exception as e:
        return f"Error: {str(e)}"


def handle_github_create_file(args: Dict[str, Any]) -> str:
    owner, repo, path, content = args.get("owner", ""), args.get("repo", ""), args.get("path", ""), args.get("content", "")
    if not all([owner, repo, path, content]):
        return "Error: owner, repo, path, content required"
    try:
        url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{path}"
        data = {"message": "Update via AI Agent", "content": base64.b64encode(content.encode()).decode()}
        r = requests.put(url, headers=get_headers(), json=data, timeout=10)
        return f"Success!" if r.status_code in [200, 201] else f"Error: {r.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"


def handle_github_search_repos(args: Dict[str, Any]) -> str:
    query = args.get("query", "")
    if not query:
        return "Error: query required"
    try:
        r = requests.get("https://api.github.com/search/repositories",
                        headers=get_headers(), params={"q": query, "per_page": 5}, timeout=10)
        items = r.json().get("items", [])
        return "\n".join([f"{i['full_name']} - {i.get('stargazers_count',0)} stars" for i in items])
    except Exception as e:
        return f"Error: {str(e)}"
