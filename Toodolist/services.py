from flask import current_app
from app import create_app
from database.conf import banco_prod
from contextlib import contextmanager
from smtplib import SMTP
from dotenv import load_dotenv
import os

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"  # Replace with your SMTP server
SMTP_PORT = 587  # Use 465 for SSL or 587 for TLS
USERNAME = os.getenv('EMAIL_TOODO')  # Your email login
PASSWORD = os.getenv('PASSWORD_TOODO') # Your email password

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

@contextmanager
def conection_stmp():
    with app.app_context():
        with SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(USERNAME, PASSWORD)
            yield server