from fastapi import FastAPI

from models.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Agente de Planejamento Acadêmico")

@app.get("/health")
def health():
    return {"status": "ok"}