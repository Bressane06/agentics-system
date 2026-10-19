import os
from dotenv import load_dotenv

load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agenda.db")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
MAX_REVISOES = int(os.getenv("MAX_REVISOES", "3"))

# Pesos da fórmula de prioridade
PESO_URGENCIA = float(os.getenv("PESO_URGENCIA", "0.40"))
PESO_IMPORTANCIA = float(os.getenv("PESO_IMPORTANCIA", "0.25"))
PESO_DIFICULDADE = float(os.getenv("PESO_DIFICULDADE", "0.20"))
PESO_PROGRESSO = float(os.getenv("PESO_PROGRESSO", "0.15"))