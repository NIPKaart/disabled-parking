# BASE IMAGE
FROM python:3.10-slim-buster
LABEL Maintainer="Klaas Schoute"

COPY . /app
WORKDIR /app

# Install requirements
RUN apt-get update && apt-get -y install cron

# Install poetry and dependencies
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --with cities --without dev

# Add crontab file in the cron directory
COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN /usr/bin/crontab /etc/cron.d/crontab

RUN touch /var/log/cron.log

CMD ["cron", "-f"]
