FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY kubesleuth_agent ./kubesleuth_agent
USER 10001
EXPOSE 8080
ENTRYPOINT ["uvicorn", "kubesleuth_agent.server:app", "--host", "0.0.0.0", "--port", "8080"]
