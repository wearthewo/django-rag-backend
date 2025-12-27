# ---------- builder ----------
FROM python:3.14-slim AS builder

WORKDIR /wheels

RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip \
    && pip wheel --no-cache-dir --no-deps -r requirements.txt


# ---------- runtime ----------
FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache-dir /wheels/*

COPY backend/ backend/

EXPOSE 8000

CMD ["uvicorn", "backend.config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
