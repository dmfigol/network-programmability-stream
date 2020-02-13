FROM python:3.6-alpine
LABEL maintainer="Dmitry Figol <git@dmfigol.me>"

WORKDIR /app

RUN apk add --no-cache \
        build-base \
        libffi-dev \
        openssl-dev \
        gcc \
        libxslt-dev \
        libxslt \
        libxml2 \
        libxml2-dev \
    && pip install --no-cache-dir poetry \
    && poetry config settings.virtualenvs.in-project true

COPY pyproject.toml .
COPY poetry.lock .

RUN poetry run pip install -U pip \
    && poetry install --no-dev --no-interaction

EXPOSE 8000

WORKDIR /app/netprog_stream

CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]