import networkx as nx
import matplotlib.pyplot as plt

grafo = nx.Graph()
grafo.add_weighted_edges_from([
    ("r1", "r2", 2),
    ("r2", "r4", 1),
    ("r1", "r3", 5),
    ("r1", "r4", 1)
])

# Dicionário com os layouts que serão testados
layouts = {
    "Spring Layout": nx.spring_layout,
    "Circular Layout": nx.circular_layout,
    "Shell Layout": nx.shell_layout,
    "Spectral Layout": nx.spectral_layout,
}

# Criar figura com 6 subplots (2 linhas, 3 colunas)
plt.figure(figsize=(18, 10))

for i, (layout_name, layout_func) in enumerate(layouts.items(), start=1):
    plt.subplot(2, 3, i)
    pos = layout_func(grafo)
    plt.title(layout_name)
    nx.draw(grafo, pos, with_labels=True, font_weight='bold')
    nx.draw_networkx_edge_labels(
        grafo, pos, edge_labels=nx.get_edge_attributes(grafo, 'weight'))

plt.tight_layout()
plt.show()
