import networkx as nx
import matplotlib.pyplot as plt
import random
import csv


def gerar_grafo(quant_nos: int, prob_conexao: float = 0.3, peso_min: int = 1, peso_max: int = 10):
    """
    Gera um grafo ponderado parcialmente conectado e salva a imagem.

    Parâmetros:
    - quant_nos (int): número de nós no grafo.
    - prob_conexao (float): probabilidade de existir uma aresta entre dois nós.
    - peso_min (int): peso mínimo das arestas.
    - peso_max (int): peso máximo das arestas.

    Retorna:
    - grafo (networkx.Graph): o grafo gerado.
    """
    grafo = nx.Graph()

    # Adiciona os nós
    # for i in range(quant_nos):
    #     grafo.add_node(f"r{i+1}")

    nos = [f"r{i+1}" for i in range(quant_nos)]

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


def salvar_grafo_imagem(grafo: nx.Graph, caminho_imagem: str = 'grafo.png'):
    """
    Salva a imagem do grafo.

    Parâmetros:
    - grafo (networkx.Graph): o grafo a ser salvo.
    - caminho_imagem (str): caminho do arquivo de imagem a ser salvo.
    """

    # Layout do grafo
    # pos = nx.spring_layout(grafo, seed=42)
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


def salvar_grafo_csv(grafo: nx.Graph, caminho_csv: str = "grafo.csv"):
    """
    Salva as informações de nós, arestas e pesos do grafo em um csv.


    Parâmetros:
    - grafo (networkx.Graph): o grafo a ser salvo.
    - caminho_csv (str): caminho do arquivo CSV a ser salvo.
    """

    with open(caminho_csv, mode='w', newline='') as arquivo_csv:
        escritor = csv.writer(arquivo_csv)

        # Escrita do cabeçalho
        escritor.writerow(['no_origem', 'no_destino', 'peso'])
        for u, v, dados in grafo.edges(data=True):
            escritor.writerow([u, v, dados.get('weight', '')])


if (__name__ == '__main__'):
    caminho = "grafo.png"
    quant_roteadores = 5

    grafo = gerar_grafo(quant_roteadores)
    salvar_grafo_imagem(grafo, caminho_imagem=caminho)
    salvar_grafo_csv(grafo)
