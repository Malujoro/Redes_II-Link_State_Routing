# Dockerfile para HOST
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
  iputils-ping \
  net-tools \
  curl \
  nano \
  && rm -rf /var/lib/apt/lists/*

CMD [ "bash" ]
