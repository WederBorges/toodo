from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import create_engine
from flask import current_app
class Base(DeclarativeBase):
    ...

class banco_prod():
    DATABASE_SQLALCHEMY_URI = "sqlite:///data/toodo.db"

