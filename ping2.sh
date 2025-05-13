#!/bin/bash

# Lista de hosts
hosts=()

# Cria um vetor associativo com a estrutura ip -> container
declare -A ip_para_container

# Contadores de sucesso e falha
success=0
fail=0

# Leitura do docker-compose
while read -r line; do
  if [[ $line == *"container_name:"* ]]; then
    container=$(echo $line | awk '{print $2}')
  fi
  if [[ $line == *"ipv4_address:"* ]]; then
    ip=$(echo $line | awk '{print $2}')
    ip_para_container[$ip]=$container

    # Adiciona os hosts
    if [[ "$container" == *_h* ]]; then
      hosts+=("$container")
    fi
  fi
done < docker-compose.yml

# Adiciona os hosts
ips=()
for ip in "${!ip_para_container[@]}"; do
  container="${ip_para_container[$ip]}"
  if [[ " ${hosts[@]} " =~ " ${container} " ]]; then
    ips+=("$ip")
  fi
done

# Imprime cabeçalho
echo "Teste de conectividade entre os hosts:"
echo "======================================="

# Loop de testes de ping
for origem in "${hosts[@]}"; do
  echo -e "\n### Pings a partir do $origem ###"

  for destino_ip in "${ips[@]}"; do
    destino_nome="${ip_para_container[$destino_ip]}"
    # Ignora o próprio host
    if [[ "$origem" == "$destino_nome" ]]; then
      continue
    fi
    printf "Pingando %-15s (%-8s)... " "$destino_ip" "$destino_nome"
    if docker exec "$origem" ping -c 1 -W 1 "$destino_ip" &> /dev/null; then
      echo "✔️"
      ((success++))
    else
      echo "❌"
      ((fail++))
    fi
  done
  echo "------------------------------"
done

# Calculo das estatísticas
total=$((success + fail))
echo -e "\nResumo (Hosts):"
echo "Total de testes: $total"
echo "Sucesso: $success"
echo "Falha: $fail"

if ((total > 0)); then
  perda=$((100 * fail / total))
  echo "Perda: $perda%"
else
  echo "Perda: N/A"
fi