FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
  iproute2 \
  iputils-ping \
  net-tools \
  nano \
  tcpdump \
  && rm -rf /var/lib/apt/lists/*

# Instala psutil normalmente
RUN pip install psutil

# Ativa roteamento IP
RUN echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

# Copia o script
COPY roteador.py /app/roteador.py
WORKDIR /app

# Entrar no container com bash
CMD ["python3", "/app/roteador.py"]