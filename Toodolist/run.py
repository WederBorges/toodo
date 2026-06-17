from app import create_app
from database.conf import banco_prod
import os
from dotenv import load_dotenv

load_dotenv()




app = create_app(banco_prod.DATABASE_SQLALCHEMY_URI)

if __name__ == '__main__':


    app.run(
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000))
    )

