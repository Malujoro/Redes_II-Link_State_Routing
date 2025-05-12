import yaml
import csv
from collections import defaultdict

# Função para gerar o docker compose baseado em um arquivo csv
def gerar_docker_compose(caminho_csv, caminho_saida="docker-compose.yml"):
    conexoes = []
    roteadores = set()

    # Leitura do csv, definindo a estrutura inicial
    with open(caminho_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            origem, destino, peso = row['no_origem'], row['no_destino'], int(
                row['peso'])
            conexoes.append((origem, destino, peso))
            roteadores.update([origem, destino])

    # Criação do grafo de conexões (quem está conectado a quem)
    conexoes_por_roteador = defaultdict(list)
    for origem, destino, peso in conexoes:
        conexoes_por_roteador[origem].append(destino)
        conexoes_por_roteador[destino].append(origem)

    # Preparação do modelo de sub-redes e ips (do roteador) 
    subnet_base = "10.10.{0}.0/24"
    ip_base = "10.10.{0}.{1}"
    networks = {}
    ip_map = defaultdict(dict)
    subnet_count = 1

    # Estrutura principal do docker compose
    docker_compose = {
        'version': '3.9',
        'services': {}
    }

    subnet_cost = {}
    # Criação das redes/conexões entre roteadores
    for origem, destino, peso in conexoes:
        net_name = f"{origem}_{destino}_net"
        subnet = subnet_base.format(subnet_count)
        ip_map[origem][net_name] = ip_base.format(subnet_count, 2)
        ip_map[destino][net_name] = ip_base.format(subnet_count, 3)
        networks[net_name] = subnet
        subnet_cost[net_name] = peso
        subnet_count += 1

    # Criação dos serviços de roteadores 
    for r in sorted(roteadores):
        service = {
            'build': './roteador',
            'container_name': r,
            'environment': {
                'CONTAINER_NAME': r,
            },
            'volumes': [
                './roteador/roteador.py:/app/roteador.py',
                './logs:/compartilhado',
            ],
            'networks': {}
        }
        # Ligações do roteador com as redes entre roteadores (estabelecendo os ips e custo das conexões)
        for net, ip in ip_map[r].items():
            service['networks'][net] = {'ipv4_address': ip}
            service['environment'][f"CUSTO_{net}"] = str(subnet_cost[net])
        service['cap_add'] = ['NET_ADMIN']

        # Criação da rede dos hosts do roteador
        host_net = f"{r}_hosts_net"
        host_subnet = f"192.168.{subnet_count}.0/24"
        networks[host_net] = host_subnet
        # Configuração do roteador na rede de hosts como gateway (final com padrão .2)
        gateway_ip = f"192.168.{subnet_count}.2"
        service['networks'][host_net] = {'ipv4_address': gateway_ip}

        docker_compose['services'][r] = service

        # Criação dos 2 hosts por roteador
        for i in range(1, 3):
            host_name = f"{r}_h{i}"
            host_ip = f"192.168.{subnet_count}.{i + 2}"
            docker_compose['services'][host_name] = {
                'build': './host',
                'container_name': host_name,
                'networks': {
                    host_net: {'ipv4_address': host_ip}
                },
                'cap_add': ['NET_ADMIN']
            }

        subnet_count += 1

    # Criação de todas as redes
    docker_compose['networks'] = {}
    for net, subnet in networks.items():
        docker_compose['networks'][net] = {
            'driver': 'bridge',
            'ipam': {
                'config': [{'subnet': subnet}]
            }
        }

    # Salvamento do arquivo
    with open(caminho_saida, "w") as f:
        yaml.dump(docker_compose, f, default_flow_style=False, sort_keys=False)

    print(f"Docker Compose salvo em: {caminho_saida}")


if (__name__ == '__main__'):
    gerar_docker_compose("grafo.csv")
