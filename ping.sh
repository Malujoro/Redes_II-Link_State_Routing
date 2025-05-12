#!/bin/bash

# Cria um vetor associativo com a estrutura ip -> container
declare -A ip_para_container

# Cria um dicionário responsável por verificar se um roteador já foi adicionado (evitando duplicatas)
declare -A roteadores_map
# Cria uma lista ordenada de roteadores
roteadores=()

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

    # Adiciona apenas roteadores que não foram adicionados
    if [[ "$container" =~ ^r[0-9]+$ ]] && [[ -z "${roteadores_map[$container]}" ]]; then
      roteadores+=("$container")
      roteadores_map[$container]=1
    fi
  fi
done < docker-compose.yml

# Coleta todos os ips encontrados
ips=("${!ip_para_container[@]}")

# Imprime cabeçalho
echo "Teste de conectividade entre os roteadores:"
echo "==========================================="

# Loop de testes de ping
for origem in "${roteadores[@]}"; do
  echo -e "\n### Pings a partir do $origem ###"
  for destino_ip in "${ips[@]}"; do
    destino_nome="${ip_para_container[$destino_ip]}"
    # Não testa o próprio IP
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
echo -e "\nResumo:"
echo "Total de testes: $total"
echo "Sucesso: $success"
echo "Falha: $fail"

if ((total > 0)); then
  perda=$((100 * fail / total))
  echo "Perda: $perda%"
else
  echo "Perda: N/A"
fi