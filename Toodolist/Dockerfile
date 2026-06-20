FROM python:3.12

WORKDIR /usr/local/app

RUN pip install poetry

COPY . .

RUN poetry config virtualenvs.create false

RUN poetry install

EXPOSE 8080

CMD gunicorn run:app --bind 0.0.0.0:$PORT