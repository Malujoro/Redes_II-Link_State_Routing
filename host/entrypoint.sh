#!/bin/bash

# Descobre o IP local do container (da interface padrão)
IP=$(ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}')

# Extrai os 3 primeiros octetos e adiciona .2 como gateway
GATEWAY=$(echo "$IP" | awk -F. '{print $1"."$2"."$3".2"}')

# Aplica o novo gateway
ip route del default 2>/dev/null
ip route add default via "$GATEWAY"

echo "Gateway padrão configurado para $GATEWAY"

# Mantém o container vivo
while true; do sleep 1000; done