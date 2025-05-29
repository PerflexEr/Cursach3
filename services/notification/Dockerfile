FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ /app/shared/
COPY services/notification/ /app/services/notification/
COPY services/auth/ /app/services/auth/

CMD ["uvicorn", "services.notification.main:app", "--host", "0.0.0.0", "--port", "8003"]