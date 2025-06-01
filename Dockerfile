FROM python:3.12-slim AS builder
LABEL org.opencontainers.image.authors="Michał Małysz"
LABEL org.opencontainers.image.title="Zadanko 1 - Apka pogodowa"
LABEL org.opencontainers.image.source="https://github.com/nightxpl01"

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=builder /usr/local/bin /usr/local/bin

COPY . /app

ENV FLASK_APP=zad1.py
ENV FLASK_RUN_PORT=8069
ENV PORT=8069
EXPOSE 8069

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3  CMD curl --fail http://localhost:8069 || exit 1

CMD ["python", "zad1.py"]