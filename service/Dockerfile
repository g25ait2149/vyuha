# Vyuha service image.  Build from the repo root:  docker build -f service/Dockerfile -t vyuha .
FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN pip install --no-cache-dir -e ".[serve]"
EXPOSE 8000
CMD ["uvicorn", "service.app:app", "--host", "0.0.0.0", "--port", "8000"]
