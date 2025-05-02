#!/bin/bash

# Lista de hosts (todos os containers com _h no nome)
hosts=()

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
    # Se for host (ex: r1_h1), adiciona na lista de hosts
    if [[ "$container" == *_h* ]]; then
      hosts+=("$container")
    fi
  fi
done < docker-compose.yml

# Lista de IPs dos hosts
ips=()
for ip in "${!ip_para_container[@]}"; do
  container="${ip_para_container[$ip]}"
  if [[ " ${hosts[@]} " =~ " ${container} " ]]; then
    ips+=("$ip")
  fi
done

# Cabeçalho
echo "Teste de conectividade entre os hosts:"
echo "======================================="

# Loop de testes
for origem in "${hosts[@]}"; do
  echo -e "\n### Pings a partir do $origem ###"

  for destino_ip in "${ips[@]}"; do
    destino_nome="${ip_para_container[$destino_ip]}"
    # Ignora o próprio host
    if [[ "$origem" == "$destino_nome" ]]; then
      continue
    fi
    printf "Pingando %-15s (%-8s)... " "$destino_ip" "$destino_nome"
    docker exec "$origem" ping -c 1 -W 1 "$destino_ip" &> /dev/null && echo "✔️" || echo "❌"
  done
  echo "------------------------------"
done
