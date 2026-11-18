from datetime import datetime
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.database import Base

class Traco(Base):
    """Evento de observabilidade de uma execução do sistema de agentes."""
    __tablename__ = "tracos"

    id: Mapped[int] = mapped_column(primary_key=True)
    plano_id: Mapped[int] = mapped_column(ForeignKey("planos.id"))
    ordem: Mapped[int]
    agente: Mapped[str] = mapped_column(String(40))
    etapa: Mapped[str] = mapped_column(String(60))
    dados: Mapped[str] = mapped_column(Text, default="{}")   # JSON
    duracao_ms: Mapped[float | None] = mapped_column(default=None)
    criado_em: Mapped[datetime] = mapped_column(default=datetime.now)

    plano = relationship("Plano", back_populates="tracos")
