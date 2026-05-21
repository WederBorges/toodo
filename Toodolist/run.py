from app import create_app
from database.conf import banco_prod

if __name__ == '__main__':
    app = create_app(banco_prod.DATABASE_SQLALCHEMY_URI)

    app.run(debug=True)

