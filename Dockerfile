FROM python:3.10.12-slim
RUN python -m pip install --upgrade pip

COPY requirements.txt /tmp/
RUN pip install -r /tmp/requirements.txt
COPY .env .
RUN mkdir -p /src
COPY src /src
RUN pip install -e /src
COPY tests /tests

WORKDIR /src/allocation/app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]