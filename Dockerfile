# Dockerfile
FROM python:3.12-slim
WORKDIR /app
ENV HF_HOME=/app/models
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY download_model.py .
RUN python download_model.py
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]