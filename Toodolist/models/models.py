from database.conf import Base
from sqlalchemy import String, VARCHAR, DATETIME
from typing import List, Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column
from datetime import datetime
from flask_login import UserMixin

class User(UserMixin,Base):
    __tablename__ = "user_account"

    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[str] = mapped_column(String(30))
    password: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    tarefas: Mapped[List["Tarefas"]] = relationship(back_populates='responsavel')

class Tarefas(UserMixin,Base):
    __tablename__ = "tarefas"

    id: Mapped[int] = mapped_column(primary_key=True)
    tarefa: Mapped[str] = mapped_column(String(300))
    descricao_obj: Mapped[str] = mapped_column(VARCHAR(300))
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(DATETIME())

    responsavel_id: Mapped[Optional[int]] = mapped_column(ForeignKey("user_account.id"), nullable=True)
    responsavel: Mapped["User"] = relationship(back_populates="tarefas")