#!/bin/bash

# Lista de roteadores
roteadores=(r1 r2 r3 r4 r5)

# Array associativo: IP → container
declare -A ip_para_container

# Preencher o mapeamento IP → container a partir do docker-compose.yml
while read -r line; do
  if [[ $line == *"container_name:"* ]]; then
    container=$(echo $line | awk '{print $2}')
  fi
  if [[ $line == *"ipv4_address:"* ]]; then
    ip=$(echo $line | awk '{print $2}')
    ip_para_container[$ip]=$container
  fi
done < docker-compose.yml

# Lista de IPs
ips=("${!ip_para_container[@]}")

# Cabeçalho
echo "Teste de conectividade entre os roteadores:"
echo "==========================================="

# Loop de testes
for origem in "${roteadores[@]}"; do
  echo -e "\n### Pings a partir do $origem ###"
  for destino_ip in "${ips[@]}"; do
    destino_nome="${ip_para_container[$destino_ip]}"
    # Não testa o próprio IP
    if [[ "$origem" == "$destino_nome" ]]; then
      continue
    fi
    printf "Pingando %-15s (%-8s)... " "$destino_ip" "$destino_nome"
    docker exec "$origem" ping -c 1 -W 1 "$destino_ip" &> /dev/null && echo "✔️" || echo "❌"
  done
  echo "------------------------------"
done
