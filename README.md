# Redes_II-Link_State_Routing

Criar ambiente
python -m venv .venv

Ativar ambiente
source .venv/bin/activate

Instalação das dependências
pip install -r requirements.txt

Geração do grafo, executando o grafo.py

Geração do compose, executando o compose.py

Executar o init.sh (responsável também por reiniciar o sistema, caso necesśario)

Para testar a conexão (ping) entre os roteadores e todos os outros componentes (roteadores e hosts), executar o ping.sh

Para testar a conexão (ping) entre os hostos e os outros hosts, executar o ping2.sh

~Método para gerar o requirements.txt
pip freeze > requirements.txt
