from datetime import datetime
from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column
from models.database import Base

class Historico(Base):
    __tablename__ = "historico_alteracoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_hora: Mapped[datetime] = mapped_column(default=datetime.now)
    acao: Mapped[str] = mapped_column(String(50)) 
    detalhes: Mapped[str] = mapped_column(Text, default="")