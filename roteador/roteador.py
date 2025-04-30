import time
import psutil
import socket
import threading
import json
import os

PORTA = 5000
BUFFER_SIZE = 4096

# {
#   "type": "HELLO",          // Tipo do pacote (poderia ser HELLO, LSA, etc.)
#   "router_id": "R1",        // Identificador único do roteador remetente
#   "timestamp": 1714419538,  // Momento em que o pacote foi enviado (em segundos)
#   "interface_ip": 10.0.0.1,      // (Opcional) Interface de saída usada
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
def criar_pacote_hello(router_id: str, ip_address: str):
    return {
        "type": "HELLO",
        "router_id": router_id,
        "timestamp": time.time(),
        "ip_address": ip_address,
    }

# Função para construção do pacote LSA
def criar_pacote_lsa(router_id: str, neighbors: list[tuple[str, int]], sequence_number: int):
    return {
        "type": "LSA",
        "router_id": router_id,
        "timestamp": time.time(),
        "sequence_number": sequence_number,
        "links": [{"neighbor_id": neighbor_id, "cost": cost} for (neighbor_id, cost) in neighbors]
    }


def listar_enderecos():
    interfaces = psutil.net_if_addrs()
    interfaces_list = []
    for interface, addresses in interfaces.items():
        if (interface.startswith("eth")):
            for address in addresses:
                if (address.family == socket.AF_INET):
                    interfaces_list.append(
                        {"address": address.address,
                         "broadcast": address.broadcast}
                    )
    return interfaces_list


def enviar_hello_broadcast(router_id: str, ip_address: str, broadcast_ip: str, interval: int = 10):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    while True:
        packet = criar_pacote_hello(router_id, ip_address)
        message = json.dumps(packet).encode('utf-8')

        try:
            sock.sendto(message, (broadcast_ip, PORTA))
            print(
                f"[{router_id}:{ip_address}] Pacote HELLO enviado para {broadcast_ip}:{PORTA}")
        except Exception as e:
            print(f"[{router_id}:{ip_address}] Erro ao enviar: {e}")

        time.sleep(interval)

def receber_hello(router_id: str):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Escuta em todas as interfaces
    sock.bind(('', PORTA))

    print(f"Receptor HELLO escutando na porta {PORTA}...")

    while True:
        try:
            data, addr = sock.recvfrom(BUFFER_SIZE)
            mensagem = data.decode('utf-8')
            pacote = json.loads(mensagem)
            received_id = pacote.get("router_id")
            if (pacote.get("type") == "HELLO" and received_id != router_id):
                print(f"\nPacote HELLO recebido de {received_id}:{addr[0]}")
                print(json.dumps(pacote, indent=4))
        except Exception as e:
            print(f"Erro ao receber pacote: {e}")


if (__name__ == "__main__"):
    router_id = os.getenv('CONTAINER_NAME')
    interfaces = listar_enderecos()

    # Iniciar receptor em thread
    thread_receptor = threading.Thread(
        target=receber_hello, args=(router_id,), daemon=True)
    thread_receptor.start()

    for dicio in interfaces:
        ip_address = dicio["address"]
        broadcast_ip = dicio["broadcast"]

        if (broadcast_ip != None):
            thread = threading.Thread(target=enviar_hello_broadcast, args=(
                router_id, ip_address, broadcast_ip), daemon=True)
            thread.start()

    while True:
        time.sleep(1)
