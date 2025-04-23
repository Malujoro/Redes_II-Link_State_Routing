import networkx as nx
import matplotlib.pyplot as plt

n_roteadores = 5

grafo = nx.Graph()
grafo.add_weighted_edges_from([("r1", "r2", 2), ("r2", "r4", 1), ("r1", "r3", 5), ("r1", "r4", 1)])

pos = nx.spring_layout(grafo)

plt.figure(figsize=(10, 5))

# Subplot 1: layout padrão
plt.subplot(121)
nx.draw(grafo, with_labels=True, font_weight='bold')
nx.draw_networkx_edge_labels(grafo, pos, edge_labels=nx.get_edge_attributes(grafo, 'weight'))

# Subplot 2: layout shell
plt.subplot(122)
shell_pos = nx.shell_layout(grafo)
nx.draw(grafo, shell_pos, with_labels=True, font_weight='bold')
nx.draw_networkx_edge_labels(grafo, shell_pos, edge_labels=nx.get_edge_attributes(grafo, 'weight'))

plt.tight_layout()
plt.show()