FROM debian:bookworm-slim

# Instalação de utilitários que serão úteis para gerenciamento da rede, limpando o cache no final
RUN apt-get update && apt-get install -y \
  iproute2 \
  iputils-ping \
  net-tools \
  nano \
  curl \
  traceroute \
  && rm -rf /var/lib/apt/lists/*

# Copia o script para a raiz do container
COPY entrypoint.sh /entrypoint.sh
# Modifica as permissões, garantindo que o script seja executável
RUN chmod +x /entrypoint.sh

# Executa o script ao iniciar o container
CMD ["/entrypoint.sh"]