FROM python:3.11-slim-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.11.32 /uv /uvx /bin/
LABEL Maintainer="Klaas Schoute"

WORKDIR /app
ENV UV_PYTHON_DOWNLOADS=never

RUN apt-get update && apt-get -y install --no-install-recommends cron \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev --no-cache
COPY . /app

COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN /usr/bin/crontab /etc/cron.d/crontab
RUN touch /var/log/cron.log

CMD ["cron", "-f"]
