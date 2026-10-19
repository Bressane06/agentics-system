from datetime import time
from sqlalchemy.orm import Mapped, mapped_column
from models.database import Base

class Disponibilidade(Base):
    __tablename__ = "disponibilidade"

    id: Mapped[int] = mapped_column(primary_key=True)
    dia_semana: Mapped[int]        # 0 = segunda ... 6 = domingo
    hora_inicio: Mapped[time]
    hora_fim: Mapped[time]