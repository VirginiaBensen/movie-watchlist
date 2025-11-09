FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends postgresql-client libpq-dev gcc build-essential

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install openai

COPY . .

EXPOSE 5000

CMD ["python3", "app.py"]

