# Backend image — AWS ECR Public only (ADR-004, no Docker Hub)
# Dev: podman-compose monta ./backend sobre /app y activa --reload.
FROM public.ecr.aws/docker/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# Wait for PostgreSQL, then serve with hot-reload for local development.
CMD ["sh", "-c", "python wait_for_db.py && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]
