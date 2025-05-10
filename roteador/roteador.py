import time
import psutil
import socket
import threading
import json
import os
import subprocess
import ipaddress

class LSDB:
    """
    Representa o Banco de Dados de Estado de Enlace (Link State Database - LSDB), responsável por armazenar as informações recebidas via LSA (Link State Advertisement) e calcular os melhores caminhos na rede utilizando o algoritmo de Dijkstra
    """

    __slots__ = [
        "_tabela", "_router_id", "_roteamento", "_neighbors_ip"
    ]

    def __init__(self, router_id: str, neighbors_ip: dict[str, str]):
        """
        Inicializa um novo LSDB

        Args: 
            router_id (str): Identificador único do roteador
            neighbors_ip (dict[str, str]): Dicionário onde a chave é o ID do vizinho e o valor é seu IP

        """
        self._router_id = router_id
        self._neighbors_ip = neighbors_ip
        # Registro das informações recebidas pelo LSA
        self._tabela = {}
        # Dicionário que mantém registro dos roteadores de destino e os próximos saltos para alcançá-los
        self._roteamento = {}

    def criar_entrada(self, sequence_number: int, timestamp: float, addresses: list[str], links: dict[str, int]) -> dict:
        """
        Cria uma entrada na tabela baseado nas informações do pacote

        Args:
            sequence_number (int): Número de sequência
            timestamp (float): Tempo de criação do pacote
            addresses (list[str]): Lista com todos os endereços IP das interfaces
            links (dict[str, int]): Dicionário onde a chave é o ID do vizinho e o valor é o custo para alcançá-lo

        Returns: 
            dict: Dicionário com os dados da entrada
        """

        return {
            "sequence_number": sequence_number,
            "timestamp": timestamp,
            "addresses": addresses,
            "links": links,
        }

    def atualizar(self, pacote: dict) -> bool:
        """
        Atualiza a tabela de roteamento após receber um pacote LSA válido

        Args:
            pacote (dict): Pacote LSA no formato de dicionário

        Returns:
            bool: Um booleano indicando se a tabela foi atualizada ou não
        """
        # Extrai o ID do emissor e número de sequência do pacote
        router_id = pacote["router_id"]
        sequence_number = pacote["sequence_number"]

        # Retorna a entrada (caso exista) do emissor na LSDB
        entrada = self._tabela.get(router_id)

        # O pacote é inválido quando já há uma entrada "igual ou mais antiga" do que o pacote recém-chegado
        if (entrada and sequence_number <= entrada["sequence_number"]):
            return False

        # Cria uma entrada na tabela
        self._tabela[pacote["router_id"]] = self.criar_entrada(
            sequence_number, pacote["timestamp"], pacote["addresses"], pacote["links"])

        # Verifica se há um roteador "desconhecido" presente nos vizinhos de algum roteador conhecido, criando uma entrada para o mesmo
        for vizinho in pacote["links"].keys():
            if (vizinho not in self._tabela):
                print(f"[{self._router_id}][LSDB] Descoberto novo roteador: {vizinho}")
                self._tabela[vizinho] = self.criar_entrada(-1, 0, [], {})

        # Calcula o menor caminho para se chegar em cada um dos outros roteadores
        caminhos = self.dijkstra()
        # Percorre os menores caminhos encontrados para estabelecer quem será o próximo pulo
        self.atualizar_proximo_pulo(caminhos)
        # Atualiza as rotas na tabela de roteamento
        self.atualizar_rotas()
        return True

    def dijkstra(self) -> dict:
        """
        Calcula o caminho com menor custo entre o roteador atual e todos os demais roteadores conhecidos

        Returns:
            dict: Dicionário com a chave sendo o roteador de destino e o valor sendo o roteador anterior a ele
        """
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
        """
        Percorre os menores caminhos encontrados para estabelecer quem será o próximo pulo para cada roteador, partindo do roteador atual

        Args:
            caminhos (dict): Dicionário com a chave sendo o roteador de destino e o valor sendo o roteador anterior a ele
        """
        for destino in caminhos.keys():
            if (destino != self._router_id):
                pulo = destino
                while (pulo is not None and caminhos[pulo] != self._router_id):
                    pulo = caminhos[pulo]
                self._roteamento[destino] = pulo

        self._roteamento = dict(sorted(self._roteamento.items()))

    def atualizar_rotas(self):
        """
        Atualiza as rotas na tabela de roteamento, baseado no próximo pulo encontrado pela função atualizar_proximo_pulo
        """
        for roteador_destino, roteador_gateway in list(self._roteamento.items()):
            # Caso não seja o próprio roteador
            if (roteador_destino != self._router_id):
                # Ignora o roteador caso o caminho não seja conhecido
                if (roteador_gateway not in self._neighbors_ip):
                    print(
                        f"[{self._router_id}][LSDB] Ignorando rota para {roteador_destino} via {roteador_gateway}: gateway não conhecido ainda")
                else:
                    # Atualiza a rota associando todos os ips do vizinho ao próximo pulo
                    for ip_destino in self._tabela[roteador_destino]["addresses"]:
                        ip_gateway = self._neighbors_ip[roteador_gateway]

                        comando = ["ip", "route", "replace",
                                   ip_destino, "via", ip_gateway]
                        try:
                            subprocess.run(comando, check=True)
                            print(
                                f"[{self._router_id}] Rota adicionada: {ip_destino} -> {ip_gateway} [{roteador_gateway}]")
                        except subprocess.CalledProcessError as e:
                            print(
                                f"[ERRO] Falha ao adicionar rota: [{comando}] -> [{e}] ({self._router_id} -> {roteador_gateway})")

class HelloSender:
    """
    Classe responsável por criar e enviar pacotes HELLO periodicamente para vizinhos em uma rede
    """

    __slots__ = [
        "_router_id", "_interfaces", "_neighbors", "_interval", "_PORTA"
    ]

    def __init__(self, router_id: str, interfaces: list[dict[str, str]], neighbors: dict[str, str], interval: int = 10, PORTA: int = 5000):
        """
        Inicializa um novo emissor

        Args:
            router_id (str): Identificador único do roteador
            interfaces (list[dict[str, str]]): Lista de dicionários representando as interfaces de rede. Cada dicionário deve conter:
                - "address": IP da interface
                - "broadcast": IP de broadcast (se aplicável) 
            neighbors (dict[str, str]): Dicionário com os roteadores vizinhos conhecidos. A chave é o ID do vizinho e o valor é seu IP
            interval (int, opcional): Tempo de intervalo para o envio periódico dos pacotes HELLO
            PORTA (int, opcional): Porta UDP onde o roteador irá escutar os pacotes (Padrão: 5000)
        """
        self._router_id = router_id
        self._interfaces = interfaces
        self._neighbors = neighbors
        self._interval = interval
        self._PORTA = PORTA

    def criar_pacote(self, ip_address: str) -> dict:
        """
        Cria um pacote HELLO

        Args:
            ip_address (str): Endereço IP da interface local

        Returns: 
            dict: Dicionário com os dados do pacote HELLO
        """
        return {
            "type": "HELLO",
            "router_id": self._router_id,
            "timestamp": time.time(),
            "ip_address": ip_address,
            "known_neighbors": list(self._neighbors.keys()),
        }

    def enviar_broadcast(self):
        """
        Inicia o envio periódico de pacotes HELLO por meio do broadcast
        """
        # Filtra apenas as interfaces que possuem endereço de broadcast
        interfaces = [item for item in self._interfaces if "broadcast" in item]

        sock = create_socket()
        # Configura o socket para envio de broadcast
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

        while True:
            for interface_info in interfaces:
                ip_address = interface_info["address"]
                broadcast_ip = interface_info["broadcast"]

                # Cria o pacote
                pacote = self.criar_pacote(ip_address)
                # Converte no formato necessário
                message = json.dumps(pacote).encode("utf-8")

                try:
                    # Envia o pacote
                    sock.sendto(message, (broadcast_ip, self._PORTA))
                    print(
                        f"[{self._router_id}] Pacote HELLO enviado para {broadcast_ip}")
                except Exception as e:
                    print(
                        f"[{self._router_id}] Erro ao enviar para {broadcast_ip}: {e}")

            # Timer para envio de um novo pacote HELLO
            time.sleep(self._interval)

    def iniciar(self):
        """
        Inicia o funcionamento do emissor de HELLO:
        - Inicializa uma thread responsável por enviar os pacotes por broadcast para cada interface
        """
        thread_emissor = threading.Thread(
            target=self.enviar_broadcast, daemon=True)
        thread_emissor.start()

class LSASender:
    """
    Classe responsável por criar, enviar e encaminhar pacotes LSA (Link State Advertisement) na rede

    Envia periodicamente pacotes LSA para vizinhos diretos e também encaminha os pacotes recebidos para outros vizinhos
    """

    __slots__ = [
        "_router_id", "_neighbors_ip", "_neighbors_cost", "_interval", "_PORTA", "_sequence_number", "_iniciado", "_lsdb", "_interfaces"
    ]

    def __init__(self, router_id: str, neighbors_ip: dict[str, str], neighbors_cost: dict[str, int], interfaces: list[dict[str, str]], lsdb: LSDB, interval: int = 30, PORTA: int = 5000):
        """
        Inicializa um novo emissor

        Args:
            router_id (str): Identificador único do roteador
            neighbors_ip (dict[str, str]): Dicionário onde a chave é o ID do vizinho e o valor é seu IP
            neighbors_cost (dict[str, str]): Dicionário onde a chave é o ID do vizinho e o valor é o custo para alcançá-lo
            interfaces (list[dict[str, str]]): Lista de dicionários representando as interfaces de rede. Cada dicionário deve conter:
                - "address": IP da interface
                - "broadcast": IP de broadcast (se aplicável) 
            interval (int, opcional): Tempo de intervalo para o envio periódico dos pacotes HELLO
            PORTA (int, opcional): Porta UDP onde o roteador irá escutar os pacotes (Padrão: 5000)
        """

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
    def neighbors_ip(self):
        return self._neighbors_ip

    @property
    def neighbors_cost(self):
        return self._neighbors_cost

    def criar_pacote(self) -> dict:
        """
        Cria um pacote LSA

        Returns: 
            dict: Dicionário com os dados do pacote LSA
        """

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
        """
        Inicia o envio periódico de pacotes LSA para todos os seus vizinhos diretos
        """
        sock = create_socket()
        while True:
            # Cria o pacote
            pacote = self.criar_pacote()
            # Atualiza a LSDB com os próprios dados
            self._lsdb.atualizar(pacote)
            # Converte no formato necessário
            message = json.dumps(pacote).encode("utf-8")

            # Envia o LSA para cada um de seus vizinhos diretos
            for neighbor_id, ip in self._neighbors_ip.items():
                try:
                    sock.sendto(message, (ip, self._PORTA))
                    print(
                        f"[{self._router_id}] Pacote LSA enviado para {ip} [{neighbor_id}]")
                except Exception as e:
                    print(
                        f"[{self._router_id}] Erro ao enviar para [{neighbor_id}]: {e}")

            # Timer para envio de um novo pacote LSA
            time.sleep(self._interval)

    def encaminhar_para_vizinhos(self, pacote: dict, sender_ip: str):
        """
        Encaminha os pacotes LSA recebidos para todos os vizinhos (com exceção do remetente original do pacote)

        Args: 
            pacote (dict): Pacote LSA no formato de dicionário
            sender_ip (str): IP do roteador emissor do pacote
        """

        sock = create_socket()
        message = json.dumps(pacote).encode("utf-8")

        # Cria uma lista de tuplas (ID, IP) com os vizinhos que receberão o pacote
        neighbors_list = [
            (neighbor_id, ip) for neighbor_id, ip in self._neighbors_ip.items() if ip != sender_ip]

        # Encaminha o pacote para seus vizinhos
        for neighbor_id, ip in neighbors_list:
            try:
                sock.sendto(message, (ip, self._PORTA))
                print(
                    f"[{self._router_id}] Pacote LSA encaminhado para {ip} [{neighbor_id}]")
            except Exception as e:
                print(
                    f"[{self._router_id}] Erro ao encaminhar para [{neighbor_id}]: {e}")

    def iniciar(self):
        """
        Inicia o funcionamento do emissor de LSA, caso não tenha sido iniciado:
        - Inicializa uma thread responsável por enviar os pacotes
        """
        if (not self._iniciado):
            self._iniciado = True
            thread_emissor = threading.Thread(
                target=self.enviar_para_vizinhos, daemon=True)
            thread_emissor.start()

class Roteador:
    """
    Representa um roteador de rede em uma simulação de protocolo de roteamento
    """

    __slots__ = [
        "_router_id", "_interfaces", "_PORTA", "_lsa", "_lsdb", "_BUFFER_SIZE", "_neighbors_detected", "_neighbors_recognized", "_gerenciador_vizinhos"
    ]

    def __init__(self, router_id: str, PORTA: int = 5000, BUFFER_SIZE: int = 4096):
        """
        Inicializa um novo roteador

        Args:
            router_id (str): Identificador único do roteador
            PORTA (int, opcional): Porta UDP onde o roteador irá escutar os pacotes (Padrão: 5000)
            BUFFER_SIZE (int, opcional): Tamanho máximo do buffer de recepção (Padrão: 4096)
        """
        self._router_id = router_id
        self._interfaces = self.listar_enderecos()
        self._PORTA = PORTA
        self._BUFFER_SIZE = BUFFER_SIZE
        # Vizinhos detectados pelo HELLO
        self._neighbors_detected = {}
        # Vizinhos reconhecidos bidirecionalmente
        self._neighbors_recognized = {}
        self._lsdb = LSDB(router_id, self._neighbors_recognized)
        self._lsa = LSASender(
            self._router_id, self._neighbors_recognized,
            self._neighbors_detected, self._interfaces, self._lsdb
        )
        self._gerenciador_vizinhos = GerenciadorVizinhos(
            self._router_id, self._lsa, self._lsdb
        )

    def receber_pacotes(self):
        """
        Inicia a escuta de pacotes UDP na porta definida
        Trata pacotes do tipo HELLO e LSA
        """
        sock = create_socket()
        # Escuta em todas as interfaces
        sock.bind(("", self._PORTA))

        while True:
            try:
                # Recebe o pacote, convertendo-o em json
                data, address = sock.recvfrom(self._BUFFER_SIZE)
                mensagem = data.decode("utf-8")
                pacote = json.loads(mensagem)
                # Retorna o tipo do pacote e o id do roteador emissor
                tipo_pacote = pacote.get("type")
                sender_id = pacote.get("router_id")
                # Caso o pacote tenha sido enviado por outro roteador
                if (sender_id != self._router_id):
                    # Recebe o ip do emissor
                    sender_ip = address[0]
                    print(
                        f"[{self._router_id}] Pacote {tipo_pacote} recebido de {sender_ip} [{sender_id}]")

                    # Processa o pacote baseado em seu tipo
                    if (tipo_pacote == "HELLO"):
                        self._gerenciador_vizinhos.processar_hello(
                            pacote, sender_ip)
                    elif (tipo_pacote == "LSA"):
                        self._gerenciador_vizinhos.processar_lsa(
                            pacote, sender_ip)

            except Exception as e:
                print(f"Erro ao receber pacote: {e}")

    def listar_enderecos(self) -> list[dict]:
        """
        Lista os endereços IP das interfaces do sistema

        Returns: 
            list[dict]: Lista de dicionários com endereços IP (e broadcast, caso sejam das conexões com outros roteadores)
                        Interfaces com IPs iniciados em 192 são tratadas como redes /24, sendo representadas com seu endereço de rede
        """
        interfaces = psutil.net_if_addrs()
        interfaces_list = []
        for interface, addresses in interfaces.items():
            # Filtra apenas as interfaces eth
            if (interface.startswith("eth")):
                for address in addresses:
                    # Caso seja da família IPv4
                    if (address.family == socket.AF_INET):
                        # Caso seja o endereço de uma rede local (iniciada em 192)
                        if (address.address.startswith("192")):
                            # Formata o ip como rede /24
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
        """
        Inicia o funcionamento do roteador:
        - Inicializa uma thread para escutar pacotes
        - Inicia o envio periódico de pacotes HELLO
        - Mantém o processo ativo com um looping infinito
        """
        hello = HelloSender(self._router_id, self._interfaces,
                            self._neighbors_detected)

        # Thread para recepção de pacotes
        thread_receptor = threading.Thread(
            target=self.receber_pacotes, daemon=True)
        thread_receptor.start()

        # Inicia o envio de pacotes HELLO
        hello.iniciar()

        # Loop para manter o processo vivo
        while True:
            time.sleep(1)

class GerenciadorVizinhos:
    """
    Classe responsável por processar pacotes HELLO e LSA além de gerenciar os vizinhos do roteador
    """

    __slots__ = [
        "_router_id", "_lsa", "_lsdb", "_neighbors_detected", "_neighbors_recognized"
    ]

    def __init__(self, router_id: str, lsa: LSASender, lsdb: LSDB):
        """
        Inicializa o gerenciador

        Args: 
            router_id (str): Identificador único do roteador
            lsa (LSASender): Emissor de pacotes LSA
            lsdb (LSDB): Banco de dados de estado de enlace
        """
        self._router_id = router_id
        self._lsa = lsa
        self._lsdb = lsdb
        self._neighbors_detected = lsa.neighbors_cost
        self._neighbors_recognized = lsa.neighbors_ip

    def processar_hello(self, pacote: dict, sender_ip: str):
        """
        Processa um pacote HELLO, reconhecendo vizinhos diretos e iniciando a emissão de pacotes LSA para eles, caso aplicável

        Args: 
        pacote (dict): Pacote HELLO no formato de dicionário
        sender_ip (str): IP do roteador emissor do pacote
        """
        # Retorna o nome do roteador emissor
        sender_id = pacote.get("router_id")
        # Retorna o custo da troca de pacotes entre o roteador e seu vizinho
        self._neighbors_detected[sender_id] = self.get_custo(
            self._router_id, sender_id)
        # Retorna os vizinhos conhecidos do roteador emissor
        neighbors = pacote.get("known_neighbors")

        # Caso o emissor tenha reconhecido o roteador atual e ainda não tenha sido registrado como vizinhos conhecidos
        if ((self._router_id in neighbors) and (sender_id not in self._neighbors_recognized)):
            # Registra o IP do emissor
            self._neighbors_recognized[sender_id] = sender_ip
            # Inicia o envio de pacotes LSA com ele
            self._lsa.iniciar()

    def processar_lsa(self, pacote: dict, sender_ip: str):
        """
        Processa o pacote LSA, atualizando a LSDB e, caso seja um pacote válido, encaminhando ele para seus vizinhos

        Args: 
            pacote (dict): Pacote LSA no formato de dicionário
            sender_ip (str): IP do roteador emissor do pacote
        """
        pacote_valido = self._lsdb.atualizar(pacote)
        if (pacote_valido):
            self._lsa.encaminhar_para_vizinhos(pacote, sender_ip)

    def get_custo(self, router_id: str, neighbor_id: str) -> int:
        """
        Retorna o custo da troca de pacotes entre o roteador e seu vizinho, armazenado em variáveis de ambientes 

        Args:
            router_id (str): Identificador único do roteador
            neighbor_id (str): Identificador único do vizinho

        Returns:
            int: Custo da rota
        """
        custo = os.getenv(f"CUSTO_{router_id}_{neighbor_id}_net")
        # Caso não esteja no formato r2_r1, está no formato r1_r2
        if (custo == None):
            custo = os.getenv(f"CUSTO_{neighbor_id}_{router_id}_net")
        return int(custo)

def create_socket():
    """
    Cria e retorna um socket UDP IPv4
    """
    return socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

if (__name__ == "__main__"):
    # Retorna o nome do roteador, definido por uma variável de ambiente
    router_id = os.getenv("CONTAINER_NAME")
    if (not router_id):
        raise ValueError(
            "CONTAINER_NAME não definido nas variáveis de ambiente")

    # Executa o algoritmo de roteador
    roteador = Roteador(router_id)
    roteador.iniciar()
