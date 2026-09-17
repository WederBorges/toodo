FROM python:3.12

WORKDIR /usr/local/app

RUN pip install --no-cache-dir --upgrade pip poetry

COPY . .

# Um venv isolado (em vez de instalar direto no site-packages do sistema)
# evita que as dependências do app colidam com as do próprio pip/poetry —
# foi exatamente essa colisão (um "attrs" novo pego pelo rich vendorizado
# do pip) que quebrou o build com virtualenvs.create=false.
RUN poetry config virtualenvs.in-project true \
 && poetry install --without dev

ENV PATH="/usr/local/app/.venv/bin:${PATH}"

EXPOSE 5000

CMD ["sh", "-c", "alembic upgrade head && exec gunicorn run:app --bind 0.0.0.0:${PORT:-5000}"]