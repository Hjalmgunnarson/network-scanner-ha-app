FROM python:3.11-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y iproute2 iputils-ping

RUN chmod a+x /app/run.sh

CMD ["/app/run.sh"]