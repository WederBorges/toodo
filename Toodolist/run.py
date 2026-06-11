from app import create_app
from database.conf import banco_prod

app = create_app(banco_prod.DATABASE_SQLALCHEMY_URI)

if __name__ == '__main__':


    app.run(debug=True)

