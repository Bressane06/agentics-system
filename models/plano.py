from datetime import date, datetime
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from models.database import Base

# proposta -> aprovada | rejeitada ; aprovada -> substituida (quando outro plano é aprovado)
STATUS_PLANO = ("proposta", "aprovada", "rejeitada", "substituida")

class Plano(Base):
    """Uma versão de plano de estudos proposta pelo sistema de agentes."""
    __tablename__ = "planos"

    id: Mapped[int] = mapped_column(primary_key=True)   # também é a "versão" das sessões
    criado_em: Mapped[datetime] = mapped_column(default=datetime.now)
    referencia: Mapped[date]                            # "hoje" usado no planejamento
    status: Mapped[str] = mapped_column(String(20), default="proposta")
    usou_llm: Mapped[bool] = mapped_column(default=False)
    resumo: Mapped[str] = mapped_column(Text, default="{}")  # JSON: ordem, problemas, revisões...
    motivo_rejeicao: Mapped[str] = mapped_column(Text, default="")

    sessoes = relationship("Sessao", back_populates="plano",
                           order_by="(Sessao.data, Sessao.hora_inicio)",
                           cascade="all, delete-orphan")
    tracos = relationship("Traco", back_populates="plano", order_by="Traco.ordem",
                          cascade="all, delete-orphan")
