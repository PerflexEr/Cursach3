FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY services/monitoring/ /app/services/monitoring/
COPY services/auth/ /app/services/auth/
COPY services/hive/ /app/services/hive/

CMD ["uvicorn", "services.monitoring.main:app", "--host", "0.0.0.0", "--port", "8000"]