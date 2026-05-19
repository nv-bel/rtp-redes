# 04 - Protocolo RTSP: Análise Profunda da Implementação

## Introdução ao RTSP

RTSP (Real Time Streaming Protocol) é o protocolo de controle de sessão para streaming de mídia. Funciona como um "controle remoto" para servidores de mídia, permitindo comandos como SETUP, PLAY, PAUSE e TEARDOWN.

## Características do RTSP (RFC 2326)

### Similaridades com HTTP

RTSP é baseado em HTTP e compartilha muitas características:

```
HTTP Request:
GET /index.html HTTP/1.1
Host: www.example.com

RTSP Request:
SETUP movie.Mjpeg RTSP/1.0
CSeq: 1
Transport: RTP/UDP; client_port=5004
```

**Semelhanças:**
- Formato texto (ASCII)
- Estrutura de requisição/resposta
- Códigos de status (200 OK, 404 Not Found, etc.)
- Cabeçalhos (headers)

**Diferenças:**
- RTSP mantém estado (stateful)
- RTSP usa Session IDs
- RTSP controla fluxo de mídia em tempo real
- RTSP não transfere dados de mídia (apenas controle)

### Modelo Stateful

```
HTTP (Stateless):
  Request 1 → Response 1 (independente)
  Request 2 → Response 2 (independente)
  Request 3 → Response 3 (independente)

RTSP (Stateful):
  SETUP → Session criada (estado: READY)
    ↓
  PLAY → Streaming iniciado (estado: PLAYING)
    ↓
  PAUSE → Streaming pausado (estado: READY)
    ↓
  TEARDOWN → Session encerrada (estado: INIT)
```

## Máquina de Estados RTSP

### Estados do Servidor e Cliente

```
┌──────────────────────────────────────────────────────────┐
│                         INIT                             │
│  - Estado inicial                                        │
│  - Sem sessão ativa                                      │
│  - Sem recursos alocados                                 │
└──────────────────────────────────────────────────────────┘
                          │
                          │ SETUP
                          ▼
┌──────────────────────────────────────────────────────────┐
│                        READY                             │
│  - Sessão estabelecida                                   │
│  - Recursos alocados                                     │
│  - Arquivo de vídeo aberto                               │
│  - Pronto para reproduzir                                │
└──────────────────────────────────────────────────────────┘
                          │
                          │ PLAY
                          ▼
┌──────────────────────────────────────────────────────────┐
│                       PLAYING                            │
│  - Stream ativo                                          │
│  - Enviando pacotes RTP                                  │
│  - Thread de envio rodando                               │
└──────────────────────────────────────────────────────────┘
                          │
                          │ PAUSE
                          ▼
                       READY
                          │
                          │ TEARDOWN
                          ▼
                        INIT
```

### Transições Válidas

| Estado Atual | Comando | Estado Novo | Ação |
|--------------|---------|-------------|------|
| INIT | SETUP | READY | Abre arquivo, cria sessão |
| READY | PLAY | PLAYING | Inicia envio RTP |
| PLAYING | PAUSE | READY | Para envio RTP |
| READY | TEARDOWN | INIT | Libera recursos |
| PLAYING | TEARDOWN | INIT | Para envio, libera recursos |

### Transições Inválidas (Ignoradas)

| Estado Atual | Comando | Ação |
|--------------|---------|------|
| INIT | PLAY | Ignorado (precisa SETUP primeiro) |
| INIT | PAUSE | Ignorado |
| READY | SETUP | Ignorado (já configurado) |
| PLAYING | SETUP | Ignorado |

## Formato das Mensagens RTSP

### Estrutura de Requisição

```
<Método> <URI> RTSP/<Versão>
<Cabeçalho1>: <Valor1>
<Cabeçalho2>: <Valor2>
...
<Linha em branco>
[Corpo opcional]
```

### Estrutura de Resposta

```
RTSP/<Versão> <Código> <Frase>
<Cabeçalho1>: <Valor1>
<Cabeçalho2>: <Valor2>
...
<Linha em branco>
[Corpo opcional]
```

## Comandos RTSP Implementados

### 1. SETUP

**Propósito:** Inicializa sessão e negocia parâmetros de transporte.

**Requisição do Cliente:**
```
SETUP movie.Mjpeg RTSP/1.0
CSeq: 1
Transport: RTP/UDP; client_port=5004
```

**Análise linha por linha:**

```
Linha 1: SETUP movie.Mjpeg RTSP/1.0
  - SETUP: método/comando
  - movie.Mjpeg: URI do recurso (arquivo de vídeo)
  - RTSP/1.0: versão do protocolo

Linha 2: CSeq: 1
  - CSeq: Command Sequence (número de sequência)
  - 1: primeiro comando da sessão
  - Incrementado a cada comando

Linha 3: Transport: RTP/UDP; client_port=5004
  - Transport: especifica método de transporte
  - RTP/UDP: protocolo RTP sobre UDP
  - client_port=5004: porta onde cliente receberá RTP
```

**Código no Cliente (Client.py):**

```python
def sendRtspRequest(self, requestCode):
    if requestCode == self.SETUP and self.state == self.INIT:
        threading.Thread(target=self.recvRtspReply).start()
        
        self.rtspSeq = 1
        
        request = ("SETUP " + str(self.fileName) + 
                   "\n " + str(self.rtspSeq) + 
                   " \n RTSP/1.0 RTP/UDP " + str(self.rtpPort))
        
        self.rtspSocket.send(request.encode())
        
        self.requestSent = self.SETUP
```

**Análise do código:**

```python
# 1. Inicia thread para receber respostas
threading.Thread(target=self.recvRtspReply).start()

# 2. Define número de sequência
self.rtspSeq = 1

# 3. Constrói mensagem RTSP
request = "SETUP movie.Mjpeg\n 1 \n RTSP/1.0 RTP/UDP 5004"

# 4. Envia via socket TCP
self.rtspSocket.send(request.encode())

# 5. Marca comando enviado
self.requestSent = self.SETUP
```

**Resposta do Servidor:**
```
RTSP/1.0 200 OK
CSeq: 1
Session: 123456
```

**Análise da resposta:**

```
Linha 1: RTSP/1.0 200 OK
  - RTSP/1.0: versão do protocolo
  - 200: código de status (sucesso)
  - OK: frase descritiva

Linha 2: CSeq: 1
  - Mesmo CSeq da requisição
  - Permite correlacionar resposta com requisição

Linha 3: Session: 123456
  - ID único da sessão
  - Gerado aleatoriamente pelo servidor
  - Usado em comandos subsequentes
```

**Código no Servidor (ServerWorker.py):**

```python
def processRtspRequest(self, data):
    request = data.split('\n')
    line1 = request[0].split(' ')
    requestType = line1[0]
    filename = line1[1]
    seq = request[1].split(' ')
    
    if requestType == self.SETUP:
        if self.state == self.INIT:
            print("Processando SETUP\n")
            
            try:
                self.clientInfo['videoStream'] = VideoStream(filename)
                self.state = self.READY
            except IOError:
                self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])
            
            self.clientInfo['session'] = randint(100000, 999999)
            
            self.replyRtsp(self.OK_200, seq[1])
            
            self.clientInfo['rtpPort'] = request[2].split(' ')[3]
```

**Análise passo a passo:**

```python
# 1. Parse da requisição
request = data.split('\n')  # Separa por linhas
line1 = request[0].split(' ')  # Separa primeira linha
requestType = line1[0]  # "SETUP"
filename = line1[1]  # "movie.Mjpeg"
seq = request[1].split(' ')  # Extrai CSeq

# 2. Verifica estado
if self.state == self.INIT:
    
    # 3. Abre arquivo de vídeo
    try:
        self.clientInfo['videoStream'] = VideoStream(filename)
        self.state = self.READY
    except IOError:
        # Arquivo não encontrado
        self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])
    
    # 4. Gera Session ID aleatório
    self.clientInfo['session'] = randint(100000, 999999)
    
    # 5. Envia resposta OK
    self.replyRtsp(self.OK_200, seq[1])
    
    # 6. Extrai porta RTP do cliente
    self.clientInfo['rtpPort'] = request[2].split(' ')[3]
```

**Método replyRtsp:**

```python
def replyRtsp(self, code, seq):
    if code == self.OK_200:
        print("200 OK")
        reply = ('RTSP/1.0 200 OK\nCSeq: ' + seq + 
                 '\nSession: ' + str(self.clientInfo['session']))
        connSocket = self.clientInfo['rtspSocket'][0]
        connSocket.send(reply.encode())
```

### 2. PLAY

**Propósito:** Inicia ou retoma reprodução do stream.

**Requisição do Cliente:**
```
PLAY RTSP/1.0
CSeq: 2
Session: 123456
```

**Análise:**
```
Linha 1: PLAY RTSP/1.0
  - PLAY: comando para iniciar reprodução
  - Sem URI (usa sessão estabelecida)

Linha 2: CSeq: 2
  - Incrementado (era 1 no SETUP)

Linha 3: Session: 123456
  - ID da sessão estabelecida no SETUP
  - Identifica qual stream controlar
```

**Código no Cliente:**

```python
elif requestCode == self.PLAY and self.state == self.READY:
    self.rtspSeq = self.rtspSeq + 1
    
    request = "PLAY " + "\n " + str(self.rtspSeq)
    self.rtspSocket.send(request.encode("utf-8"))
    print('-'*60 + "\nSolicitação PLAY enviada ao Servidor...\n" + '-'*60)
    
    self.requestSent = self.PLAY
```

**Análise:**
```python
# 1. Incrementa CSeq
self.rtspSeq = self.rtspSeq + 1  # 1 → 2

# 2. Constrói mensagem
request = "PLAY \n 2"

# 3. Envia via TCP
self.rtspSocket.send(request.encode("utf-8"))

# 4. Marca comando enviado
self.requestSent = self.PLAY
```

**Resposta do Servidor:**
```
RTSP/1.0 200 OK
CSeq: 2
Session: 123456
```

**Código no Servidor:**

```python
elif requestType == self.PLAY:
    if self.state == self.READY:
        print("Processando PLAY\n")
        self.state = self.PLAYING
        
        self.clientInfo["rtpSocket"] = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM
        )
        
        self.clientInfo["rtpSocket"].setsockopt(
            socket.IPPROTO_IP, socket.IP_TOS, 0xB8
        )
        
        self.replyRtsp(self.OK_200, seq[1])
        
        self.clientInfo['event'] = threading.Event()
        self.clientInfo['worker'] = threading.Thread(target=self.sendRtp)
        self.clientInfo['worker'].start()
```

**Análise passo a passo:**

```python
# 1. Verifica estado
if self.state == self.READY:
    
    # 2. Muda estado
    self.state = self.PLAYING
    
    # 3. Cria socket UDP para RTP
    self.clientInfo["rtpSocket"] = socket.socket(
        socket.AF_INET,  # IPv4
        socket.SOCK_DGRAM  # UDP
    )
    
    # 4. Configura QoS (DSCP = EF)
    self.clientInfo["rtpSocket"].setsockopt(
        socket.IPPROTO_IP,  # Nível IP
        socket.IP_TOS,      # Type of Service
        0xB8                # DSCP = 46 (EF)
    )
    
    # 5. Envia resposta OK
    self.replyRtsp(self.OK_200, seq[1])
    
    # 6. Cria Event para controle
    self.clientInfo['event'] = threading.Event()
    
    # 7. Inicia thread de envio RTP
    self.clientInfo['worker'] = threading.Thread(target=self.sendRtp)
    self.clientInfo['worker'].start()
```

**Thread sendRtp:**

```python
def sendRtp(self):
    while True:
        self.clientInfo['event'].wait(0.05)  # 50ms = 20 FPS
        
        if self.clientInfo['event'].isSet():
            break
        
        data = self.clientInfo['videoStream'].nextFrame()
        if data:
            frameNumber = self.clientInfo['videoStream'].frameNbr()
            try:
                address = self.clientInfo['rtspSocket'][1][0]
                port = int(self.clientInfo['rtpPort'])
                self.clientInfo['rtpSocket'].sendto(
                    self.makeRtp(data, frameNumber),
                    (address, port)
                )
            except:
                print("Erro de conexão")
```

**Análise:**

```python
# Loop infinito de envio
while True:
    # 1. Aguarda 50ms (20 frames por segundo)
    self.clientInfo['event'].wait(0.05)
    
    # 2. Verifica se deve parar (PAUSE/TEARDOWN)
    if self.clientInfo['event'].isSet():
        break
    
    # 3. Lê próximo frame do arquivo
    data = self.clientInfo['videoStream'].nextFrame()
    
    if data:
        # 4. Obtém número do frame
        frameNumber = self.clientInfo['videoStream'].frameNbr()
        
        try:
            # 5. Obtém endereço do cliente
            address = self.clientInfo['rtspSocket'][1][0]
            port = int(self.clientInfo['rtpPort'])
            
            # 6. Cria pacote RTP e envia
            packet = self.makeRtp(data, frameNumber)
            self.clientInfo['rtpSocket'].sendto(packet, (address, port))
        except:
            print("Erro de conexão")
```

### 3. PAUSE

**Propósito:** Pausa reprodução do stream.

**Requisição do Cliente:**
```
PAUSE RTSP/1.0
CSeq: 3
Session: 123456
```

**Código no Cliente:**

```python
elif requestCode == self.PAUSE and self.state == self.PLAYING:
    self.rtspSeq = self.rtspSeq + 1
    
    request = "PAUSE " + "\n " + str(self.rtspSeq)
    self.rtspSocket.send(request.encode("utf-8"))
    print('-'*60 + "\nSolicitação PAUSE enviada ao Servidor...\n" + '-'*60)
    
    self.requestSent = self.PAUSE
```

**Resposta do Servidor:**
```
RTSP/1.0 200 OK
CSeq: 3
Session: 123456
```

**Código no Servidor:**

```python
elif requestType == self.PAUSE:
    if self.state == self.PLAYING:
        print("Processando PAUSE\n")
        self.state = self.READY
        
        self.clientInfo['event'].set()
        
        self.replyRtsp(self.OK_200, seq[1])
```

**Análise:**

```python
# 1. Verifica estado
if self.state == self.PLAYING:
    
    # 2. Muda estado
    self.state = self.READY
    
    # 3. Sinaliza thread para parar
    self.clientInfo['event'].set()
    
    # 4. Envia resposta OK
    self.replyRtsp(self.OK_200, seq[1])
```

**Efeito no sendRtp:**
```python
# Thread sendRtp detecta event setado
if self.clientInfo['event'].isSet():
    break  # Para loop, encerra thread
```

### 4. TEARDOWN

**Propósito:** Encerra sessão e libera recursos.

**Requisição do Cliente:**
```
TEARDOWN RTSP/1.0
CSeq: 4
Session: 123456
```

**Código no Cliente:**

```python
elif requestCode == self.TEARDOWN and not self.state == self.INIT:
    self.rtspSeq = self.rtspSeq + 1
    
    request = "TEARDOWN " + "\n " + str(self.rtspSeq)
    self.rtspSocket.send(request.encode("utf-8"))
    print('-'*60 + "\nSolicitação TEARDOWN enviada ao Servidor...\n" + '-'*60)
    
    self.requestSent = self.TEARDOWN
```

**Resposta do Servidor:**
```
RTSP/1.0 200 OK
CSeq: 4
Session: 123456
```

**Código no Servidor:**

```python
elif requestType == self.TEARDOWN:
    print("Processando TEARDOWN\n")
    
    self.clientInfo['event'].set()
    
    self.replyRtsp(self.OK_200, seq[1])
    
    self.clientInfo['rtpSocket'].close()
```

**Análise:**

```python
# 1. Sinaliza thread para parar
self.clientInfo['event'].set()

# 2. Envia resposta OK
self.replyRtsp(self.OK_200, seq[1])

# 3. Fecha socket RTP
self.clientInfo['rtpSocket'].close()
```

**Limpeza no Cliente:**

```python
def exitClient(self):
    self.sendRtspRequest(self.TEARDOWN)
    self.master.destroy()  # Fecha GUI
    os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)  # Remove cache
```

## Processamento de Respostas no Cliente

### Recepção de Respostas

**Thread recvRtspReply:**

```python
def recvRtspReply(self):
    while True:
        reply = self.rtspSocket.recv(1024)
        
        if reply:
            self.parseRtspReply(reply.decode("utf-8"))
        
        if self.requestSent == self.TEARDOWN:
            self.rtspSocket.shutdown(socket.SHUT_RDWR)
            self.rtspSocket.close()
            break
```

**Análise:**

```python
# Loop infinito de recepção
while True:
    # 1. Recebe resposta (até 1024 bytes)
    reply = self.rtspSocket.recv(1024)
    
    if reply:
        # 2. Decodifica e processa
        self.parseRtspReply(reply.decode("utf-8"))
    
    # 3. Se foi TEARDOWN, fecha socket e para
    if self.requestSent == self.TEARDOWN:
        self.rtspSocket.shutdown(socket.SHUT_RDWR)
        self.rtspSocket.close()
        break
```

### Parse de Respostas

**Método parseRtspReply:**

```python
def parseRtspReply(self, data):
    lines = data.split('\n')
    seqNum = int(lines[1].split(' ')[1])
    
    if seqNum == self.rtspSeq:
        session = int(lines[2].split(' ')[1])
        
        if self.sessionId == 0:
            self.sessionId = session
        
        if self.sessionId == session:
            if int(lines[0].split(' ')[1]) == 200:
                if self.requestSent == self.SETUP:
                    print("\nAtualizando estado RTSP...")
                    self.state = self.READY
                    
                    print("\nConfigurando porta RTP para stream de vídeo...")
                    self.openRtpPort()
                
                elif self.requestSent == self.PLAY:
                    self.state = self.PLAYING
                    print('-'*60 + "\nCliente está PLAYING...\n" + '-'*60)
                
                elif self.requestSent == self.PAUSE:
                    self.state = self.READY
                    self.playEvent.set()
                
                elif self.requestSent == self.TEARDOWN:
                    self.state = self.INIT
                    self.teardownAcked = 1
```

**Análise passo a passo:**

```python
# 1. Parse da resposta
lines = data.split('\n')
# lines[0] = "RTSP/1.0 200 OK"
# lines[1] = "CSeq: 1"
# lines[2] = "Session: 123456"

# 2. Extrai CSeq
seqNum = int(lines[1].split(' ')[1])

# 3. Verifica se CSeq corresponde
if seqNum == self.rtspSeq:
    
    # 4. Extrai Session ID
    session = int(lines[2].split(' ')[1])
    
    # 5. Armazena Session ID (primeira vez)
    if self.sessionId == 0:
        self.sessionId = session
    
    # 6. Verifica se Session ID corresponde
    if self.sessionId == session:
        
        # 7. Extrai código de status
        statusCode = int(lines[0].split(' ')[1])
        
        # 8. Se 200 OK, processa baseado no comando
        if statusCode == 200:
            
            if self.requestSent == self.SETUP:
                # Muda estado para READY
                self.state = self.READY
                # Abre porta RTP
                self.openRtpPort()
            
            elif self.requestSent == self.PLAY:
                # Muda estado para PLAYING
                self.state = self.PLAYING
            
            elif self.requestSent == self.PAUSE:
                # Muda estado para READY
                self.state = self.READY
                # Para thread RTP
                self.playEvent.set()
            
            elif self.requestSent == self.TEARDOWN:
                # Muda estado para INIT
                self.state = self.INIT
                # Sinaliza para fechar socket RTP
                self.teardownAcked = 1
```

## Códigos de Status RTSP

### Códigos Implementados

```python
OK_200 = 0
FILE_NOT_FOUND_404 = 1
CON_ERR_500 = 2
```

### Mapeamento para Mensagens

```python
def replyRtsp(self, code, seq):
    if code == self.OK_200:
        print("200 OK")
        reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
        connSocket = self.clientInfo['rtspSocket'][0]
        connSocket.send(reply.encode())
    
    elif code == self.FILE_NOT_FOUND_404:
        print("404 NOT FOUND")
    
    elif code == self.CON_ERR_500:
        print("500 CONNECTION ERROR")
```

### Códigos RTSP Padrão (RFC 2326)

| Código | Significado | Uso |
|--------|-------------|-----|
| 200 | OK | Sucesso |
| 400 | Bad Request | Requisição malformada |
| 404 | Not Found | Arquivo não encontrado |
| 454 | Session Not Found | Session ID inválido |
| 455 | Method Not Valid in This State | Comando inválido no estado atual |
| 500 | Internal Server Error | Erro interno |

## Sequência Completa de Comunicação

### Exemplo Prático

```
Cliente                                    Servidor
  │                                          │
  │ 1. Conecta TCP (porta 554)               │
  ├─────────────────────────────────────────►│
  │                                          │
  │ 2. SETUP movie.Mjpeg                     │
  │    CSeq: 1                               │
  │    Transport: RTP/UDP; port=5004         │
  ├─────────────────────────────────────────►│
  │                                          │ Abre arquivo
  │                                          │ Gera Session: 123456
  │                                          │ Estado: READY
  │                                          │
  │ 3. RTSP/1.0 200 OK                       │
  │    CSeq: 1                               │
  │    Session: 123456                       │
  │◄─────────────────────────────────────────┤
  │                                          │
  │ Estado: READY                            │
  │ Abre porta RTP 5004                      │
  │                                          │
  │ 4. PLAY                                  │
  │    CSeq: 2                               │
  │    Session: 123456                       │
  ├─────────────────────────────────────────►│
  │                                          │ Cria socket UDP
  │                                          │ Configura QoS
  │                                          │ Inicia thread RTP
  │                                          │ Estado: PLAYING
  │                                          │
  │ 5. RTSP/1.0 200 OK                       │
  │    CSeq: 2                               │
  │    Session: 123456                       │
  │◄─────────────────────────────────────────┤
  │                                          │
  │ Estado: PLAYING                          │
  │ Inicia thread listenRtp                  │
  │                                          │
  │ 6. Pacotes RTP (UDP, porta 5004)         │
  │◄═════════════════════════════════════════┤
  │    Frame 1, Frame 2, Frame 3...          │
  │◄═════════════════════════════════════════┤
  │                                          │
  │ [Usuário clica Pause]                    │
  │                                          │
  │ 7. PAUSE                                 │
  │    CSeq: 3                               │
  │    Session: 123456                       │
  ├─────────────────────────────────────────►│
  │                                          │ Para thread RTP
  │                                          │ Estado: READY
  │                                          │
  │ 8. RTSP/1.0 200 OK                       │
  │    CSeq: 3                               │
  │    Session: 123456                       │
  │◄─────────────────────────────────────────┤
  │                                          │
  │ Estado: READY                            │
  │ Para thread listenRtp                    │
  │                                          │
  │ [Usuário clica Play novamente]           │
  │                                          │
  │ 9. PLAY                                  │
  │    CSeq: 4                               │
  │    Session: 123456                       │
  ├─────────────────────────────────────────►│
  │                                          │ Reinicia thread RTP
  │                                          │ Estado: PLAYING
  │                                          │
  │ 10. RTSP/1.0 200 OK                      │
  │     CSeq: 4                              │
  │     Session: 123456                      │
  │◄─────────────────────────────────────────┤
  │                                          │
  │ 11. Pacotes RTP continuam...             │
  │◄═════════════════════════════════════════┤
  │                                          │
  │ [Usuário clica Teardown]                 │
  │                                          │
  │ 12. TEARDOWN                             │
  │     CSeq: 5                              │
  │     Session: 123456                      │
  ├─────────────────────────────────────────►│
  │                                          │ Para thread RTP
  │                                          │ Fecha socket UDP
  │                                          │ Estado: INIT
  │                                          │
  │ 13. RTSP/1.0 200 OK                      │
  │     CSeq: 5                              │
  │     Session: 123456                      │
  │◄─────────────────────────────────────────┤
  │                                          │
  │ Fecha socket TCP                         │
  │ Remove cache                             │
  │ Estado: INIT                             │
```

## Gerenciamento de Session ID

### Geração no Servidor

```python
self.clientInfo['session'] = randint(100000, 999999)
```

**Características:**
- Número aleatório de 6 dígitos
- Único por cliente
- Gerado no SETUP
- Usado em todos os comandos subsequentes

### Validação

```python
# Cliente valida Session ID em respostas
if self.sessionId == session:
    # Processa resposta
```

**Propósito:**
- Identifica sessão específica
- Permite múltiplos clientes simultâneos
- Previne comandos para sessão errada

## Sincronização com CSeq

### Incremento no Cliente

```python
# SETUP
self.rtspSeq = 1

# PLAY
self.rtspSeq = self.rtspSeq + 1  # 2

# PAUSE
self.rtspSeq = self.rtspSeq + 1  # 3

# TEARDOWN
self.rtspSeq = self.rtspSeq + 1  # 4
```

### Validação no Cliente

```python
seqNum = int(lines[1].split(' ')[1])

if seqNum == self.rtspSeq:
    # Processa resposta
```

**Propósito:**
- Correlaciona requisição com resposta
- Detecta respostas fora de ordem
- Previne processamento de respostas antigas

## Tratamento de Erros

### Arquivo Não Encontrado

```python
try:
    self.clientInfo['videoStream'] = VideoStream(filename)
    self.state = self.READY
except IOError:
    self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])
```

### Conexão Falha

```python
try:
    self.rtspSocket.connect((self.serverAddr, self.serverPort))
except:
    tkMessageBox.showwarning('Conexão Falhou', 
                             'Conexão com \'%s\' falhou.' % self.serverAddr)
```

### Comando em Estado Inválido

```python
if requestCode == self.PLAY and self.state == self.READY:
    # Processa PLAY
else:
    return  # Ignora comando
```

## Melhorias Possíveis

### 1. Suporte a Mais Comandos

```python
# DESCRIBE: Obtém descrição do recurso
# OPTIONS: Lista comandos suportados
# GET_PARAMETER: Obtém parâmetros da sessão
# SET_PARAMETER: Define parâmetros da sessão
```

### 2. Timeout de Sessão

```python
# Encerrar sessão após inatividade
last_activity = time()
if time() - last_activity > SESSION_TIMEOUT:
    self.teardownSession()
```

### 3. Autenticação

```python
# Adicionar autenticação básica ou digest
Authorization: Basic dXNlcjpwYXNz
```

### 4. Range (Seek)

```python
# Permitir busca em posição específica
PLAY movie.Mjpeg RTSP/1.0
Range: npt=30-60  # Segundos 30 a 60
```

## Resumo do Protocolo RTSP

### Pontos-Chave

1. **Protocolo de controle** (não transporta mídia)
2. **Stateful** (mantém estado da sessão)
3. **Baseado em texto** (similar a HTTP)
4. **Session IDs** identificam sessões
5. **CSeq** correlaciona requisições/respostas
6. **Máquina de estados** controla transições
7. **TCP** garante confiabilidade

### Comandos Essenciais

```
SETUP → Inicializa sessão
PLAY → Inicia streaming
PAUSE → Pausa streaming
TEARDOWN → Encerra sessão
```

---

**Próximo:** [05-QOS.md](05-QOS.md) - Quality of Service Implementado
