FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

ENV PYTHONDONTWRITEBYTECODE 1

ENV PYTHONUNBUFFERED 1

CMD ["streamlit", "run", "invoice_app.py", "--server.address", "0.0.0.0", "--server.baseUrlPath", "svm", "--server.enableCORS", "false", "--server.enableXsrfProtection", "false"]
