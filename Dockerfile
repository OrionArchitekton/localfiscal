FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN pip install --no-cache-dir . \
    && useradd --create-home --uid 10001 appuser \
    && mkdir -p /app/data \
    && chown -R appuser:appuser /app

# Drop root. The container binds 0.0.0.0 (required for port mapping); host-side
# exposure is gated by the compose port mapping (127.0.0.1 by default).
USER appuser
ENV LOCALFISCAL_HOST=0.0.0.0 \
    LOCALFISCAL_DB=/app/data/ledger.db

EXPOSE 8080

CMD ["localfiscal-web"]
