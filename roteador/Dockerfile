FROM python:3.12-slim

# Instalação de utilitários que serão úteis para gerenciamento da rede, limpando o cache no final
RUN apt-get update && apt-get install -y \
  iproute2 \
  iputils-ping \
  net-tools \
  nano \
  tcpdump \
  traceroute \
  && rm -rf /var/lib/apt/lists/*

# Instala o psutil (biblioteca que acessa as informações do sistema)
RUN pip install psutil

# Ativa o encaminhamento de pacotes IPv4 >> Aplica as alterações feitas
RUN echo "net.ipv4.ip_forward=1" >> /etc/sysctl.conf

# Copia o script para o diretório /app
COPY roteador.py /app/roteador.py
# Define /app como o diretório de trabalho
WORKDIR /app

# Executa o script ao iniciar o container
CMD ["python3", "-u", "/app/roteador.py"]