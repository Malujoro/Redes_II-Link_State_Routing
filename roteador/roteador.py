import time
import psutil
import socket
import threading
import json
import os

# {
#   "type": "LSA",                    // Tipo do pacote
#   "router_id": "R1",               // Roteador que criou o LSA
#   "sequence_number": 15,          // Número da versão do LSA
#   "timestamp": 1714419538.77,     // Quando o LSA foi gerado
#   "links": [                      // Lista de enlaces conhecidos pelo roteador
#     {"vizinho_id": "R2", "custo": 10},
#     {"vizinho_id": "R3", "custo": 20}
#   ]
# }

# {
#   "type": "HELLO",          // Tipo do pacote (poderia ser HELLO, LSA, etc.)
#   "router_id": "R1",        // Identificador único do roteador remetente
#   "timestamp": 1714419538,  // Momento em que o pacote foi enviado (em segundos)
#   "interface_ip": 10.0.0.1,      // (Opcional) Interface de saída usada
# }


# Função para construção do pacote LSA
def criar_pacote_lsa(router_id: str, neighbors: dict[str, int], sequence_number: int):
    return {
        "type": "LSA",
        "router_id": router_id,
        "timestamp": time.time(),
        "sequence_number": sequence_number,
        "links": [{"vizinho_id": vizinho_id, "custo": custo} for (vizinho_id, custo) in neighbors.items()]
    }


class HelloSender:

    __slots__ = ["_router_id", "_interfaces",
                 "_interval", "_PORTA"]

    def __init__(self, router_id: str, interfaces: list[dict[str: str]], interval: int = 10, PORTA: int = 5000):
        self._router_id = router_id
        self._interfaces = interfaces
        self._interval = interval
        self._PORTA = PORTA

    # Função para construção do pacote Hello
    def criar_pacote(self, ip_address: str):
        return {
            "type": "HELLO",
            "router_id": self._router_id,
            "timestamp": time.time(),
            "ip_address": ip_address,
        }

    def enviar_broadcast(self, ip_address: str, broadcast_ip: str):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while True:
            packet = self.criar_pacote(ip_address)
            message = json.dumps(packet).encode('utf-8')

            try:
                sock.sendto(message, (broadcast_ip, self._PORTA))
                print(
                    f"[{self._router_id}:{ip_address}] Pacote HELLO enviado para {broadcast_ip}:{self._PORTA}")
            except Exception as e:
                print(f"[{self._router_id}:{ip_address}] Erro ao enviar: {e}")

            time.sleep(self._interval)

    def iniciar(self):
        for interface_info in self._interfaces:
            ip_address = interface_info["address"]
            broadcast_ip = interface_info["broadcast"]

            if (broadcast_ip != None):
                thread_emissor = threading.Thread(target=self.enviar_broadcast, args=(
                    ip_address, broadcast_ip), daemon=True)
                thread_emissor.start()

class Roteador:

    __slots__ = ["_router_id", "_interfaces",
                 "_PORTA", "_BUFFER_SIZE", '_vizinhos']

    def __init__(self, router_id: str, interfaces: list[dict[str: str]], PORTA: int = 5000, BUFFER_SIZE: int = 4096):
        self._router_id = router_id
        self._interfaces = interfaces
        self._PORTA = PORTA
        self._BUFFER_SIZE = BUFFER_SIZE
        self._vizinhos = {}

    def receber_pacotes(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Escuta em todas as interfaces
        sock.bind(('', self._PORTA))

        print(f"Receptor HELLO escutando na porta {self._PORTA}...")

        while True:
            try:
                data, addr = sock.recvfrom(self._BUFFER_SIZE)
                mensagem = data.decode('utf-8')
                pacote = json.loads(mensagem)
                received_id = pacote.get("router_id")
                if (pacote.get("type") == "HELLO" and received_id != self._router_id):
                    print(f"Pacote HELLO recebido de {received_id}:{addr[0]}")

                    # print(json.dumps(pacote, indent=4))

                    self._vizinhos[received_id] = get_custo(
                        router_id, received_id)
                    print(f"Vizinhos de [{self._router_id}]: {self._vizinhos}")
            except Exception as e:
                print(f"Erro ao receber pacote: {e}")

    def iniciar(self):
        hello = HelloSender(self._router_id, self._interfaces)
        # self._lsa = LSA(router_id, interfaces)

        thread_receptor = threading.Thread(
            target=self.receber_pacotes, daemon=True)
        thread_receptor.start()

        hello.iniciar()

        while True:
            time.sleep(1)


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


def get_custo(router_id: str, vizinho_id: str):
    custo = os.getenv(f'CUSTO_{router_id}_{vizinho_id}_net')
    if (custo == None):
        custo = os.getenv(f'CUSTO_{vizinho_id}_{router_id}_net')
    return int(custo)


if (__name__ == "__main__"):
    router_id = os.getenv('CONTAINER_NAME')
    if (not router_id):
        raise ValueError(
            "CONTAINER_NAME não definido nas variáveis de ambiente")

    interfaces = listar_enderecos()

    roteador = Roteador(router_id, interfaces)
    roteador.iniciar()
