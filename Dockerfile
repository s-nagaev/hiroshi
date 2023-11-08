FROM python:3.11-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
  gcc \
  build-essential \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

FROM python:3.11-slim

LABEL org.label-schema.schema-version = "1.0"
LABEL org.label-schema.name = "hiroshi"
LABEL org.label-schema.vendor = "nagaev.sv@gmail.com"
LABEL org.label-schema.vcs-url = "https://github.com/s-nagaev/hiroshi"

ENV PYTHONUNBUFFERED 1

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

WORKDIR /app

COPY . .

RUN groupadd hiroshi && useradd -g hiroshi hiroshi
RUN chown hiroshi:hiroshi /app/data
USER hiroshi

ENTRYPOINT []
CMD python main.py
