FROM python:3.13-alpine

LABEL maintainer="David Dami"

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY api-poll-main-v4.py ./

CMD ["python", "api-poll-main-v4.py"]