FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
  iputils-ping \
  net-tools \
  curl \
  nano \
  && rm -rf /var/lib/apt/lists/*

CMD ["bash", "-c", "while true; do sleep 1000; done"]
