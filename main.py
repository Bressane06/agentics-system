from fastapi import FastAPI

app = FastAPI(title="Agente de Planejamento Acadêmico")

@app.get("/health")
def health():
    return {"status": "ok"}