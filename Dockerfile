FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure Python can find the modules
ENV PYTHONPATH=/app

CMD ["python", "-m", "src.main"]