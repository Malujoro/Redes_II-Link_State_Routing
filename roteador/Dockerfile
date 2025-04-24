# Dockerfile para ROTEADOR
FROM debian:bookworm-slim

RUN apt-get update && apt-get install -y \
  iproute2 \
  iputils-ping \
  net-tools \
  nano \
  tcpdump \
  && rm -rf /var/lib/apt/lists/*

# Ativa roteamento IP
RUN echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

# Entrar no container com bash
CMD [ "bash" ]
