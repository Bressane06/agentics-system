import os
from dotenv import load_dotenv

load_dotenv() 

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./agenda.db")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")
MAX_REVISOES = int(os.getenv("MAX_REVISOES", "3"))

# Pesos da fórmula de prioridade
PESO_URGENCIA = 0.40
PESO_IMPORTANCIA = 0.25
PESO_DIFICULDADE = 0.20
PESO_PROGRESSO = 0.15