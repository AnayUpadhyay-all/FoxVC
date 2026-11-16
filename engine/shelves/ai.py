"""
FoxVC AI & LLM Agent Processing Shelf (fuse ai).
Provides lightweight, zero-dependency LLM orchestration for both local models
(Ollama, llama.cpp, LocalAI) and cloud providers (Groq, OpenAI, Google Gemini, OpenRouter, DeepSeek).
"""

import os
import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional
from engine.runtime import FoxPack


# Default API endpoints
DEFAULT_ENDPOINTS = {
    "ollama": "http://localhost:11434/api/chat",
    "groq": "https://api.groq.com/openai/v1/chat/completions",
    "openai": "https://api.openai.com/v1/chat/completions",
    "openrouter": "https://openrouter.ai/api/v1/chat/completions",
    "deepseek": "https://api.deepseek.com/chat/completions",
    "gemini": "https://generativelanguage.googleapis.com/v1beta/openai/chat/completions",
}

DEFAULT_MODELS = {
    "ollama": "llama3",
    "groq": "llama-3.3-70b-versatile",
    "openai": "gpt-4o-mini",
    "openrouter": "meta-llama/llama-3.3-70b-instruct",
    "deepseek": "deepseek-chat",
    "gemini": "gemini-1.5-flash",
}


def _resolve_api_key(provider: str, api_key: Optional[str] = None) -> str:
    if api_key:
        return str(api_key).strip()
    env_keys = {
        "groq": "GROQ_API_KEY",
        "openai": "OPENAI_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }
    env_var = env_keys.get(provider.lower())
    if env_var:
        return os.environ.get(env_var, "").strip()
    return ""


def _post_json(url: str, payload: dict, headers: Optional[dict] = None, timeout: float = 60.0) -> dict:
    req_headers = {"Content-Type": "application/json", "User-Agent": "FoxVC-AI-Engine/1.0"}
    if headers:
        req_headers.update(headers)

    req_data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=req_data, headers=req_headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            res_body = response.read().decode("utf-8", errors="replace")
            return json.loads(res_body)
    except urllib.error.HTTPError as e:
        err_msg = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"AI API HTTP {e.code}: {err_msg}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"AI Connection Error ({url}): {e.reason}") from None
    except Exception as e:
        raise RuntimeError(f"AI Execution Error: {str(e)}") from None


def fox_ai_prompt(
    prompt: Any,
    model: Optional[str] = None,
    provider: str = "ollama",
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    temperature: float = 0.7,
    timeout: float = 60.0
) -> str:
    """
    Execute a single-turn prompt against a local or cloud LLM.
    Returns the assistant's string reply.
    """
    provider_clean = str(provider).lower().strip()
    model_name = str(model) if model else DEFAULT_MODELS.get(provider_clean, "llama3")
    key = _resolve_api_key(provider_clean, api_key)

    # 1. Ollama Native Endpoint
    if provider_clean == "ollama" and not endpoint:
        ollama_url = "http://localhost:11434/api/generate"
        payload = {
            "model": model_name,
            "prompt": str(prompt),
            "stream": False,
            "options": {"temperature": float(temperature)}
        }
        res = _post_json(ollama_url, payload, timeout=timeout)
        return res.get("response", "").strip()

    # 2. OpenAI-Compatible Format (Groq, OpenAI, Gemini, OpenRouter, DeepSeek, or Custom)
    url = endpoint or DEFAULT_ENDPOINTS.get(provider_clean, DEFAULT_ENDPOINTS["ollama"])
    headers = {}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    payload = {
        "model": model_name,
        "messages": [{"role": "user", "content": str(prompt)}],
        "temperature": float(temperature)
    }

    res = _post_json(url, payload, headers=headers, timeout=timeout)
    choices = res.get("choices", [])
    if choices and "message" in choices[0]:
        return choices[0]["message"].get("content", "").strip()
    if "response" in res:
        return res["response"].strip()
    return str(res)


def fox_ai_chat(
    messages: Any,
    model: Optional[str] = None,
    provider: str = "ollama",
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    temperature: float = 0.7,
    timeout: float = 60.0
) -> str:
    """
    Execute multi-turn conversation messages:
    messages: list of packs or dicts [{"role": "user", "content": "..."}]
    """
    provider_clean = str(provider).lower().strip()
    model_name = str(model) if model else DEFAULT_MODELS.get(provider_clean, "llama3")
    key = _resolve_api_key(provider_clean, api_key)
    url = endpoint or DEFAULT_ENDPOINTS.get(provider_clean, DEFAULT_ENDPOINTS["ollama"])

    # Normalize messages
    raw_msgs = []
    if isinstance(messages, (list, tuple)):
        for m in messages:
            if hasattr(m, "_data"):
                raw_msgs.append(dict(m._data))
            elif isinstance(m, dict):
                raw_msgs.append(dict(m))
            else:
                raw_msgs.append({"role": "user", "content": str(m)})
    else:
        raw_msgs = [{"role": "user", "content": str(messages)}]

    headers = {}
    if key:
        headers["Authorization"] = f"Bearer {key}"

    # Ollama native chat endpoint supports OpenAI format or native
    if provider_clean == "ollama" and not endpoint:
        payload = {
            "model": model_name,
            "messages": raw_msgs,
            "stream": False,
            "options": {"temperature": float(temperature)}
        }
        res = _post_json("http://localhost:11434/api/chat", payload, timeout=timeout)
        return res.get("message", {}).get("content", "").strip()

    payload = {
        "model": model_name,
        "messages": raw_msgs,
        "temperature": float(temperature)
    }
    res = _post_json(url, payload, headers=headers, timeout=timeout)
    choices = res.get("choices", [])
    if choices and "message" in choices[0]:
        return choices[0]["message"].get("content", "").strip()
    return str(res)


class FoxAIAgent:
    """Stateful conversational AI agent holding persona & chat memory."""
    def __init__(
        self,
        system_prompt: str,
        model: Optional[str] = None,
        provider: str = "ollama",
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        temperature: float = 0.7
    ):
        self.system_prompt = str(system_prompt)
        self.provider = str(provider).lower().strip()
        self.model = str(model) if model else DEFAULT_MODELS.get(self.provider, "llama3")
        self.api_key = _resolve_api_key(self.provider, api_key)
        self.endpoint = endpoint
        self.temperature = float(temperature)
        self.history: List[Dict[str, str]] = []
        self.reset()

    def reset(self):
        self.history = [{"role": "system", "content": self.system_prompt}]

    def ask(self, user_message: Any) -> str:
        self.history.append({"role": "user", "content": str(user_message)})
        reply = fox_ai_chat(
            self.history,
            model=self.model,
            provider=self.provider,
            api_key=self.api_key,
            endpoint=self.endpoint,
            temperature=self.temperature
        )
        self.history.append({"role": "assistant", "content": reply})
        return reply

    def get_history(self) -> FoxPack:
        return FoxPack({"messages": [FoxPack(m) for m in self.history]})

    def to_pack(self) -> FoxPack:
        return FoxPack({
            "ask": self.ask,
            "reset": self.reset,
            "history": self.get_history,
            "model": self.model,
            "provider": self.provider
        })


def fox_ai_agent(
    system_prompt: Any,
    model: Optional[str] = None,
    provider: str = "ollama",
    api_key: Optional[str] = None,
    endpoint: Optional[str] = None,
    temperature: float = 0.7
) -> FoxPack:
    agent = FoxAIAgent(
        str(system_prompt),
        model=model,
        provider=provider,
        api_key=api_key,
        endpoint=endpoint,
        temperature=temperature
    )
    return agent.to_pack()


def fox_ai_is_online(provider: str = "ollama", endpoint: Optional[str] = None) -> int:
    """Returns 1 if the LLM provider service is reachable, 0 otherwise."""
    provider_clean = str(provider).lower().strip()
    url = endpoint or ("http://localhost:11434" if provider_clean == "ollama" else DEFAULT_ENDPOINTS.get(provider_clean))
    if not url:
        return 0
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "FoxVC/1.0"})
        with urllib.request.urlopen(req, timeout=2.0) as res:
            return 1 if res.status in (200, 404, 405) else 0
    except Exception:
        return 0


def get_ai_shelf() -> Dict[str, Any]:
    """Returns the public FoxVC dictionary exposed by `fuse ai`."""
    return {
        "aiPrompt": fox_ai_prompt,
        "aiChat": fox_ai_chat,
        "aiAgent": fox_ai_agent,
        "aiIsOnline": fox_ai_is_online,
        "AI_MODELS": FoxPack(DEFAULT_MODELS),
    }
