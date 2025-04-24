import csv
from collections import defaultdict

def gerar_docker_compose(caminho_csv, caminho_saida="docker-compose.yml"):
    conexoes = []
    roteadores = set()

    with open(caminho_csv, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            origem, destino = row['no_origem'], row['no_destino']
            conexoes.append((origem, destino))
            roteadores.update([origem, destino])

    conexoes_por_roteador = defaultdict(list)
    for origem, destino in conexoes:
        conexoes_por_roteador[origem].append(destino)
        conexoes_por_roteador[destino].append(origem)

    subnet_base = "10.10.{0}.0/24"
    ip_base = "10.10.{0}.{1}"
    networks = {}
    ip_map = defaultdict(dict)
    subnet_count = 1

    for origem, destino in conexoes:
        net_name = f"{origem}_{destino}_net"
        subnet = subnet_base.format(subnet_count)
        ip_map[origem][net_name] = ip_base.format(subnet_count, 2)
        ip_map[destino][net_name] = ip_base.format(subnet_count, 3)
        networks[net_name] = subnet
        subnet_count += 1

    linhas = ["version: '3.9'", "services:"]
    for r in sorted(roteadores):
        linhas.append(f"  {r}:")
        linhas.append(f"    build: ./roteador")
        linhas.append(f"    container_name: {r}")
        linhas.append(f"    networks:")
        for net, ip in ip_map[r].items():
            linhas.append(f"      {net}:")
            linhas.append(f"        ipv4_address: {ip}")
        linhas.append(f"    cap_add:")
        linhas.append(f"      - NET_ADMIN")

        # Adiciona apenas uma rede para os dois hosts
        host_net = f"{r}_hosts_net"
        host_subnet = f"192.168.{subnet_count}.0/24"
        networks[host_net] = host_subnet

        for i in range(1, 3):
            host_name = f"{r}_h{i}"
            host_ip = f"192.168.{subnet_count}.{i+1}"
            linhas.extend([
                f"  {host_name}:",
                f"    build: ./host",
                f"    container_name: {host_name}",
                f"    networks:",
                f"      {host_net}:",
                f"        ipv4_address: {host_ip}"
            ])
        subnet_count += 1

    linhas.append("networks:")
    for net, subnet in networks.items():
        linhas.append(f"  {net}:")
        linhas.append(f"    driver: bridge")
        linhas.append(f"    ipam:")
        linhas.append(f"      config:")
        linhas.append(f"        - subnet: {subnet}")

    with open(caminho_saida, "w") as f:
        f.write('\n'.join(linhas))
    print(f"Docker Compose salvo em: {caminho_saida}")

if(__name__ == '__main__'):
    gerar_docker_compose("grafo1.csv")
