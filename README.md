# Sistema de Roteamento por Estado de Enlace (Link State Routing)

## Funcionamento geral

Este projeto tem como objetivo simular o funcionamento do sistema de roteamento por estado de enlace.

A rede será composta por diversas sub-redes.

Cada sub-rede é composta por um roteador e dois hosts.

As sub-redes estão conectados por uma topologia aleatória, com a única restrição sendo que ela deve estar parcialmente conectada.

Tecnologias utilizadas:
- Python: implementa a lógica e funcionamento dos roteadores.
- Docker: utilizando containers, representa os roteadores e hosts da rede.

Para que o projeto funcione da maneira esperada, faz uso dos seguintes componentes:
- Pacotes HELLO: responsáveis por permitir que os roteadores conheçam quem são seus vizinhos diretos na topologia.
- Pacotes LSA (Link State Advertisement): responsáveis por compartilhar as informações dos roteadores em toda a rede, permitindo que todos possam conhecer a topologia.
- LSDB (Link State Database): responsável por armazenar as informações da topologia.
- Algoritmo de Dijkstra: utiliza as informações armazenadas no LSDB para calcular a menor rota entre um roteador e todos os outros da topologia.
- Ip route: responsável por atualizar a tabela de roteamento, baseado na rota determinada pelo algoritmo de Dijkstra.

Considerando que os roteadores precisarão trocar pacotes constantemente, priorizando a velocidade de comunicação e aceitando possíveis falhas (já que os pacotes são enviados periodicamente), o **protocolo UDP** foi escolhido para realizar a comunicação entre os roteadores.

## Execução do projeto
Para executar o projeto com uma topologia gerada aleatóriamente, é necessário seguir as seguintes instruções:

Para criar o ambiente em que serão instalados o python e as dependências necessárias para seu funcionamento, será necessário executar o seguinte comando na pasta do projeto:
```python -m venv .venv```

Após a criação do ambiente, é necessário ativá-lo com
```source .venv/bin/activate```

Após ativar o ambiente, é preciso instalar as dependências requeridas com
```pip install -r requirements.txt```

A topologia se baseia em um grafo gerado aleatoriamente pelo arquivo [grafo.py](grafo.py). Por padrão, a quantidade de roteadores está definida em 5, mas pode ser alterada no arquivo.
Para gerar o grafo basta executar o arquivo ```grafo.py```.

Será salvo uma [imagem do grafo](grafo.png) contendo apenas os roteadores, para facilitar a visualização, bem como um [arquivo csv](grafo.csv) contendo as informações das conexões e pesos.

Baseado no grafo gerado, o [compose.py](compose.py) será responsável por gerar o arquivo **docker-compose.yml**, que conterá as informações necessárias para estabelecer a estrutura do projeto, como as conexões e containers. 
Para isso, basta executar o arquivo ```compose.py```.

Com o docker-compose gerado, é preciso construir as imagens dos containers e executá-las.
Para isso, basta utilizar o seguinte comando ```sudo docker compose up --build```.

Caso o projeto já esteja rodando e seja necessário reiniciá-lo (considerando que não houveram alterações na estrutura do Dockerfile ou do docker-compose), basta executar o arquivo ```./init.sh```

Caso o projeto já esteja rodando e seja necessário finalizar sua execução, basta executar o seguinte comando:
```sudo docker compose down```

Caso queira testar a conexão por meio de ping entre os roteadores e todos os outros componentes da rede (roteadores e hosts), basta executar
```./ping.sh```

Caso queira testar a conexão por meio de ping entre os hosts e todos os outros hosts, basta executar
```./ping2.sh```