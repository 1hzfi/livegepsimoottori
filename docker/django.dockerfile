FROM python:3.14 AS builder

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

ENV PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1


RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends g++ gcc libjpeg-dev zlib1g-dev libwebp-dev libmagic-dev libpq5

RUN curl https://sh.rustup.rs -sSf | sh -s -- -y

RUN uv venv /opt/venv
ENV VIRTUAL_ENV="/opt/venv/" \
    PATH="/opt/venv/bin:/root/.cargo/bin:$PATH"

RUN . /opt/venv/bin/activate

COPY requirements.txt .

RUN uv pip install -r requirements.txt

RUN find /opt/venv -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null; \
    find /opt/venv -name "*.pyc" -delete 2>/dev/null; \
    find /opt/venv -name "*.pyo" -delete 2>/dev/null; \
    true

# final stage
FROM python:3.14-slim AS final

RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends libglib2.0-0 libmagic1 && \
    apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /usr/share/doc /usr/share/man

COPY --from=builder /opt/venv /opt/venv

ENV VIRTUAL_ENV="/opt/venv/"
ENV PATH="/opt/venv/bin:$PATH"
ENV LD_LIBRARY_PATH="/usr/local/lib"

WORKDIR /app

COPY .env.dev ./.env
ADD . /app/

EXPOSE 8000
EXPOSE 2000

ENV DJANGO_SETTINGS_MODULE=routechoices.settings
