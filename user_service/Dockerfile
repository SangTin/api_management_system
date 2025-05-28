FROM python:3.11-slim

ARG SERVICE_NAME

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    bash \
    git \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY ./${SERVICE_NAME}/ .
RUN pip install --no-cache-dir -r requirements.txt

COPY ./${SERVICE_NAME}/entrypoint.sh .
RUN chmod +x entrypoint.sh

CMD ["/bin/bash", "./entrypoint.sh"]