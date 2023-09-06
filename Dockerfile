FROM python:3.11-slim

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

RUN apt-get update && apt-get upgrade -y
RUN playwright install
RUN playwright install-deps

EXPOSE 5000

ENV NAME World

CMD ["python", "app.py"]
