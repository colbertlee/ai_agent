from datetime import datetime
import math
import os
from typing import Union
import json
from langchain_core.tools import tool

_rag_instance = None

def set_rag_instance(rag):
    global _rag_instance
    _rag_instance = rag

def get_rag_instance():
    return _rag_instance

@tool
def get_current_time() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool
def calculate(expression: str) -> Union[float, int, str]:
    try:
        expression = expression.replace("^", "**")
        result = eval(expression, {"__builtins__": None}, {
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "sqrt": math.sqrt, "abs": abs, "pi": math.pi, "e": math.e,
        })
        return result
    except Exception as e:
        return f"计算错误: {str(e)}"

@tool
def search_web(query: str) -> str:
    try:
        from serpapi import GoogleSearch
        from config import SERPAPI_API_KEY
        if not SERPAPI_API_KEY:
            return "请先配置 SERPAPI_API_KEY"
        search = GoogleSearch({"q": query, "api_key": SERPAPI_API_KEY, "num": 5})
        results = search.get_dict()
        if "organic_results" in results:
            return "\n\n".join([f"{r.get('title')}\n{r.get('snippet')}" for r in results["organic_results"][:5]])
        return "未找到相关结果"
    except Exception as e:
        return f"搜索错误: {str(e)}"

@tool
def query_knowledge_base(query: str) -> str:
    rag = get_rag_instance()
    return rag.query(query) if rag else "知识库未初始化"

@tool
def load_knowledge_base(file_path: str) -> str:
    rag = get_rag_instance()
    if not rag or not os.path.exists(file_path):
        return "文件不存在或知识库未初始化"
    return "文档加载成功" if rag.load_documents([file_path]) else "加载失败"

@tool
def read_file(file_path: str) -> str:
    if ".." in file_path or file_path.startswith("/"):
        return "Access denied"
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            return content[:5000] + "..." if len(content) > 5000 else content
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def write_file(file_path: str, content: str, append: bool = False) -> str:
    if ".." in file_path or file_path.startswith("/"):
        return "Access denied"
    try:
        with open(file_path, 'a' if append else 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Success: {file_path}"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def list_files(directory: str = ".") -> str:
    if ".." in directory or directory.startswith("/"):
        return "Access denied"
    try:
        return "\n".join(os.listdir(directory)) or "Empty"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def run_code(code: str) -> str:
    dangerous = ['import', 'exec', 'eval', 'open', '__import__']
    for p in dangerous:
        if p in code:
            return f"Forbidden: {p}"
    try:
        result = eval(code, {"__builtins__": None}, {
            "sin": math.sin, "cos": math.cos, "tan": math.tan,
            "sqrt": math.sqrt, "abs": abs, "pi": math.pi, "e": math.e,
        })
        return f"Result: {result}"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def get_weather(city: str) -> str:
    try:
        import requests
        r = requests.get(f"http://wttr.in/{city}?format=j1", timeout=15)
        if r.status_code == 200:
            data = r.json().get("current_condition", [{}])[0]
            return f"{city}: {data.get('temp_C')}C, Humidity: {data.get('humidity')}%"
        return f"Error: {r.status_code}"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def github_search(query: str) -> str:
    try:
        import requests
        r = requests.get("https://api.github.com/search/repositories",
                        params={"q": query, "per_page": 5}, timeout=15)
        if r.status_code == 200:
            return "\n".join([f"{i['full_name']} - {i.get('stargazers_count',0)} stars" for i in r.json().get("items", [])])
        return "No results"
    except Exception as e:
        return f"Error: {str(e)}"

@tool
def generate_chart(data: str, chart_type: str = "bar") -> str:
    try:
        import matplotlib.pyplot as plt
        d = json.loads(data)
        plt.figure(figsize=(8, 6))
        plt.bar(d.get("labels",[]), d.get("values",[]), color='skyblue')
        filename = f"chart_{int(datetime.now().timestamp())}.png"
        plt.savefig(filename)
        plt.close()
        return f"Saved: {filename}"
    except Exception as e:
        return f"Error: {str(e)}"

def get_all_tools():
    return [get_current_time, calculate, search_web, query_knowledge_base,
            load_knowledge_base, read_file, write_file, list_files, run_code,
            get_weather, github_search, generate_chart]
