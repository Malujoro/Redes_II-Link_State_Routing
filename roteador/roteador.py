import time

# {
#   "type": "HELLO",          // Tipo do pacote (poderia ser HELLO, LSA, etc.)
#   "router_id": "R1",        // Identificador único do roteador remetente
#   "timestamp": 1714419538,  // Momento em que o pacote foi enviado (em segundos)
#   "interface": "eth0",      // (Opcional) Interface de saída usada
# }

# {
#   "type": "LSA",                    // Tipo do pacote
#   "router_id": "R1",               // Roteador que criou o LSA
#   "sequence_number": 15,          // Número da versão do LSA
#   "timestamp": 1714419538.77,     // Quando o LSA foi gerado
#   "links": [                      // Lista de enlaces conhecidos pelo roteador
#     {"neighbor_id": "R2", "cost": 10},
#     {"neighbor_id": "R3", "cost": 20}
#   ]
# }

# Interface: (família)
#   - 2: IPv4
#   - 10: IPv6
#   - 17: Endereço MAC

# Função para construção do pacote Hello
def build_hello_packet(router_id: str, interface: str = "eth0"):
    return {
        "type": "HELLO",
        "router_id": router_id,
        "timestamp": time.time(),
        "interface": interface,
    }

# Função para construção do pacote LSA
def build_lsa_packet(router_id: str, neighbors: list[tuple[str, int]], sequence_number: int):
    return {
        "type": "LSA",
        "router_id": router_id,
        "timestamp": time.time(),
        "sequence_number": sequence_number,
        "links": [{"neighbor_id": neighbor_id, "cost": cost} for (neighbor_id, cost) in neighbors]
    }


import psutil

def list_interfaces():
    # Obtém informações sobre as interfaces de rede
    interfaces = psutil.net_if_addrs()
    for interface, addresses in interfaces.items():
        print(f"Interface: {interface}")
        for address in addresses:
            print(f"  - {address.family}: {address.address}")

# Exemplo de uso

if(__name__ == "__main__"):
    list_interfaces()
