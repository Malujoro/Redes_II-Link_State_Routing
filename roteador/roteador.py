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
#     {"neighbor_id": "R2", "custo": 10},
#     {"neighbor_id": "R3", "custo": 20}
#   ]
# }

# {
#   "type": "HELLO",          // Tipo do pacote (poderia ser HELLO, LSA, etc.)
#   "router_id": "R1",        // Identificador único do roteador remetente
#   "timestamp": 1714419538,  // Momento em que o pacote foi enviado (em segundos)
#   "interface_ip": 10.0.0.1,      // (Opcional) Interface de saída usada
# }


class HelloSender:

    __slots__ = ["_router_id", "_interfaces",
                 "_neighbors", "_interval", "_PORTA"]

    def __init__(self, router_id: str, interfaces: list[dict[str: str]], neighbors: dict[str: str], interval: int = 10, PORTA: int = 5000):
        self._router_id = router_id
        self._interfaces = interfaces
        self._neighbors = neighbors
        self._interval = interval
        self._PORTA = PORTA

    # Função para construção do pacote Hello
    def criar_pacote(self, ip_address: str):
        return {
            "type": "HELLO",
            "router_id": self._router_id,
            "timestamp": time.time(),
            "ip_address": ip_address,
            "known_neighbors": list(self._neighbors.keys()),
        }

    def enviar_broadcast(self, ip_address: str, broadcast_ip: str):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while True:
            pacote = self.criar_pacote(ip_address)
            message = json.dumps(pacote).encode("utf-8")

            try:
                sock.sendto(message, (broadcast_ip, self._PORTA))
                print(
                    f"[{self._router_id}] Pacote HELLO enviado para {broadcast_ip}")
            except Exception as e:
                print(f"[{self._router_id}] Erro ao enviar: {e}")

            time.sleep(self._interval)

    def iniciar(self):
        for interface_info in self._interfaces:
            ip_address = interface_info["address"]
            broadcast_ip = interface_info["broadcast"]

            if (broadcast_ip != None):
                thread_emissor = threading.Thread(target=self.enviar_broadcast, args=(
                    ip_address, broadcast_ip), daemon=True)
                thread_emissor.start()

class LSASender:

    __slots__ = ["_router_id", "_neighbors_ip", "_neighbors_cost",
                 "_interval", "_PORTA", "_sequence_number", "_iniciado"]

    def __init__(self, router_id: str, neighbors_ip: dict[str: str], neighbors_cost: dict[str: int], interval: int = 30, PORTA: int = 5000):
        self._router_id = router_id
        self._neighbors_ip = neighbors_ip
        self._neighbors_cost = neighbors_cost
        self._interval = interval
        self._PORTA = PORTA
        self._sequence_number = 0
        self._iniciado = False

    @property
    def router_id(self):
        return self._router_id

    @property
    def neighbors_ip(self):
        return self._neighbors_ip

    @property
    def neighbors_cost(self):
        return self._neighbors_cost

    # Função para construção do pacote LSA
    def criar_pacote(self):
        self._sequence_number += 1
        return {
            "type": "LSA",
            "router_id": self._router_id,
            "timestamp": time.time(),
            "sequence_number": self._sequence_number,
            "links": [{"neighbor_id": neighbor_id, "custo": custo} for (neighbor_id, custo) in self._neighbors_cost.items()]
        }

    def enviar_para_vizinhos(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        while True:
            pacote = self.criar_pacote()
            message = json.dumps(pacote).encode("utf-8")

            for ip in self._neighbors_ip.values():
                try:
                    sock.sendto(message, (ip, self._PORTA))
                    print(
                        f"[{self._router_id}] Pacote LSA enviado para {ip}")
                except Exception as e:
                    print(f"[{self._router_id}] Erro ao enviar: {e}")

            time.sleep(self._interval)

    def iniciar(self):
        if (not self._iniciado):
            self._iniciado = True
            thread_emissor = threading.Thread(
                target=self.enviar_para_vizinhos, daemon=True)
            thread_emissor.start()


class Roteador:

    __slots__ = ["_router_id", "_interfaces", "_PORTA", "_lsa", "_BUFFER_SIZE",
                 "_neighbors_detected", "_neighbors_recognized", "_gerenciador_vizinhos"]

    def __init__(self, router_id: str, interfaces: list[dict[str: str]], PORTA: int = 5000, BUFFER_SIZE: int = 4096):
        self._router_id = router_id
        self._interfaces = interfaces
        self._PORTA = PORTA
        self._BUFFER_SIZE = BUFFER_SIZE
        self._neighbors_detected = {}
        self._neighbors_recognized = {}
        self._lsa = LSASender(
            self._router_id, self._neighbors_recognized, self._neighbors_detected)
        self._gerenciador_vizinhos = GerenciadorVizinhos(
            self._router_id, self._lsa)

    def receber_pacotes(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # Escuta em todas as interfaces
        sock.bind(("", self._PORTA))

        print(f"Receptor escutando na porta {self._PORTA}")

        while True:
            try:
                data, address = sock.recvfrom(self._BUFFER_SIZE)
                mensagem = data.decode("utf-8")
                pacote = json.loads(mensagem)
                tipo_pacote = pacote.get("type")
                received_id = pacote.get("router_id")
                if (received_id != self._router_id):
                    received_ip = address[0]
                    print(
                        f"Pacote {tipo_pacote} recebido de [{received_id}] {received_ip}")

                    if (tipo_pacote == "HELLO"):
                        self._gerenciador_vizinhos.processar_hello(
                            pacote, received_ip)
                    elif (tipo_pacote == "LSA"):
                        print(json.dumps(pacote, indent=4))
            except Exception as e:
                print(f"Erro ao receber pacote: {e}")

    def iniciar(self):
        hello = HelloSender(self._router_id, self._interfaces,
                            self._neighbors_detected)

        thread_receptor = threading.Thread(
            target=self.receber_pacotes, daemon=True)
        thread_receptor.start()

        hello.iniciar()

        while True:
            time.sleep(1)


class GerenciadorVizinhos:

    __slots__ = ["_router_id", "_lsa", "_neighbors_detected", "_neighbors_recognized"]

    def __init__(self, router_id: str, lsa_sender: LSASender):
        self._router_id = router_id
        self._lsa = lsa_sender
        self._neighbors_detected = lsa_sender.neighbors_cost
        self._neighbors_recognized = lsa_sender.neighbors_ip

    def processar_hello(self, pacote: dict, received_ip: str):
        received_id = pacote.get("router_id")
        self._neighbors_detected[received_id] = self.get_custo(
            self._router_id, received_id)
        neighbors = pacote.get("known_neighbors")
        print(
            f"neighbors de [{self._router_id}]: {self._neighbors_detected}")
        print(
            f"neighbors de [{received_id}]: {neighbors}")

        if ((router_id in neighbors) and (received_id not in self._neighbors_recognized.keys())):
            self._neighbors_recognized[received_id] = received_ip
            print(
                f"recognized neighbors de [{router_id}]: {self._neighbors_recognized}")
            self._lsa.iniciar()

    def get_custo(self, router_id: str, neighbor_id: str):
        custo = os.getenv(f"CUSTO_{router_id}_{neighbor_id}_net")
        if (custo == None):
            custo = os.getenv(f"CUSTO_{neighbor_id}_{router_id}_net")
        return int(custo)


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


if (__name__ == "__main__"):
    router_id = os.getenv("CONTAINER_NAME")
    if (not router_id):
        raise ValueError(
            "CONTAINER_NAME não definido nas variáveis de ambiente")

    interfaces = listar_enderecos()

    roteador = Roteador(router_id, interfaces)
    roteador.iniciar()
