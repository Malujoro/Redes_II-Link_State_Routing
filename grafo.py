import networkx as nx
import matplotlib.pyplot as plt
import random
import csv

# Função para gerar um grafo parcialmente conectado
def gerar_grafo(quant_nos: int, prob_conexao: float = 0.3, peso_min: int = 1, peso_max: int = 10):
    grafo = nx.Graph()

    # Gera e adiciona os nós
    nos = [f"r{i + 1}" for i in range(quant_nos)]
    grafo.add_nodes_from(nos)

    # Adiciona arestas com peso aleatório
    for i in range(quant_nos):
        for j in range(i + 1, quant_nos):
            if (random.random() < prob_conexao):
                peso = random.randint(peso_min, peso_max)
                grafo.add_edge(nos[i], nos[j], weight=peso)

    # Se o grafo não for conexo, adicione arestas aleatórias para conectá-lo
    while not nx.is_connected(grafo):
        # Escolhe dois nós desconectados aleatórios para adicionar uma conexão
        no1, no2 = random.sample(list(grafo.nodes()), 2)
        if (not grafo.has_edge(no1, no2)):
            peso = random.randint(peso_min, peso_max)
            grafo.add_edge(no1, no2, weight=peso)

    return grafo


# Função para salvar a imagem de um grafo
def salvar_grafo_imagem(grafo: nx.Graph, caminho_imagem: str = 'grafo.png'):
    pos = nx.circular_layout(grafo)
    pesos = nx.get_edge_attributes(grafo, 'weight')

    # Aumenta o tamanho da figura
    plt.figure(figsize=(10, 10))

    # Desenhando o grafo
    nx.draw(grafo, pos, with_labels=True, node_color='skyblue',
            node_size=500, edge_color='gray')
    nx.draw_networkx_edge_labels(grafo, pos, edge_labels=pesos)

    # Salvando a imagem
    plt.title(
        f"Grafo parcialmente conectado com {grafo.number_of_nodes()} nós")
    plt.savefig(caminho_imagem, format='png', dpi=300)
    plt.close()


# Função para salvar as informações do grafo (nós, arestas e pesos) do grafo em um .csv
def salvar_grafo_csv(grafo: nx.Graph, caminho_csv: str = "grafo.csv"):

    with open(caminho_csv, mode='w', newline='') as arquivo_csv:
        escritor = csv.writer(arquivo_csv)

        # Escrita do cabeçalho
        escritor.writerow(['no_origem', 'no_destino', 'peso'])
        for u, v, dados in grafo.edges(data=True):
            escritor.writerow([u, v, dados.get('weight', '')])


if (__name__ == '__main__'):
    caminho = "grafos/grafo"
    quant_roteadores = 10

    grafo = gerar_grafo(quant_roteadores)
    salvar_grafo_imagem(grafo, caminho_imagem=f"{caminho}.png")
    salvar_grafo_csv(grafo, caminho_csv=f"{caminho}.csv")
