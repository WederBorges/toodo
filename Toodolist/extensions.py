from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# Instância compartilhada: criada sem app (padrão application factory) e
# associada a um Flask app específico via limiter.init_app(app) em app.py.
# Isso permite decorar rotas em routes/*.py com @limiter.limit(...) mesmo
# antes do app existir.
limiter = Limiter(key_func=get_remote_address)
