# Sistema de Sincronização de Arquivos usando RMI (Python 3.12)

Este é um sistema distribuído implementado utilizando o conceito de Invocação Remota de Métodos (RMI) sobre HTTP em Python. Ele sincroniza um arquivo `master.txt` no servidor com um arquivo `slave.txt` no cliente. O sistema suporta autenticação, requisições concorrentes e três protocolos de comunicação.

## Funcionalidades
- Interface remota com esqueleto dinâmico (reflection)
- Comunicação RMI via HTTP (`http.server` + `urllib.request`)
- Autenticação via Basic Auth com registro de usuários
- Três estilos de comunicação: R (Requisição), RR (Requisição-Resposta), RRA (Confirmação Assíncrona)
- Detecção automática de mudanças no `master.txt`
- Servidor multithread para vários clientes simultâneos
- Log de sincronização salvo em `server/sync.log`

## Requisitos
Somente a biblioteca padrão do Python 3.12 é utilizada. Nenhuma dependência externa é necessária.

## Estrutura de Diretórios
```
sync_rmi_project/
├── client/
│   ├── client_main.py          # Ponto de entrada do cliente
│   ├── stub.py                 # Stub/proxy do cliente
│   ├── sync_monitor.py         # Monitor de sincronização
│   └── slave.txt               # Arquivo sincronizado localmente
│
├── server/
│   ├── server_main.py          # Ponto de entrada do servidor
│   ├── dispatcher.py           # Esqueleto/Dispatcher
│   ├── threads.py              # Servidor HTTP com threads
│   ├── file_handler.py         # Manipulação de arquivos e versões
│   ├── master.txt              # Arquivo mestre a ser sincronizado
│   ├── sync.log                # Log de sincronizações
│   └── users.json              # Arquivo JSON com usuários autorizados
│
├── common/
│   ├── auth.py                 # Funções de autenticação
│   └── protocol.py             # Enum SyncProtocol e utilitários
│
├── interface/
│   └── remote_interface.py     # Interface Remota (IDL)
│
├── README.md
└── requirements.txt
```

## Iniciando

### 1. Iniciar o Servidor
```bash
cd server
python server_main.py --host localhost --port 8000
```
Você pode adicionar usuários com:
```bash
python server_main.py --add-user USUARIO SENHA
```
Ou listar usuários:
```bash
python server_main.py --list-users
```

### 2. Rodar o Cliente
```bash
cd client
python client_main.py --server http://localhost:8000 \
                      --username admin \
                      --password password \
                      --protocol R \
                      --interval 5
```
Substitua `--protocol` por `RR` ou `RRA` para testar os outros modos.

### 3. Editar `master.txt`
Altere o conteúdo do arquivo `server/master.txt` para testar a sincronização automática. O cliente detectará a mudança e atualizará o `slave.txt`.

## Arquivo de Log
Todas as tentativas de sincronização são registradas em `server/sync.log`, com:
- Endereço IP
- Nome de usuário
- Operação realizada
- Status (SUCCESS / FAILED)
- Data e hora

## Licença
Licença MIT

---

Para uso exclusivamente acadêmico. Desenvolvido para a disciplina de Sistemas Distribuídos.
