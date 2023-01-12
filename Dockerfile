FROM python:3.11.1-slim-buster as builder

WORKDIR /app

RUN apt-get update \
    && apt-get -y install libpq-dev gcc \
    && pip install psycopg2

COPY ./requirements.txt .
RUN pip install --upgrade pip
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


#####
# FINAL #
#######
FROM python:3.11.1-slim-buster
WORKDIR /app

RUN apt-get -y update && apt-get install -y libpq-dev  \
    && apt-get -y autoremove

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

COPY . .