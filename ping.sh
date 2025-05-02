#!/bin/bash

# Array associativo: IP → container
declare -A ip_para_container

# Conjunto de roteadores (usando outra estrutura para evitar duplicatas)
declare -A roteadores_map
roteadores=()

# Preencher o mapeamento IP → container a partir do docker-compose.yml
while read -r line; do
  if [[ $line == *"container_name:"* ]]; then
    container=$(echo $line | awk '{print $2}')
  fi
  if [[ $line == *"ipv4_address:"* ]]; then
    ip=$(echo $line | awk '{print $2}')
    ip_para_container[$ip]=$container

    # Adiciona apenas se for roteador e ainda não tiver sido adicionado
    if [[ "$container" =~ ^r[0-9]+$ ]] && [[ -z "${roteadores_map[$container]}" ]]; then
      roteadores+=("$container")
      roteadores_map[$container]=1
    fi
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
