import time
import psutil
import socket
import threading
import json
import os
import subprocess
import ipaddress

class LSDB:

    __slots__ = ["_tabela", "_router_id", "_roteamento", "_neighbors_ip"]

    def __init__(self, router_id: str, neighbors_ip: dict[str: str]):
        self._router_id = router_id
        self._tabela = {}
        self._roteamento = {}
        self._neighbors_ip = neighbors_ip

    def criar_entrada(self, sequence_number, timestamp, addresses, links):
        return {
            "sequence_number": sequence_number,
            "timestamp": timestamp,
            "addresses": addresses,
            "links": links,
        }

    def atualizar(self, pacote):
        router_id = pacote["router_id"]
        sequence_number = pacote["sequence_number"]

        entrada = self._tabela.get(router_id)

        if (entrada and sequence_number <= entrada["sequence_number"]):
            return False

        self._tabela[pacote["router_id"]] = self.criar_entrada(
            sequence_number, pacote["timestamp"], pacote["addresses"], pacote["links"])

        for vizinho in pacote["links"].keys():
            if (vizinho not in self._tabela):
                print(f"[LSDB] Descoberto novo roteador: {vizinho}")
                self._tabela[vizinho] = self.criar_entrada(-1, 0, [], {})

        caminhos = self.dijkstra()
        self.atualizar_proximo_pulo(caminhos)
        self.atualizar_rotas()
        return True

    def dijkstra(self):
        distancias = {}
        caminhos = {}
        marcados = {}

        # Inicializando os dicionários
        for roteador in self._tabela.keys():
            distancias[roteador] = float('inf')
            caminhos[roteador] = None

        distancias[self._router_id] = 0

        while len(marcados) < len(self._tabela):
            roteador = None
            menor = float('inf')
            # Busca pelo menor roteador não marcado
            for no, custo in distancias.items():
                if (no not in marcados and custo < menor):
                    roteador = no
                    menor = custo

            if (roteador is None):
                break

            marcados[roteador] = True
            vizinhos = self._tabela[roteador]["links"]

            # Atualização dos menores caminhos
            for vizinho, custo in vizinhos.items():
                if (vizinho not in marcados):
                    custo_total = custo + distancias[roteador]
                    if (custo_total < distancias[vizinho]):
                        distancias[vizinho] = custo_total
                        caminhos[vizinho] = roteador

        return caminhos

    def atualizar_proximo_pulo(self, caminhos: dict):
        for destino in caminhos.keys():
            if (destino != self._router_id):
                pulo = destino
                while (pulo is not None and caminhos[pulo] != self._router_id):
                    pulo = caminhos[pulo]
                self._roteamento[destino] = pulo

        self._roteamento = dict(sorted(self._roteamento.items()))

    def atualizar_rotas(self):
        for roteador_destino, roteador_gateway in list(self._roteamento.items()):
            if (roteador_destino != self._router_id):
                if (roteador_gateway not in self._neighbors_ip):
                    print(
                        f"[LSDB] Ignorando rota para {roteador_destino} via {roteador_gateway}: gateway não conhecido ainda")
                else:
                    for ip_destino in self._tabela[roteador_destino]["addresses"]:
                        ip_gateway = self._neighbors_ip[roteador_gateway]

                        comando = ["ip", "route", "replace",
                                   ip_destino, "via", ip_gateway]
                        try:
                            subprocess.run(comando, check=True)
                            print(
                                f"Rota adicionada: {ip_destino} -> {ip_gateway}")
                        except subprocess.CalledProcessError as e:
                            print(
                                f"[ERRO] Falha ao adicionar rota: [{comando}] -> [{e}]")

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
        sock = create_socket()
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
        interfaces = [
            item for item in self._interfaces if "broadcast" in item]
        print(interfaces)
        for interface_info in interfaces:
            ip_address = interface_info["address"]
            broadcast_ip = interface_info["broadcast"]

            if (broadcast_ip != None):
                thread_emissor = threading.Thread(target=self.enviar_broadcast, args=(
                    ip_address, broadcast_ip), daemon=True)
                thread_emissor.start()

class LSASender:

    __slots__ = ["_router_id", "_neighbors_ip", "_neighbors_cost",
                 "_interval", "_PORTA", "_sequence_number", "_iniciado", "_lsdb", "_interfaces"]

    def __init__(self, router_id: str, neighbors_ip: dict[str: str], neighbors_cost: dict[str: int], interfaces: list[dict[str: str]], lsdb: LSDB, interval: int = 30, PORTA: int = 5000):
        self._router_id = router_id
        self._neighbors_ip = neighbors_ip
        self._neighbors_cost = neighbors_cost
        self._interval = interval
        self._PORTA = PORTA
        self._sequence_number = 0
        self._iniciado = False
        self._lsdb = lsdb
        self._interfaces = interfaces

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
            "addresses": [item["address"] for item in self._interfaces],
            "sequence_number": self._sequence_number,
            "links": {neighbor_id: custo for (neighbor_id, custo) in self._neighbors_cost.items()}
        }

    def enviar_para_vizinhos(self):
        sock = create_socket()
        while True:
            pacote = self.criar_pacote()
            self._lsdb.atualizar(pacote)
            message = json.dumps(pacote).encode("utf-8")

            for ip in self._neighbors_ip.values():
                try:
                    sock.sendto(message, (ip, self._PORTA))
                    print(
                        f"[{self._router_id}] Pacote LSA enviado para {ip}")
                except Exception as e:
                    print(f"[{self._router_id}] Erro ao enviar: {e}")

            time.sleep(self._interval)

    def encaminhar_para_vizinhos(self, pacote: dict, neighbor_ip: str):
        sock = create_socket()
        message = json.dumps(pacote).encode("utf-8")

        neighbors_list = [
            ip for ip in self._neighbors_ip.values() if ip != neighbor_ip]

        for ip in neighbors_list:
            try:
                sock.sendto(message, (ip, self._PORTA))
                print(
                    f"[{self._router_id}] Pacote LSA encaminhado para {ip}")
            except Exception as e:
                print(f"[{self._router_id}] Erro ao encaminhar: {e}")

    def iniciar(self):
        if (not self._iniciado):
            self._iniciado = True
            thread_emissor = threading.Thread(
                target=self.enviar_para_vizinhos, daemon=True)
            thread_emissor.start()


class Roteador:

    __slots__ = ["_router_id", "_interfaces", "_PORTA", "_lsa", "_lsdb", "_BUFFER_SIZE",
                 "_neighbors_detected", "_neighbors_recognized", "_gerenciador_vizinhos"]

    def __init__(self, router_id: str, PORTA: int = 5000, BUFFER_SIZE: int = 4096):
        self._router_id = router_id
        self._interfaces = self.listar_enderecos()
        self._PORTA = PORTA
        self._BUFFER_SIZE = BUFFER_SIZE
        self._neighbors_detected = {}
        self._neighbors_recognized = {}
        self._lsdb = LSDB(router_id, self._neighbors_recognized)
        self._lsa = LSASender(
            self._router_id, self._neighbors_recognized, self._neighbors_detected, self._interfaces, self._lsdb)
        self._gerenciador_vizinhos = GerenciadorVizinhos(
            self._router_id, self._lsa, self._lsdb)

    def receber_pacotes(self):
        sock = create_socket()
        # Escuta em todas as interfaces
        sock.bind(("", self._PORTA))

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
                        self._gerenciador_vizinhos.processar_lsa(
                            pacote, received_ip)

            except Exception as e:
                print(f"Erro ao receber pacote: {e}")

    def listar_enderecos(self):
        interfaces = psutil.net_if_addrs()
        interfaces_list = []
        for interface, addresses in interfaces.items():
            if (interface.startswith("eth")):
                for address in addresses:
                    if (address.family == socket.AF_INET):
                        if (address.address.startswith("192")):
                            ip = ipaddress.ip_address(address.address)
                            rede = ipaddress.IPv4Network(
                                f"{ip}/24", strict=False)
                            
                            interfaces_list.append(
                                {"address": f"{rede.network_address}/24"})
                        else:
                            interfaces_list.append(
                                {"address": address.address,
                                 "broadcast": address.broadcast}
                            )
        return interfaces_list

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

    __slots__ = ["_router_id", "_lsa", "_lsdb",
                 "_neighbors_detected", "_neighbors_recognized"]

    def __init__(self, router_id: str, lsa: LSASender, lsdb: LSDB):
        self._router_id = router_id
        self._lsa = lsa
        self._lsdb = lsdb
        self._neighbors_detected = lsa.neighbors_cost
        self._neighbors_recognized = lsa.neighbors_ip

    def processar_hello(self, pacote: dict, received_ip: str):
        received_id = pacote.get("router_id")
        self._neighbors_detected[received_id] = self.get_custo(
            self._router_id, received_id)
        neighbors = pacote.get("known_neighbors")

        # print(
        #     f"neighbors de [{self._router_id}]: {self._neighbors_detected}")
        # print(
        #     f"neighbors de [{received_id}]: {neighbors}")

        if ((self._router_id in neighbors) and (received_id not in self._neighbors_recognized)):
            self._neighbors_recognized[received_id] = received_ip
            # print(
            #     f"recognized neighbors de [{router_id}]: {self._neighbors_recognized}")
            self._lsa.iniciar()

    def processar_lsa(self, pacote: dict, received_ip: str):
        pacote_valido = self._lsdb.atualizar(pacote)
        if (pacote_valido):
            self._lsa.encaminhar_para_vizinhos(pacote, received_ip)
        pass

    def get_custo(self, router_id: str, neighbor_id: str):
        custo = os.getenv(f"CUSTO_{router_id}_{neighbor_id}_net")
        if (custo == None):
            custo = os.getenv(f"CUSTO_{neighbor_id}_{router_id}_net")
        return int(custo)

def create_socket():
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


if (__name__ == "__main__"):
    router_id = os.getenv("CONTAINER_NAME")
    if (not router_id):
        raise ValueError(
            "CONTAINER_NAME não definido nas variáveis de ambiente")

    roteador = Roteador(router_id)
    roteador.iniciar()
