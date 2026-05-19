# 06 - Fluxo de Execução Completo do Sistema

## Visão Geral

Este documento detalha o fluxo completo de execução do sistema de streaming, desde a inicialização até o encerramento, com análise linha por linha do código.

## Fase 1: Inicialização do Servidor

### 1.1 Execução do Servidor

**Comando:**
```bash
python Server.py 554
```

**Código (Server.py):**

```python
if __name__ == "__main__":
    (Server()).main()
```

**Análise:**
```python
# 1. Cria instância da classe Server
server = Server()

# 2. Chama método main()
server.main()
```

### 1.2 Método main() do Servidor

**Código:**

```python
def main(self):
    try:
        SERVER_PORT = int(sys.argv[1])
    except:
        print("[Uso: Server.py Porta_Servidor]\n")
    
    rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    rtspSocket.bind(('', SERVER_PORT))
    rtspSocket.listen(5)
    
    while True:
        clientInfo = {}
        clientInfo['rtspSocket'] = rtspSocket.accept()
        ServerWorker(clientInfo).run()
```

**Fluxo Detalhado:**

```
Passo 1: Obter porta da linha de comando
  │
  ├─ sys.argv[1] = "554"
  ├─ SERVER_PORT = 554
  │
Passo 2: Criar socket TCP
  │
  ├─ socket.AF_INET = IPv4
  ├─ socket.SOCK_STREAM = TCP
  ├─ rtspSocket criado
  │
Passo 3: Bind (associar) socket à porta
  │
  ├─ bind(('', 554))
  ├─ '' = todas as interfaces de rede
  ├─ Servidor agora escuta na porta 554
  │
Passo 4: Listen (aguardar conexões)
  │
  ├─ listen(5)
  ├─ Aceita até 5 conexões pendentes
  │
Passo 5: Loop infinito
  │
  ├─ while True:
  │   │
  │   ├─ Aguarda conexão de cliente
  │   │   rtspSocket.accept() [BLOQUEANTE]
  │   │
  │   ├─ Cliente conecta
  │   │   clientInfo['rtspSocket'] = (connSocket, clientAddr)
  │   │
  │   ├─ Cria ServerWorker para este cliente
  │   │   worker = ServerWorker(clientInfo)
  │   │
  │   └─ Inicia worker
  │       worker.run()
  │
  └─ Volta ao início do loop (aguarda próximo cliente)
```

**Estado do Servidor:**
```
┌─────────────────────────────────────┐
│ Servidor Iniciado                   │
│ Porta: 554                          │
│ Estado: Aguardando conexões         │
│ Socket: Escutando                   │
└─────────────────────────────────────┘
```

## Fase 2: Inicialização do Cliente

### 2.1 Execução do Cliente

**Comando:**
```bash
python ClientLauncher.py
```

**Código (ClientLauncher.py):**

```python
if __name__ == "__main__":
    serverAddr = "127.0.0.1"
    serverPort = 554
    rtpPort = 5004
    fileName = "movie.Mjpeg"
    
    root = Tk()
    
    app = Client(root, serverAddr, serverPort, rtpPort, fileName)
    app.master.title("RTPClient")
    root.mainloop()
```

**Fluxo:**

```
Passo 1: Definir parâmetros
  │
  ├─ serverAddr = "127.0.0.1" (localhost)
  ├─ serverPort = 554 (porta RTSP)
  ├─ rtpPort = 5004 (porta para receber RTP)
  ├─ fileName = "movie.Mjpeg"
  │
Passo 2: Criar janela Tkinter
  │
  ├─ root = Tk()
  ├─ Janela principal criada
  │
Passo 3: Criar instância do Cliente
  │
  ├─ app = Client(root, serverAddr, serverPort, rtpPort, fileName)
  ├─ Chama __init__ do Cliente
  │
Passo 4: Configurar título
  │
  ├─ app.master.title("RTPClient")
  │
Passo 5: Iniciar loop de eventos
  │
  └─ root.mainloop()
      └─ Aguarda interação do usuário
```

### 2.2 Construtor do Cliente

**Código (Client.py):**

```python
def __init__(self, master, serveraddr, serverport, rtpport, filename):
    self.master = master
    self.master.protocol("WM_DELETE_WINDOW", self.handler)
    self.createWidgets()
    self.serverAddr = serveraddr
    self.serverPort = int(serverport)
    self.rtpPort = int(rtpport)
    self.fileName = filename
    self.rtspSeq = 0
    self.sessionId = 0
    self.requestSent = -1
    self.teardownAcked = 0
    self.connectToServer()
    self.frameNbr = 0
    self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
```

**Fluxo Detalhado:**

```
Passo 1: Armazenar referências
  │
  ├─ self.master = root (janela Tkinter)
  │
Passo 2: Configurar handler de fechamento
  │
  ├─ protocol("WM_DELETE_WINDOW", self.handler)
  ├─ Quando usuário fechar janela, chama self.handler
  │
Passo 3: Criar interface gráfica
  │
  ├─ self.createWidgets()
  ├─ Cria botões: Setup, Play, Pause, Teardown
  ├─ Cria label para exibir vídeo
  │
Passo 4: Armazenar parâmetros
  │
  ├─ self.serverAddr = "127.0.0.1"
  ├─ self.serverPort = 554
  ├─ self.rtpPort = 5004
  ├─ self.fileName = "movie.Mjpeg"
  │
Passo 5: Inicializar variáveis de controle
  │
  ├─ self.rtspSeq = 0 (número de sequência RTSP)
  ├─ self.sessionId = 0 (ID da sessão)
  ├─ self.requestSent = -1 (último comando enviado)
  ├─ self.teardownAcked = 0 (flag de teardown)
  │
Passo 6: Conectar ao servidor
  │
  ├─ self.connectToServer()
  ├─ Cria socket TCP
  ├─ Conecta a 127.0.0.1:554
  │
Passo 7: Inicializar variáveis RTP
  │
  ├─ self.frameNbr = 0 (último frame recebido)
  ├─ self.rtpSocket = socket UDP (para receber RTP)
  │
Estado: INIT
```

### 2.3 Conexão ao Servidor

**Código:**

```python
def connectToServer(self):
    self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        self.rtspSocket.connect((self.serverAddr, self.serverPort))
    except:
        tkMessageBox.showwarning('Conexão Falhou', 
                                 'Conexão com \'%s\' falhou.' % self.serverAddr)
```

**Fluxo:**

```
Cliente                                 Servidor
  │                                       │
  │ 1. Cria socket TCP                    │
  │    rtspSocket = socket(TCP)           │
  │                                       │
  │ 2. Conecta ao servidor                │
  │    connect(127.0.0.1:554)             │
  ├──────────────────────────────────────►│
  │                                       │ 3. accept() retorna
  │                                       │    (connSocket, clientAddr)
  │                                       │
  │                                       │ 4. Cria ServerWorker
  │                                       │    worker = ServerWorker(clientInfo)
  │                                       │
  │                                       │ 5. Inicia thread
  │                                       │    worker.run()
  │                                       │      └─► Thread recvRtspRequest()
  │                                       │
  │ Conexão estabelecida                  │ Aguardando comandos RTSP
```

**Estado após conexão:**

```
Cliente:
  - Socket TCP conectado
  - Estado: INIT
  - Aguardando usuário clicar "Setup"

Servidor:
  - Thread recvRtspRequest rodando
  - Estado: INIT
  - Aguardando comando SETUP
```

## Fase 3: Comando SETUP

### 3.1 Usuário Clica "Setup"

**Código (Client.py):**

```python
def setupMovie(self):
    if self.state == self.INIT:
        self.sendRtspRequest(self.SETUP)
```

**Fluxo:**

```
Usuário clica botão "Setup"
  │
  ├─ setupMovie() chamado
  │
  ├─ Verifica estado
  │   if self.state == self.INIT:
  │
  └─ Envia requisição SETUP
      self.sendRtspRequest(self.SETUP)
```

### 3.2 Envio da Requisição SETUP

**Código:**

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

**Fluxo Detalhado:**

```
Passo 1: Iniciar thread de recepção
  │
  ├─ threading.Thread(target=self.recvRtspReply).start()
  ├─ Nova thread criada
  ├─ Thread aguarda respostas RTSP
  │
Passo 2: Definir CSeq
  │
  ├─ self.rtspSeq = 1
  │
Passo 3: Construir mensagem RTSP
  │
  ├─ request = "SETUP movie.Mjpeg\n 1 \n RTSP/1.0 RTP/UDP 5004"
  │
Passo 4: Enviar via TCP
  │
  ├─ self.rtspSocket.send(request.encode())
  │
Passo 5: Marcar comando enviado
  │
  └─ self.requestSent = self.SETUP
```

**Mensagem RTSP enviada:**
```
SETUP movie.Mjpeg
 1 
 RTSP/1.0 RTP/UDP 5004
```

### 3.3 Servidor Recebe SETUP

**Thread recvRtspRequest (ServerWorker.py):**

```python
def recvRtspRequest(self):
    connSocket = self.clientInfo['rtspSocket'][0]
    while True:
        data = connSocket.recv(256)
        if data:
            print("Dados recebidos:\n" + data.decode("utf-8"))
            self.processRtspRequest(data.decode("utf-8"))
```

**Fluxo:**

```
Thread recvRtspRequest rodando
  │
  ├─ data = connSocket.recv(256) [BLOQUEANTE]
  │
  ├─ Cliente envia SETUP
  │   data = b"SETUP movie.Mjpeg\n 1 \n RTSP/1.0 RTP/UDP 5004"
  │
  ├─ Imprime dados recebidos
  │
  └─ Processa requisição
      self.processRtspRequest(data.decode("utf-8"))
```

### 3.4 Processamento do SETUP

**Código:**

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

**Fluxo Detalhado:**

```
Passo 1: Parse da requisição
  │
  ├─ request = ["SETUP movie.Mjpeg", " 1 ", " RTSP/1.0 RTP/UDP 5004"]
  ├─ line1 = ["SETUP", "movie.Mjpeg"]
  ├─ requestType = "SETUP"
  ├─ filename = "movie.Mjpeg"
  ├─ seq = [" ", "1", " "]
  │
Passo 2: Verificar tipo de requisição
  │
  ├─ if requestType == self.SETUP:
  │
Passo 3: Verificar estado
  │
  ├─ if self.state == self.INIT:
  │
Passo 4: Abrir arquivo de vídeo
  │
  ├─ try:
  │     self.clientInfo['videoStream'] = VideoStream("movie.Mjpeg")
  │     │
  │     ├─ VideoStream.__init__("movie.Mjpeg")
  │     ├─ self.file = open("movie.Mjpeg", 'rb')
  │     ├─ self.frameNum = 0
  │     │
  │     └─ Arquivo aberto com sucesso
  │
  ├─ self.state = self.READY
  │
Passo 5: Gerar Session ID
  │
  ├─ self.clientInfo['session'] = randint(100000, 999999)
  ├─ Exemplo: session = 456789
  │
Passo 6: Enviar resposta OK
  │
  ├─ self.replyRtsp(self.OK_200, seq[1])
  │   │
  │   ├─ reply = "RTSP/1.0 200 OK\nCSeq: 1\nSession: 456789"
  │   ├─ connSocket.send(reply.encode())
  │
Passo 7: Extrair porta RTP do cliente
  │
  └─ self.clientInfo['rtpPort'] = "5004"
```

**Resposta RTSP enviada:**
```
RTSP/1.0 200 OK
CSeq: 1
Session: 456789
```

### 3.5 Cliente Recebe Resposta SETUP

**Thread recvRtspReply (Client.py):**

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

**Fluxo:**

```
Thread recvRtspReply rodando
  │
  ├─ reply = self.rtspSocket.recv(1024) [BLOQUEANTE]
  │
  ├─ Servidor envia resposta
  │   reply = b"RTSP/1.0 200 OK\nCSeq: 1\nSession: 456789"
  │
  └─ Processa resposta
      self.parseRtspReply(reply.decode("utf-8"))
```

### 3.6 Parse da Resposta SETUP

**Código:**

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
```

**Fluxo Detalhado:**

```
Passo 1: Parse da resposta
  │
  ├─ lines = ["RTSP/1.0 200 OK", "CSeq: 1", "Session: 456789"]
  ├─ seqNum = 1
  │
Passo 2: Verificar CSeq
  │
  ├─ if seqNum == self.rtspSeq: (1 == 1)
  │
Passo 3: Extrair Session ID
  │
  ├─ session = 456789
  │
Passo 4: Armazenar Session ID (primeira vez)
  │
  ├─ if self.sessionId == 0:
  ├─   self.sessionId = 456789
  │
Passo 5: Verificar código de status
  │
  ├─ statusCode = 200
  ├─ if statusCode == 200:
  │
Passo 6: Processar SETUP
  │
  ├─ if self.requestSent == self.SETUP:
  │
Passo 7: Atualizar estado
  │
  ├─ self.state = self.READY
  │
Passo 8: Abrir porta RTP
  │
  └─ self.openRtpPort()
      │
      ├─ self.rtpSocket.settimeout(0.5)
      ├─ self.rtpSocket.bind(("127.0.0.1", 5004))
      └─ Porta RTP aberta e pronta para receber
```

**Estado após SETUP:**

```
Cliente:
  - Estado: READY
  - Session ID: 456789
  - Porta RTP: 5004 (aberta e aguardando)
  - Botão "Play" habilitado

Servidor:
  - Estado: READY
  - Session ID: 456789
  - Arquivo: movie.Mjpeg (aberto)
  - Porta RTP do cliente: 5004
  - Aguardando comando PLAY
```

## Fase 4: Comando PLAY

### 4.1 Usuário Clica "Play"

**Código:**

```python
def playMovie(self):
    if self.state == self.READY:
        threading.Thread(target=self.listenRtp).start()
        self.playEvent = threading.Event()
        self.playEvent.clear()
        self.sendRtspRequest(self.PLAY)
```

**Fluxo:**

```
Usuário clica botão "Play"
  │
  ├─ playMovie() chamado
  │
  ├─ Verifica estado
  │   if self.state == self.READY:
  │
  ├─ Inicia thread de recepção RTP
  │   threading.Thread(target=self.listenRtp).start()
  │
  ├─ Cria Event para controle
  │   self.playEvent = threading.Event()
  │   self.playEvent.clear()
  │
  └─ Envia requisição PLAY
      self.sendRtspRequest(self.PLAY)
```

### 4.2 Envio da Requisição PLAY

**Código:**

```python
elif requestCode == self.PLAY and self.state == self.READY:
    self.rtspSeq = self.rtspSeq + 1
    
    request = "PLAY " + "\n " + str(self.rtspSeq)
    self.rtspSocket.send(request.encode("utf-8"))
    print('-'*60 + "\nSolicitação PLAY enviada ao Servidor...\n" + '-'*60)
    
    self.requestSent = self.PLAY
```

**Mensagem RTSP enviada:**
```
PLAY 
 2
```

### 4.3 Servidor Processa PLAY

**Código:**

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

**Fluxo Detalhado:**

```
Passo 1: Mudar estado
  │
  ├─ self.state = self.PLAYING
  │
Passo 2: Criar socket UDP para RTP
  │
  ├─ rtpSocket = socket(AF_INET, SOCK_DGRAM)
  │
Passo 3: Configurar QoS
  │
  ├─ rtpSocket.setsockopt(IPPROTO_IP, IP_TOS, 0xB8)
  ├─ DSCP = 46 (EF - Expedited Forwarding)
  │
Passo 4: Enviar resposta OK
  │
  ├─ reply = "RTSP/1.0 200 OK\nCSeq: 2\nSession: 456789"
  ├─ connSocket.send(reply.encode())
  │
Passo 5: Criar Event para controle
  │
  ├─ event = threading.Event()
  │
Passo 6: Iniciar thread de envio RTP
  │
  └─ worker = threading.Thread(target=self.sendRtp)
      worker.start()
```

### 4.4 Thread sendRtp (Servidor)

**Código:**

```python
def sendRtp(self):
    while True:
        self.clientInfo['event'].wait(0.05)
        
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

**Fluxo Contínuo:**

```
Loop infinito de envio
  │
  ├─ Aguarda 50ms (20 FPS)
  │   event.wait(0.05)
  │
  ├─ Verifica se deve parar
  │   if event.isSet(): break
  │
  ├─ Lê próximo frame
  │   data = videoStream.nextFrame()
  │   │
  │   ├─ Lê 5 bytes (tamanho)
  │   ├─ Lê N bytes (JPEG)
  │   └─ frameNum += 1
  │
  ├─ Se frame existe:
  │   │
  │   ├─ frameNumber = videoStream.frameNbr()
  │   │
  │   ├─ Cria pacote RTP
  │   │   packet = makeRtp(data, frameNumber)
  │   │   │
  │   │   ├─ rtpPacket = RtpPacket()
  │   │   ├─ rtpPacket.encode(version=2, padding=0, extension=0,
  │   │   │                    cc=0, seqnum=frameNumber, marker=0,
  │   │   │                    pt=26, ssrc=0, payload=data)
  │   │   │
  │   │   └─ return rtpPacket.getPacket()
  │   │
  │   └─ Envia via UDP
  │       rtpSocket.sendto(packet, ("127.0.0.1", 5004))
  │
  └─ Volta ao início do loop
```

**Exemplo de envio:**

```
Frame 1:
  ├─ Lê frame JPEG (15234 bytes)
  ├─ Cria pacote RTP:
  │   [12 bytes header][15234 bytes payload]
  ├─ Envia via UDP para 127.0.0.1:5004
  │
Aguarda 50ms
  │
Frame 2:
  ├─ Lê frame JPEG (14987 bytes)
  ├─ Cria pacote RTP:
  │   [12 bytes header][14987 bytes payload]
  ├─ Envia via UDP para 127.0.0.1:5004
  │
Aguarda 50ms
  │
Frame 3:
  ...
```

### 4.5 Cliente Recebe Resposta PLAY

**Parse da resposta:**

```python
elif self.requestSent == self.PLAY:
    self.state = self.PLAYING
    print('-'*60 + "\nCliente está PLAYING...\n" + '-'*60)
```

**Estado atualizado:**
```
Cliente:
  - Estado: PLAYING
  - Thread listenRtp rodando
  - Aguardando pacotes RTP
```

### 4.6 Thread listenRtp (Cliente)

**Código:**

```python
def listenRtp(self):
    while True:
        try:
            data = self.rtpSocket.recv(20480)
            if data:
                rtpPacket = RtpPacket()
                rtpPacket.decode(data)
                
                currFrameNbr = rtpPacket.seqNum()
                print("Número de sequência atual: " + str(currFrameNbr))
                
                if currFrameNbr > self.frameNbr:
                    self.frameNbr = currFrameNbr
                    self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
        except:
            if self.playEvent.isSet():
                break
            
            if self.teardownAcked == 1:
                self.rtpSocket.shutdown(socket.SHUT_RDWR)
                self.rtpSocket.close()
                break
```

**Fluxo Contínuo:**

```
Loop infinito de recepção
  │
  ├─ Aguarda pacote UDP
  │   data = rtpSocket.recv(20480) [BLOQUEANTE]
  │
  ├─ Servidor envia pacote RTP
  │   data = [12 bytes header][15234 bytes JPEG]
  │
  ├─ Decodifica pacote RTP
  │   rtpPacket = RtpPacket()
  │   rtpPacket.decode(data)
  │   │
  │   ├─ header = data[0:12]
  │   └─ payload = data[12:]
  │
  ├─ Extrai número de sequência
  │   currFrameNbr = rtpPacket.seqNum()
  │   │
  │   ├─ seqNum = header[2] << 8 | header[3]
  │   └─ return seqNum (ex: 1)
  │
  ├─ Verifica se não é pacote atrasado
  │   if currFrameNbr > self.frameNbr: (1 > 0)
  │
  ├─ Atualiza último frame recebido
  │   self.frameNbr = 1
  │
  ├─ Extrai payload
  │   payload = rtpPacket.getPayload()
  │   payload = [15234 bytes de JPEG]
  │
  ├─ Escreve frame em arquivo cache
  │   cacheFile = writeFrame(payload)
  │   │
  │   ├─ cachename = "cache-456789.jpg"
  │   ├─ file = open(cachename, "wb")
  │   ├─ file.write(payload)
  │   ├─ file.close()
  │   └─ return cachename
  │
  ├─ Atualiza display
  │   updateMovie(cacheFile)
  │   │
  │   ├─ photo = ImageTk.PhotoImage(Image.open(cacheFile))
  │   ├─ label.configure(image=photo, height=288)
  │   └─ label.image = photo
  │
  └─ Volta ao início do loop (aguarda próximo frame)
```

**Visualização do fluxo:**

```
Servidor                          Cliente
  │                                 │
  │ Frame 1 (RTP)                   │
  ├════════════════════════════════►│
  │                                 ├─ Decodifica
  │                                 ├─ Escreve cache-456789.jpg
  │                                 └─ Exibe na tela
  │                                 │
  │ 50ms depois                     │
  │                                 │
  │ Frame 2 (RTP)                   │
  ├════════════════════════════════►│
  │                                 ├─ Decodifica
  │                                 ├─ Sobrescreve cache-456789.jpg
  │                                 └─ Atualiza tela
  │                                 │
  │ 50ms depois                     │
  │                                 │
  │ Frame 3 (RTP)                   │
  ├════════════════════════════════►│
  │                                 ├─ Decodifica
  │                                 ├─ Sobrescreve cache-456789.jpg
  │                                 └─ Atualiza tela
  │                                 │
  ...                               ...
```

## Fase 5: Comando PAUSE

### 5.1 Usuário Clica "Pause"

**Código:**

```python
def pauseMovie(self):
    if self.state == self.PLAYING:
        self.sendRtspRequest(self.PAUSE)
```

### 5.2 Cliente Envia PAUSE

**Mensagem RTSP:**
```
PAUSE 
 3
```

### 5.3 Servidor Processa PAUSE

**Código:**

```python
elif requestType == self.PAUSE:
    if self.state == self.PLAYING:
        print("Processando PAUSE\n")
        self.state = self.READY
        
        self.clientInfo['event'].set()
        
        self.replyRtsp(self.OK_200, seq[1])
```

**Fluxo:**

```
Passo 1: Mudar estado
  │
  ├─ self.state = self.READY
  │
Passo 2: Sinalizar thread para parar
  │
  ├─ event.set()
  │
Passo 3: Enviar resposta OK
  │
  └─ reply = "RTSP/1.0 200 OK\nCSeq: 3\nSession: 456789"
```

**Efeito na thread sendRtp:**

```
Loop de envio
  │
  ├─ event.wait(0.05)
  │
  ├─ Verifica se deve parar
  │   if event.isSet(): (True)
  │
  └─ break (encerra loop, thread termina)
```

### 5.4 Cliente Processa Resposta PAUSE

**Código:**

```python
elif self.requestSent == self.PAUSE:
    self.state = self.READY
    self.playEvent.set()
```

**Efeito na thread listenRtp:**

```
Loop de recepção
  │
  ├─ recv(20480) [timeout após 0.5s]
  │
  ├─ Timeout (servidor parou de enviar)
  │
  ├─ except:
  │   if self.playEvent.isSet(): (True)
  │
  └─ break (encerra loop, thread termina)
```

**Estado após PAUSE:**

```
Cliente:
  - Estado: READY
  - Thread listenRtp encerrada
  - Último frame congelado na tela

Servidor:
  - Estado: READY
  - Thread sendRtp encerrada
  - Arquivo de vídeo ainda aberto
```

## Fase 6: Comando TEARDOWN

### 6.1 Usuário Clica "Teardown"

**Código:**

```python
def exitClient(self):
    self.sendRtspRequest(self.TEARDOWN)
    self.master.destroy()
    os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT)
```

### 6.2 Cliente Envia TEARDOWN

**Mensagem RTSP:**
```
TEARDOWN 
 4
```

### 6.3 Servidor Processa TEARDOWN

**Código:**

```python
elif requestType == self.TEARDOWN:
    print("Processando TEARDOWN\n")
    
    self.clientInfo['event'].set()
    
    self.replyRtsp(self.OK_200, seq[1])
    
    self.clientInfo['rtpSocket'].close()
```

**Fluxo:**

```
Passo 1: Sinalizar thread (se ainda rodando)
  │
  ├─ event.set()
  │
Passo 2: Enviar resposta OK
  │
  ├─ reply = "RTSP/1.0 200 OK\nCSeq: 4\nSession: 456789"
  │
Passo 3: Fechar socket RTP
  │
  └─ rtpSocket.close()
```

### 6.4 Cliente Processa Resposta TEARDOWN

**Código:**

```python
elif self.requestSent == self.TEARDOWN:
    self.state = self.INIT
    self.teardownAcked = 1
```

**Thread recvRtspReply:**

```python
if self.requestSent == self.TEARDOWN:
    self.rtspSocket.shutdown(socket.SHUT_RDWR)
    self.rtspSocket.close()
    break
```

**Limpeza final:**

```python
self.master.destroy()  # Fecha janela GUI
os.remove("cache-456789.jpg")  # Remove arquivo cache
```

**Estado final:**

```
Cliente:
  - Estado: INIT
  - Todas as threads encerradas
  - Sockets fechados
  - Cache removido
  - Janela fechada

Servidor:
  - Thread recvRtspRequest encerrada (cliente desconectou)
  - Socket RTP fechado
  - Aguardando próximo cliente
```

## Resumo do Fluxo Completo

```
1. Servidor inicia → Aguarda conexões na porta 554

2. Cliente inicia → Conecta ao servidor via TCP

3. SETUP:
   Cliente → SETUP → Servidor
   Servidor → Abre arquivo, gera Session ID
   Servidor → 200 OK → Cliente
   Cliente → Abre porta RTP, estado READY

4. PLAY:
   Cliente → PLAY → Servidor
   Servidor → Cria socket UDP, configura QoS
   Servidor → 200 OK → Cliente
   Servidor → Inicia thread sendRtp
   Cliente → Inicia thread listenRtp
   Servidor ═══ Pacotes RTP ═══► Cliente
   Cliente → Decodifica e exibe frames

5. PAUSE:
   Cliente → PAUSE → Servidor
   Servidor → Para thread sendRtp
   Servidor → 200 OK → Cliente
   Cliente → Para thread listenRtp

6. TEARDOWN:
   Cliente → TEARDOWN → Servidor
   Servidor → Fecha socket RTP
   Servidor → 200 OK → Cliente
   Cliente → Fecha sockets, remove cache, encerra
```

---