# 💡 Sistema de Roteamento por Estado de Enlace (Link State Routing)

## 📘 Descrição Geral

Este projeto tem como objetivo **simular o funcionamento de um sistema de roteamento baseado no protocolo de Estado de Enlace (Link State Routing)**, utilizando:

- 🐍 **Python**: para a lógica e funcionamento dos roteadores
- 🐳 **Docker**: para simular hosts e roteadores como containers interconectados


A rede será composta por diversas **sub-redes**, onde:

- Cada **sub-rede** contém **1 roteador** e **2 hosts**
- Os roteadores se conectam entre si segundo uma **topologia aleatória**, com a única exigência de que ela seja **parcialmente conectada**

---

## 🧠 Componentes do Sistema

O sistema é construído com os seguintes módulos e conceitos: 

- 🔄 **Pacotes HELLO**: permitem que os roteadores identifiquem seus vizinhos diretos na topologia
- 📡 **Pacotes LSA (Link State Advertisement)**: compartilham as informações dos roteadores em toda a rede, permitindo que todos possam conhecer a topologia
- 🗃️ **LSDB (Link State Database)**: armazena as informações da topologia da rede
- 🧭 **Algoritmo de Dijkstra**: calcula os caminhos de menor custo entre os roteadores, baseando-se nas informações armazenadas no LSDB
- 🧷 **`Ip route`**: atualiza a tabela de roteamento, baseado-se nas rotas calculadas

> 💬 **Protocolo utilizado**:
> Para comunicação entre os roteadores, o projeto utiliza o **UDP**. Essa escolha se deve ao fato que ele oferece maior desempenho e simplicidade para o envio periódico de pacotes. Mesmo que ocorram pequenas perdas, o sistema se mantém funcional.

---

## 🧱 Construção da topologia
A topologia é baseada em um grafo gerado aleatoriamente pelo script [`grafo.py`](grafo.py).

- 🔢 A quantidade de roteadores padrão é 5 (editável no código)
- 🧾 Um arquivo [`grafo.csv`](grafos/grafo.csv) é gerado com as conexões e seus respectivos pesos
- 🖼️ Também é gerada uma imagem [`grafo.png`](grafos/grafo.png) com a visualização do grafo (roteadores e suas conexões)

Em seguida:

- 📦 O script [`compose.py`](compose.py) gera automaticamente o arquivo `docker-compose.yml` com base no grafo
- 🧩 Para **cada roteador** do grafo, são criados **2 hosts associados**, formando uma sub-rede isolada por container bridge
- 🔌 As conexões entre os containers representam os enlaces da topologia definida no grafo

---

## ▶️ Execução do projeto

### 🔧 1. Preparação do ambiente virtual

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 📊 2. Gerar topologia da rede

```bash
# Gera o grafo aleatório e os arquivos grafo.csv e grafo.png
python grafo.py
# Gera o docker-compose.yml com base no grafo
python compose.py
```

### 🚀 3. Executar os containers da rede

```bash
sudo docker compose up --build
```

### ♻️ 4. Reiniciar o projeto (sem rebuild)

```bash
./init.sh
```

### 🛑 5. Finalizar a execução

```bash
sudo docker compose down
```

---

## 🧪 Testes de conectividade
### 🔄 Testes entre roteadores e os outros componentes (roteadores + hosts)

```bash
./ping.sh
```

### 🔄 Teste entre hosts e todos os outros hosts

```bash
./ping2.sh
```
---

## ✅ Conclusão

Este projeto oferece uma visão prática do funcionamento de um protocolo de roteamento por estado de enlace, com simulação de uma rede distribuída de forma realista utilizando containers, permitindo a experimentação de topologias variadas.