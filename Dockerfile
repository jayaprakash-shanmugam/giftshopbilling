# Dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
COPY invoice_app.py .

RUN pip install -r requirements.txt

EXPOSE 8501

# Use host.docker.internal to connect to host machine's MongoDB
ENV MONGO_URI="mongodb://host.docker.internal:27017/"

CMD ["streamlit", "run", "invoice_app.py", "--server.address", "0.0.0.0"]