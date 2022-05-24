# BASE IMAGE
FROM python:3.10-slim-buster
LABEL Maintainer="Klaas Schoute"

ENV TZ=Europe/Amsterdam

COPY . /app
WORKDIR /app

# Install requirements
RUN apt-get update && apt-get -y install cron tzdata
# Set the timezone
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
RUN pip install -r requirements.txt

COPY crontab /etc/cron.d/crontab
RUN chmod 0644 /etc/cron.d/crontab
RUN /usr/bin/crontab /etc/cron.d/crontab

RUN touch /var/log/cron.log

CMD ["cron", "-f"]