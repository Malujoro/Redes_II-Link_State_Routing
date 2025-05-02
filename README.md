# Redes_II-Link_State_Routing

Criar ambiente
```python -m venv .venv```

Ativar ambiente
```source .venv/bin/activate```

Instalação das dependências
```pip install -r requirements.txt```

Geração do grafo, executando o ```grafo.py```

Geração do compose, executando o ```compose.py```

Para iniciar pela primeira vez, basta executar ```sudo docker compose up --build```

Caso seja necessário reiniciar o sistema, execute o ```init.sh```

Para fechar o sistema, execute ```sudo docker compose down```

Para testar a conexão (ping) entre os roteadores e todos os outros componentes (roteadores e hosts), executar o ```ping.sh```

Para testar a conexão (ping) entre os hostos e os outros hosts, executar o ```ping2.sh```