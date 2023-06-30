FROM python:3.10.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip3 install -r requirements.txt --no-cache-dir
COPY .env .
COPY *.py /app/
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
