from flask import current_app
from app import create_app
from database.conf import banco_prod
from contextlib import contextmanager
from smtplib import SMTP
from dotenv import load_dotenv
import os

load_dotenv()

database_uri = os.getenv(
    "DATABASE_URL", 
     os.getenv("DATABASE_URL_PUBLIC", banco_prod.DATABASE_SQLALCHEMY_URI))

if database_uri.startswith("postgresql://"):
    database_uri = database_uri.replace(
        "postgresql://",
        "postgresql+psycopg://"
    )   

app = create_app(database_uri)

@contextmanager
def connection_bd():
     with app.app_context():    
        with current_app.Session() as session:
            yield session
