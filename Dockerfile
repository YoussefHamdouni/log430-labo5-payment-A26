FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copier tout le dépôt dans /app (le code se retrouve dans /app/src),
# comme le montage de volume .:/app de docker-compose.yml
COPY . .

WORKDIR /app/src

EXPOSE 5009
CMD ["python", "payments_api.py"]
