"""Dublês de LLM para testes e evals: respostas roteirizadas, sem rede."""
from services.llm import LLMError

class LLMRoteirizado:
    """Devolve, em ordem, as respostas fornecidas. Uma Exception na lista é levantada."""

    def __init__(self, *respostas):
        self.respostas = list(respostas)
        self.prompts: list[str] = []

    def gerar_json(self, prompt: str) -> dict:
        self.prompts.append(prompt)
        if not self.respostas:
            raise LLMError("sem resposta roteirizada")
        r = self.respostas.pop(0) if len(self.respostas) > 1 else self.respostas[0]
        if isinstance(r, Exception):
            raise r
        return r

class LLMIndisponivel:
    def __init__(self):
        self.prompts: list[str] = []

    def gerar_json(self, prompt: str) -> dict:
        self.prompts.append(prompt)
        raise LLMError("Ollama fora do ar")
