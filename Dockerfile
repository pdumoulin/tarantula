FROM python:3.14.0-slim-bookworm AS base

WORKDIR /var/app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    VIRTUAL_ENV="/opt/pysetup/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

RUN python -m venv $VIRTUAL_ENV && \
    pip install --no-cache-dir poetry==2.2.1

FROM base AS poetry_update

COPY scripts/poetry_update.sh pyproject.toml ./

RUN useradd -ms /bin/bash appuser
USER appuser
ENTRYPOINT ["./poetry_update.sh"]

FROM base AS app

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-cache --only main

COPY log.ini ./
COPY static ./static
COPY templates ./templates
COPY src ./src

RUN useradd -ms /bin/bash appuser
USER appuser
RUN mkdir /tmp/logs
CMD ["python", "-m", "src.entrypoint"]

FROM base AS lint_and_test

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-cache

COPY src ./src
COPY docker-compose.yaml scripts/lint_and_test.sh ./
CMD ["./lint_and_test.sh"]

FROM base AS format

COPY pyproject.toml poetry.lock ./
RUN poetry install --no-root --no-cache

COPY src ./src
COPY scripts/format.sh ./
CMD ["./format.sh"]
