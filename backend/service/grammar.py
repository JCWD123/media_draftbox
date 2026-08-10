"""
语法检查服务 - LanguageTool API
"""
import requests


def check_grammar(text: str, language: str):
    """语法检查"""
    try:
        url = "https://api.languagetool.org/v2/check"
        data = {"text": text, "language": language}
        response = requests.post(url, data=data, timeout=10)
        result = response.json()
        return {"matches": result.get("matches", []), "total": len(result.get("matches", []))}
    except Exception as e:
        return {"error": str(e), "matches": [], "total": 0}
