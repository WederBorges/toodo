from app import create_app
from database.conf import banco_prod
import os
from dotenv import load_dotenv

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

if __name__ == '__main__':


    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000))
    )

