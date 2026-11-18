"""Cliente de LLM. Isolado atrás de um Protocol para ser trocado por um dublê nos testes."""
import json
from typing import Protocol

import httpx

import config

class LLMError(Exception):
    """Qualquer falha ao obter uma resposta JSON utilizável do modelo."""

class LLMClient(Protocol):
    def gerar_json(self, prompt: str) -> dict: ...

class OllamaClient:
    def __init__(self, host: str = config.OLLAMA_HOST, modelo: str = config.OLLAMA_MODEL,
                 timeout: float = config.LLM_TIMEOUT, http: httpx.Client | None = None):
        self.host = host.rstrip("/")
        self.modelo = modelo
        self.timeout = timeout
        self._http = http

    def gerar_json(self, prompt: str) -> dict:
        corpo = {
            "model": self.modelo,
            "prompt": prompt,
            "format": "json",
            "stream": False,
            "options": {"temperature": 0},
        }
        try:
            if self._http is not None:
                resp = self._http.post(f"{self.host}/api/generate", json=corpo)
            else:
                resp = httpx.post(f"{self.host}/api/generate", json=corpo, timeout=self.timeout)
            resp.raise_for_status()
            dados = json.loads(resp.json()["response"])
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise LLMError(f"Falha ao consultar o LLM: {exc}") from exc
        if not isinstance(dados, dict):
            raise LLMError("O LLM não retornou um objeto JSON.")
        return dados
