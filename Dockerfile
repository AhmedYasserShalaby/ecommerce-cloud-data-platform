FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    COMMERCE_DATA_ROOT=/app/data

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl openjdk-17-jre-headless \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY src ./src
COPY app ./app
COPY config ./config
COPY dbt ./dbt

RUN pip install --no-cache-dir -e ".[dev,spark,dbt,kafka]"

CMD ["commerce-platform", "smoke", "--profile", "ci"]
