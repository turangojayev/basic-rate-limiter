FROM python:3.9-slim-buster
WORKDIR /app
COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY src /tmp/app/src
COPY tests /tmp/app/tests
COPY pyproject.toml /tmp/app/pyproject.toml

RUN pytest -v /tmp/app/tests && rm -rf /tmp/app

COPY proxy_server.py /app/proxy_server.py

EXPOSE 8080
CMD ["uvicorn", "proxy_server:app", "--reload", "--host", "0.0.0.0", "--port", "8080"]