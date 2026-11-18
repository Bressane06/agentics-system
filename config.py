import os
from dotenv import load_dotenv

load_dotenv()

def _bool(nome: str, padrao: bool) -> bool:
    return os.getenv(nome, str(padrao)).strip().lower() in {"1", "true", "yes", "sim"}

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agenda.db")

# LLM (Ollama)
LLM_HABILITADO = _bool("LLM_HABILITADO", False)
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "30"))

# Loop de revisão e planejamento
MAX_REVISOES = int(os.getenv("MAX_REVISOES", "3"))
SESSAO_MAX_BLOCO_MIN = int(os.getenv("SESSAO_MAX_BLOCO_MIN", "120"))
SESSAO_MIN_BLOCO_MIN = int(os.getenv("SESSAO_MIN_BLOCO_MIN", "30"))
HORIZONTE_MAX_DIAS = int(os.getenv("HORIZONTE_MAX_DIAS", "90"))

# Guardrail: quantas posições o LLM pode mover uma tarefa no ranking
MAX_DESLOCAMENTO_LLM = int(os.getenv("MAX_DESLOCAMENTO_LLM", "3"))

# Pesos da fórmula de prioridade
PESO_URGENCIA = float(os.getenv("PESO_URGENCIA", "0.40"))
PESO_IMPORTANCIA = float(os.getenv("PESO_IMPORTANCIA", "0.25"))
PESO_DIFICULDADE = float(os.getenv("PESO_DIFICULDADE", "0.20"))
PESO_PROGRESSO = float(os.getenv("PESO_PROGRESSO", "0.15"))
