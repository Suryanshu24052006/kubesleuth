FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY kubesleuth_broker ./kubesleuth_broker
USER 10001
EXPOSE 8090
ENTRYPOINT ["python", "-m", "kubesleuth_broker.server"]
