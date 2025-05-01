#!/bin/bash

# Lista de roteadores principais
roteadores=(r1 r2 r3 r4 r5)

# Array associativo: IP → container
declare -A ip_para_container

# Ler o docker-compose.yml para preencher o mapeamento
container=""
while read -r line; do
  if [[ $line =~ ^[[:space:]]*container_name: ]]; then
    container=$(echo "$line" | awk '{print $2}')
  elif [[ $line =~ ^[[:space:]]*ipv4_address: ]]; then
    ip=$(echo "$line" | awk '{print $2}')
    ip_para_container[$ip]=$container
  fi
done < docker-compose.yml

# Lista de IPs dos roteadores (ignora hosts como r1_h1)
ips=()
for ip in "${!ip_para_container[@]}"; do
  container="${ip_para_container[$ip]}"
  if [[ " ${roteadores[@]} " =~ " ${container} " ]]; then
    ips+=("$ip")
  fi
done

# Cabeçalho
echo "Teste de conectividade entre os roteadores:"
echo "==========================================="

# Loop de testes
for origem in "${roteadores[@]}"; do
  echo -e "\n### Pings a partir do $origem ###"
  
  # Exibir tabela de roteamento do roteador
  echo "Tabela de roteamento do $origem:"
  docker exec "$origem" ip route show
  echo "------------------------------"
  
  for destino_ip in "${ips[@]}"; do
    destino_nome="${ip_para_container[$destino_ip]}"
    if [[ "$origem" == "$destino_nome" ]]; then
      continue
    fi
    printf "Pingando %-15s (%-8s)... " "$destino_ip" "$destino_nome"
    docker exec "$origem" ping -c 1 -W 1 "$destino_ip" &> /dev/null && echo "✔️" || echo "❌"
  done
  echo "------------------------------"
done
