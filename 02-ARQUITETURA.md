# 02 - Arquitetura do Sistema de Streaming

## Visão Geral da Arquitetura

Este documento detalha a arquitetura completa do sistema de streaming RTP/RTSP, explicando como cada componente interage e suas responsabilidades.

## Arquitetura em Camadas

### Modelo de 3 Camadas

```
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE APRESENTAÇÃO                   │
│                                                             │
│  ┌──────────────────────────────────────────────────┐      │
│  │         Interface Gráfica (Tkinter)              │      │
│  │  [Setup] [Play] [Pause] [Teardown] [Display]    │      │
│  └──────────────────────────────────────────────────┘      │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE APLICAÇÃO                      │
│                                                             │
│  ┌─────────────────────┐      ┌──────────────────────┐     │
│  │   Cliente RTSP      │      │   Servidor RTSP      │     │
│  │  - Envia comandos   │◄────►│  - Processa comandos │     │
│  │  - Recebe respostas │      │  - Gerencia sessões  │     │
│  └─────────────────────┘      └──────────────────────┘     │
│                                                             │
│  ┌─────────────────────┐      ┌──────────────────────┐     │
│  │   Receptor RTP      │      │   Transmissor RTP    │     │
│  │  - Decodifica       │◄════►│  - Codifica          │     │
│  │  - Reordena         │      │  - Fragmenta         │     │
│  └─────────────────────┘      └──────────────────────┘     │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    CAMADA DE TRANSPORTE                     │
│                                                             │
│         TCP (RTSP)                  UDP (RTP)              │
│    Porta 554 (padrão)           Porta 5004 (negociada)    │
└─────────────────────────────────────────────────────────────┘
```

## Componentes do Sistema

### 1. Servidor (Server.py)

**Responsabilidade:** Ponto de entrada do servidor, aceita conexões de clientes.

**Código Relevante:**
```python
class Server:
    def main(self):
        SERVER_PORT = int(sys.argv[1])  # Porta RTSP (554)
        rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rtspSocket.bind(('', SERVER_PORT))
        rtspSocket.listen(5)  # Aceita até 5 conexões pendentes
        
        while True:
            clientInfo = {}
            clientInfo['rtspSocket'] = rtspSocket.accept()
            ServerWorker(clientInfo).run()
```

**Características:**
- Socket TCP para RTSP
- Loop infinito aceitando conexões
- Cria um ServerWorker para cada cliente
- Suporta múltiplos clientes simultâneos

**Diagrama de Fluxo:**
```
Início
  │
  ▼
Cria socket TCP na porta 554
  │
  ▼
Aguarda conexão ◄─────┐
  │                   │
  │ Cliente conecta   │
  ▼                   │
Aceita conexão        │
  │                   │
  ▼                   │
Cria ServerWorker     │
  │                   │
  ▼                   │
Inicia thread ────────┘
```

### 2. ServerWorker (ServerWorker.py)

**Responsabilidade:** Gerencia a sessão de um cliente específico.

**Máquina de Estados:**
```
┌──────┐  SETUP   ┌───────┐  PLAY    ┌─────────┐
│ INIT │─────────►│ READY │─────────►│ PLAYING │
└──────┘          └───────┘          └─────────┘
                      ▲                    │
                      │       PAUSE        │
                      └────────────────────┘
                      │
                      │ TEARDOWN
                      ▼
                  ┌──────┐
                  │ INIT │
                  └──────┘
```

**Estrutura de Dados do Cliente:**
```python
clientInfo = {
    'rtspSocket': (connSocket, clientAddr),  # Socket TCP RTSP
    'rtpSocket': udpSocket,                  # Socket UDP RTP
    'videoStream': VideoStream(filename),    # Stream de vídeo
    'session': 123456,                       # ID da sessão
    'rtpPort': 5004,                         # Porta RTP do cliente
    'event': threading.Event(),              # Controle de thread
    'worker': threading.Thread()             # Thread de envio RTP
}
```

**Processamento de Comandos:**

```
┌─────────────────────────────────────────────────────────┐
│              Recebe Comando RTSP                        │
└─────────────────────────────────────────────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ Qual comando?   │
              └─────────────────┘
                        │
        ┌───────────────┼───────────────┬──────────────┐
        │               │               │              │
        ▼               ▼               ▼              ▼
    ┌──────┐       ┌──────┐       ┌───────┐     ┌──────────┐
    │SETUP │       │ PLAY │       │ PAUSE │     │TEARDOWN  │
    └──────┘       └──────┘       └───────┘     └──────────┘
        │               │               │              │
        ▼               ▼               ▼              ▼
  Abre arquivo   Inicia thread   Para thread    Fecha socket
  Cria sessão    Envia RTP       RTP            Libera recursos
  Responde OK    Responde OK     Responde OK    Responde OK
```

**Código de Processamento SETUP:**
```python
if requestType == self.SETUP:
    if self.state == self.INIT:
        # 1. Abre arquivo de vídeo
        self.clientInfo['videoStream'] = VideoStream(filename)
        self.state = self.READY
        
        # 2. Gera ID de sessão aleatório
        self.clientInfo['session'] = randint(100000, 999999)
        
        # 3. Envia resposta OK
        self.replyRtsp(self.OK_200, seq[1])
        
        # 4. Extrai porta RTP do cliente
        self.clientInfo['rtpPort'] = request[2].split(' ')[3]
```

**Código de Processamento PLAY:**
```python
if requestType == self.PLAY:
    if self.state == self.READY:
        self.state = self.PLAYING
        
        # 1. Cria socket UDP para RTP
        self.clientInfo["rtpSocket"] = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM
        )
        
        # 2. Configura QoS (DSCP = EF)
        self.clientInfo["rtpSocket"].setsockopt(
            socket.IPPROTO_IP, socket.IP_TOS, 0xB8
        )
        
        # 3. Responde OK
        self.replyRtsp(self.OK_200, seq[1])
        
        # 4. Inicia thread de envio RTP
        self.clientInfo['event'] = threading.Event()
        self.clientInfo['worker'] = threading.Thread(target=self.sendRtp)
        self.clientInfo['worker'].start()
```

**Thread de Envio RTP:**
```
Loop infinito
    │
    ▼
Aguarda 50ms (20 FPS)
    │
    ▼
Event está setado? ──Sim──► Break (para thread)
    │
    Não
    ▼
Lê próximo frame do arquivo
    │
    ▼
Frame existe? ──Não──► Break
    │
    Sim
    ▼
Cria pacote RTP
    │
    ▼
Envia via UDP para cliente
    │
    └──► Volta ao início
```

### 3. Cliente (Client.py)

**Responsabilidade:** Interface com usuário e coordenação de comunicação.

**Estrutura de Threads:**
```
┌─────────────────────────────────────────────────┐
│            Thread Principal (GUI)               │
│  - Renderiza interface                          │
│  - Processa eventos de botões                   │
│  - Atualiza display de vídeo                    │
└─────────────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
        ▼                       ▼
┌──────────────────┐   ┌──────────────────┐
│  Thread RTSP     │   │   Thread RTP     │
│  - Recebe        │   │   - Recebe       │
│    respostas     │   │     pacotes      │
│  - Atualiza      │   │   - Decodifica   │
│    estado        │   │   - Escreve      │
│                  │   │     cache        │
└──────────────────┘   └──────────────────┘
```

**Máquina de Estados do Cliente:**
```
Estado: INIT
  │
  │ Usuário clica "Setup"
  ▼
Envia SETUP ──► Recebe OK ──► Estado: READY
                                  │
                                  │ Usuário clica "Play"
                                  ▼
                            Envia PLAY ──► Recebe OK ──► Estado: PLAYING
                                                              │
                                                              │ Usuário clica "Pause"
                                                              ▼
                                                        Envia PAUSE ──► Estado: READY
```

**Código de Recepção RTP:**
```python
def listenRtp(self):
    while True:
        try:
            # 1. Recebe pacote UDP
            data = self.rtpSocket.recv(20480)
            
            if data:
                # 2. Decodifica pacote RTP
                rtpPacket = RtpPacket()
                rtpPacket.decode(data)
                
                # 3. Obtém número de sequência
                currFrameNbr = rtpPacket.seqNum()
                
                # 4. Descarta pacotes atrasados
                if currFrameNbr > self.frameNbr:
                    self.frameNbr = currFrameNbr
                    
                    # 5. Extrai payload (frame JPEG)
                    payload = rtpPacket.getPayload()
                    
                    # 6. Escreve em arquivo cache
                    cacheFile = self.writeFrame(payload)
                    
                    # 7. Atualiza display
                    self.updateMovie(cacheFile)
        except:
            # Para em caso de PAUSE ou TEARDOWN
            if self.playEvent.isSet():
                break
```

**Sistema de Cache:**
```
Pacote RTP recebido
        │
        ▼
Extrai payload (JPEG)
        │
        ▼
Escreve em cache-{sessionId}.jpg
        │
        ▼
PIL abre imagem
        │
        ▼
Converte para PhotoImage
        │
        ▼
Atualiza Label da GUI
        │
        ▼
Frame exibido na tela
```

### 4. RtpPacket (RtpPacket.py)

**Responsabilidade:** Codificação e decodificação de pacotes RTP.

**Estrutura do Pacote:**
```
┌────────────────────────────────────────────────┐
│              Cabeçalho RTP (12 bytes)          │
├────────────────────────────────────────────────┤
│  Byte 0: V(2) P(1) X(1) CC(4)                  │
│  Byte 1: M(1) PT(7)                            │
│  Bytes 2-3: Sequence Number                    │
│  Bytes 4-7: Timestamp                          │
│  Bytes 8-11: SSRC                              │
├────────────────────────────────────────────────┤
│              Payload (Frame JPEG)              │
│              Tamanho variável                  │
└────────────────────────────────────────────────┘
```

**Processo de Codificação (Servidor):**
```python
def encode(self, version, padding, extension, cc, seqnum, 
           marker, pt, ssrc, payload):
    timestamp = int(time())
    header = bytearray(HEADER_SIZE)
    
    # Byte 0: V(2) + P(1) + X(1) + CC(4)
    header[0] = version << 6          # Bits 7-6
    header[0] |= padding << 5         # Bit 5
    header[0] |= extension << 4       # Bit 4
    header[0] |= cc                   # Bits 3-0
    
    # Byte 1: M(1) + PT(7)
    header[1] = marker << 7           # Bit 7
    header[1] |= pt                   # Bits 6-0
    
    # Bytes 2-3: Sequence Number (16 bits)
    header[2] = seqnum >> 8           # Byte alto
    header[3] = seqnum & 0xFF         # Byte baixo
    
    # Bytes 4-7: Timestamp (32 bits)
    header[4] = (timestamp >> 24) & 0xFF
    header[5] = (timestamp >> 16) & 0xFF
    header[6] = (timestamp >> 8) & 0xFF
    header[7] = timestamp & 0xFF
    
    # Bytes 8-11: SSRC (32 bits)
    header[8] = ssrc >> 24
    header[9] = (ssrc >> 16) & 0xFF
    header[10] = (ssrc >> 8) & 0xFF
    header[11] = ssrc & 0xFF
    
    self.payload = payload
```

**Processo de Decodificação (Cliente):**
```python
def decode(self, byteStream):
    # Separa cabeçalho e payload
    self.header = bytearray(byteStream[:HEADER_SIZE])
    self.payload = byteStream[HEADER_SIZE:]

def seqNum(self):
    # Reconstrói número de sequência de 16 bits
    seqNum = self.header[2] << 8 | self.header[3]
    return int(seqNum)

def timestamp(self):
    # Reconstrói timestamp de 32 bits
    timestamp = (self.header[4] << 24 | 
                 self.header[5] << 16 | 
                 self.header[6] << 8 | 
                 self.header[7])
    return int(timestamp)
```

**Manipulação de Bits:**
```
Exemplo: Codificar Version=2, Padding=0, Extension=0, CC=0

Version = 2 (binário: 10)
  10 << 6 = 10000000

Padding = 0 (binário: 0)
  0 << 5 = 00000000

Extension = 0 (binário: 0)
  0 << 4 = 00000000

CC = 0 (binário: 0000)
  0 = 00000000

Byte 0 = 10000000 | 00000000 | 00000000 | 00000000
       = 10000000 (0x80 em hexadecimal)
```

### 5. VideoStream (VideoStream.py)

**Responsabilidade:** Leitura sequencial de frames do arquivo MJPEG.

**Formato do Arquivo MJPEG:**
```
┌─────────────────────────────────────────┐
│ Frame 1:                                │
│   5 bytes: tamanho do frame (ASCII)     │
│   N bytes: dados JPEG                   │
├─────────────────────────────────────────┤
│ Frame 2:                                │
│   5 bytes: tamanho do frame (ASCII)     │
│   N bytes: dados JPEG                   │
├─────────────────────────────────────────┤
│ Frame 3:                                │
│   ...                                   │
└─────────────────────────────────────────┘
```

**Exemplo Prático:**
```
Arquivo movie.Mjpeg:
  "15234" + [15234 bytes de JPEG] +
  "14987" + [14987 bytes de JPEG] +
  "15102" + [15102 bytes de JPEG] +
  ...
```

**Código de Leitura:**
```python
def nextFrame(self):
    # 1. Lê 5 bytes (tamanho do frame em ASCII)
    data = self.file.read(5)
    
    if data:
        # 2. Converte para inteiro
        framelength = int(data)
        
        # 3. Lê exatamente framelength bytes (frame JPEG)
        data = self.file.read(framelength)
        
        # 4. Incrementa contador
        self.frameNum += 1
        
    return data
```

**Fluxo de Leitura:**
```
Posição 0: Lê "15234"
           ↓
Posição 5: Lê 15234 bytes (Frame 1)
           ↓
Posição 15239: Lê "14987"
           ↓
Posição 15244: Lê 14987 bytes (Frame 2)
           ↓
...
```

## Fluxo de Dados Completo

### Visão Geral

```
┌──────────────────────────────────────────────────────────────┐
│                         CLIENTE                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  1. Usuário clica "Setup"                                    │
│     │                                                        │
│     ▼                                                        │
│  2. Client.sendRtspRequest(SETUP)                           │
│     │                                                        │
│     │ TCP (porta 554)                                        │
│     ├────────────────────────────────────────────────►      │
│                                                              │
│                         SERVIDOR                             │
│                                                              │
│     ◄────────────────────────────────────────────────┤      │
│     │ RTSP/1.0 200 OK + Session ID                          │
│     │                                                        │
│     ▼                                                        │
│  3. Cliente muda estado para READY                          │
│  4. Abre porta RTP (5004)                                   │
│                                                              │
│  5. Usuário clica "Play"                                    │
│     │                                                        │
│     ▼                                                        │
│  6. Client.sendRtspRequest(PLAY)                            │
│     │                                                        │
│     │ TCP                                                    │
│     ├────────────────────────────────────────────────►      │
│                                                              │
│     ◄────────────────────────────────────────────────┤      │
│     │ RTSP/1.0 200 OK                                       │
│     │                                                        │
│     ▼                                                        │
│  7. Cliente inicia thread listenRtp()                       │
│  8. Cliente muda estado para PLAYING                        │
│                                                              │
│     ◄════════════════════════════════════════════════┤      │
│     │ Pacotes RTP (UDP, porta 5004, DSCP=0xB8)             │
│     │ Frame 1, Frame 2, Frame 3...                          │
│     │                                                        │
│     ▼                                                        │
│  9. RtpPacket.decode()                                      │
│ 10. Extrai payload (JPEG)                                   │
│ 11. Escreve cache-{session}.jpg                             │
│ 12. Atualiza GUI com frame                                  │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### Detalhamento por Camada

**Camada de Aplicação (RTSP):**
```
Cliente                           Servidor
  │                                 │
  │ SETUP movie.Mjpeg              │
  │ CSeq: 1                         │
  │ Transport: RTP/UDP; port=5004   │
  ├────────────────────────────────►│
  │                                 │ ServerWorker.processRtspRequest()
  │                                 │   - Abre VideoStream
  │                                 │   - Gera Session ID
  │                                 │   - Muda estado para READY
  │                                 │
  │ RTSP/1.0 200 OK                │
  │ CSeq: 1                         │
  │ Session: 123456                 │
  │◄────────────────────────────────┤
  │                                 │
Client.parseRtspReply()             │
  - Extrai Session ID               │
  - Muda estado para READY          │
  - Abre porta RTP                  │
```

**Camada de Aplicação (RTP):**
```
Servidor                          Cliente
  │                                 │
ServerWorker.sendRtp()              │
  │                                 │
  ├─ VideoStream.nextFrame()        │
  │    - Lê 5 bytes (tamanho)       │
  │    - Lê N bytes (JPEG)          │
  │                                 │
  ├─ makeRtp(payload, frameNum)     │
  │    - RtpPacket.encode()         │
  │    - Cria cabeçalho 12 bytes    │
  │    - Anexa payload              │
  │                                 │
  │ [RTP Header][JPEG Data]         │
  ├════════════════════════════════►│
  │ UDP, porta 5004                 │
  │ DSCP = 0xB8 (EF)               │
  │                                 │
  │                                 ├─ Client.listenRtp()
  │                                 │    - Recebe pacote UDP
  │                                 │    - RtpPacket.decode()
  │                                 │    - Verifica seqNum
  │                                 │    - Extrai payload
  │                                 │    - writeFrame()
  │                                 │    - updateMovie()
```

**Camada de Transporte:**
```
TCP (RTSP - Controle)              UDP (RTP - Dados)
  │                                  │
  │ Porta 554                        │ Porta 5004
  │ Confiável                        │ Não confiável
  │ Ordenado                         │ Sem garantia de ordem
  │ Controle de fluxo                │ Sem controle de fluxo
  │ Baixo volume                     │ Alto volume
  │ Latência variável                │ Latência baixa
  │                                  │ QoS (DSCP = 0xB8)
```

## Sincronização e Concorrência

### Threads no Servidor

```
Thread Principal
  │
  │ Aceita conexão do Cliente 1
  ├──► ServerWorker 1
  │      │
  │      ├─► Thread recvRtspRequest (Cliente 1)
  │      │
  │      └─► Thread sendRtp (Cliente 1)
  │
  │ Aceita conexão do Cliente 2
  └──► ServerWorker 2
         │
         ├─► Thread recvRtspRequest (Cliente 2)
         │
         └─► Thread sendRtp (Cliente 2)
```

### Threads no Cliente

```
Thread Principal (GUI)
  │
  ├─► Thread recvRtspReply
  │     │
  │     └─► Aguarda respostas RTSP
  │          Atualiza estado do cliente
  │
  └─► Thread listenRtp
        │
        └─► Aguarda pacotes RTP
             Decodifica e exibe frames
```

### Mecanismos de Sincronização

**Event para Controle de Thread RTP:**
```python
# Servidor - Iniciar envio
self.clientInfo['event'] = threading.Event()
self.clientInfo['worker'] = threading.Thread(target=self.sendRtp)
self.clientInfo['worker'].start()

# Servidor - Parar envio (PAUSE/TEARDOWN)
self.clientInfo['event'].set()  # Sinaliza para parar

# Thread sendRtp - Verifica sinal
while True:
    self.clientInfo['event'].wait(0.05)  # Aguarda 50ms
    if self.clientInfo['event'].isSet():  # Verifica se deve parar
        break
    # Continua enviando...
```

**Event para Controle de Thread RTP no Cliente:**
```python
# Cliente - Iniciar recepção
self.playEvent = threading.Event()
self.playEvent.clear()
threading.Thread(target=self.listenRtp).start()

# Cliente - Parar recepção (PAUSE)
self.playEvent.set()

# Thread listenRtp - Verifica sinal
try:
    data = self.rtpSocket.recv(20480)
    # Processa...
except:
    if self.playEvent.isSet():
        break  # Para thread
```

## Tratamento de Erros

### No Servidor

```python
# Arquivo não encontrado
try:
    self.clientInfo['videoStream'] = VideoStream(filename)
except IOError:
    self.replyRtsp(self.FILE_NOT_FOUND_404, seq[1])

# Erro de conexão ao enviar RTP
try:
    self.clientInfo['rtpSocket'].sendto(packet, (address, port))
except:
    print("Erro de conexão")
```

### No Cliente

```python
# Falha ao conectar ao servidor
try:
    self.rtspSocket.connect((self.serverAddr, self.serverPort))
except:
    tkMessageBox.showwarning('Conexão Falhou', 
                             'Conexão com \'%s\' falhou.' % self.serverAddr)

# Falha ao abrir porta RTP
try:
    self.rtpSocket.bind((self.serverAddr, self.rtpPort))
except:
    tkMessageBox.showwarning('Não foi possível conectar', 
                             'Não foi possível conectar na PORTA=%d' % self.rtpPort)
```

## Gerenciamento de Recursos

### Alocação de Recursos

**No SETUP:**
- Abre arquivo de vídeo
- Gera Session ID
- Armazena porta RTP do cliente

**No PLAY:**
- Cria socket UDP
- Configura QoS
- Inicia thread de envio

### Liberação de Recursos

**No TEARDOWN:**
```python
# Servidor
self.clientInfo['event'].set()        # Para thread
self.clientInfo['rtpSocket'].close()  # Fecha socket UDP

# Cliente
self.rtpSocket.shutdown(socket.SHUT_RDWR)
self.rtpSocket.close()
os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
```

## Escalabilidade

### Suporte a Múltiplos Clientes

```
Servidor (Porta 554)
  │
  ├─► Cliente 1 (Session 123456)
  │     ├─► Thread RTSP
  │     └─► Thread RTP → Porta 5004
  │
  ├─► Cliente 2 (Session 789012)
  │     ├─► Thread RTSP
  │     └─► Thread RTP → Porta 5005
  │
  └─► Cliente 3 (Session 345678)
        ├─► Thread RTSP
        └─► Thread RTP → Porta 5006
```

**Isolamento por Cliente:**
- Cada cliente tem seu próprio `clientInfo`
- Threads independentes
- Sockets separados
- Session IDs únicos

## Resumo da Arquitetura

### Pontos-Chave

1. **Separação de Responsabilidades**: Cada módulo tem função específica
2. **Dois Canais**: TCP para controle, UDP para dados
3. **Máquina de Estados**: Controle rigoroso de transições
4. **Multithreading**: Operações simultâneas sem bloqueio
5. **QoS**: Priorização de tráfego RTP
6. **Escalabilidade**: Suporte a múltiplos clientes

### Fluxo Resumido

```
1. Cliente conecta (TCP)
2. SETUP → Servidor prepara recursos
3. PLAY → Servidor inicia envio RTP (UDP)
4. Cliente recebe e exibe frames
5. PAUSE → Servidor para envio
6. TEARDOWN → Servidor libera recursos
```

---

**Próximo:** [03-PROTOCOLO-RTP.md](03-PROTOCOLO-RTP.md) - Análise Profunda do Protocolo RTP
