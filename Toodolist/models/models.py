from database.conf import Base
from sqlalchemy import String, VARCHAR,  Boolean, UniqueConstraint, TIMESTAMP
from typing import List, Optional
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, relationship
from sqlalchemy.orm import mapped_column
from datetime import datetime
from flask_login import UserMixin
from sqlalchemy.sql import func

class User(UserMixin,Base):
    __tablename__ = "user_account"
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    id: Mapped[int] = mapped_column(primary_key=True)
    user: Mapped[str] = mapped_column(String(30),nullable=False)
    password: Mapped[str] = mapped_column(VARCHAR(100), nullable=False)
    email: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    receber_mensagem: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    #user_ativo: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True) para o próximo estudo

    tarefas: Mapped[List["Tarefas"]] = relationship(
        "Tarefas",
        back_populates='responsavel',
        cascade="all, delete-orphan",
        passive_deletes=True)
    
    __table_args__ = (
        UniqueConstraint("user", name="uq_user_account_user"),
        UniqueConstraint("email", name="uq_user_account_email")
    )

class Tarefas(Base):
    __tablename__ = "tarefas"

    id: Mapped[int] = mapped_column(primary_key=True)
    tarefa: Mapped[str] = mapped_column(String(300))
    descricao_obj: Mapped[str] = mapped_column(VARCHAR(300))
    status: Mapped[str] = mapped_column(String(30))
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False))

    responsavel_id: Mapped[Optional[int]] = mapped_column(ForeignKey(
                                                            "user_account.id", 
                                                            ondelete="CASCADE", 
                                                            name="fk_tarefas_responsavel_id"), 
                                                            nullable=False)
    responsavel: Mapped["User"] = relationship(back_populates="tarefas")