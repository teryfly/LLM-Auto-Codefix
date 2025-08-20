# utils/url_utils.py

from urllib.parse import quote

def encode_project_path(name: str) -> str:
    """
    对 GitLab 项目路径进行 URL 编码（斜杠需编码为 %2F）
    例如: ai/dotnet-ai-demo -> ai%2Fdotnet-ai-demo
    """
    return quote(name, safe='')