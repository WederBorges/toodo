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
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
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

    etapas: Mapped[List["Etapa"]] = relationship(
        "Etapa",
        back_populates='tarefa',
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Etapa.id")


class Etapa(Base):
    """Subitem/anotação de uma tarefa (ex.: os passos para concluí-la)."""
    __tablename__ = "etapas"

    id: Mapped[int] = mapped_column(primary_key=True)
    descricao: Mapped[str] = mapped_column(String(300), nullable=False)
    concluida: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())

    tarefa_id: Mapped[int] = mapped_column(ForeignKey(
                                            "tarefas.id",
                                            ondelete="CASCADE",
                                            name="fk_etapas_tarefa_id"),
                                            nullable=False)
    tarefa: Mapped["Tarefas"] = relationship(back_populates="etapas")


class EmailToken(Base):
    """Token de uso único para confirmação de email e redefinição de senha.

    Guarda apenas o hash do token (nunca o valor enviado por email), para que
    um vazamento do banco não permita reconstruir links válidos.
    """
    __tablename__ = "email_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey(
                                            "user_account.id",
                                            ondelete="CASCADE",
                                            name="fk_email_tokens_user_id"),
                                            nullable=False)
    token_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    purpose: Mapped[str] = mapped_column(String(20), nullable=False)
    created_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(TIMESTAMP(timezone=False), nullable=False)
    used_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP(timezone=False), nullable=True)

    __table_args__ = (
        UniqueConstraint("token_hash", name="uq_email_tokens_token_hash"),
    )