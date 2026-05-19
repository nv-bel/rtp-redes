# 03 - Protocolo RTP: Análise Profunda da Implementação

## Introdução ao RTP

RTP (Real-time Transport Protocol) é o protocolo responsável por transportar dados de mídia em tempo real. Este documento analisa em profundidade a implementação prática no arquivo `RtpPacket.py`.

## Estrutura do Pacote RTP (RFC 3550)

### Cabeçalho Completo (12 bytes mínimo)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|V=2|P|X|  CC   |M|     PT      |       Sequence Number         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Timestamp                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|           Synchronization Source (SSRC) identifier            |
+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+=+
|            Contributing Source (CSRC) identifiers             |
|                             ....                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

### Detalhamento dos Campos

#### Byte 0: V, P, X, CC

```
Bit:  7   6 | 5 | 4 | 3   2   1   0
     +-----+---+---+---------------+
     |  V  | P | X |      CC       |
     +-----+---+---+---------------+
```

**V (Version) - 2 bits:**
- Valor: 2 (binário: 10)
- Identifica a versão do RTP
- Sempre 2 na RFC 3550

**P (Padding) - 1 bit:**
- Valor: 0 ou 1
- Indica se há bytes de padding no final do payload
- Usado para alinhar pacotes a múltiplos de 32 bits
- Neste projeto: sempre 0

**X (Extension) - 1 bit:**
- Valor: 0 ou 1
- Indica presença de cabeçalho de extensão
- Permite adicionar informações customizadas
- Neste projeto: sempre 0

**CC (CSRC Count) - 4 bits:**
- Valor: 0 a 15
- Número de identificadores CSRC que seguem o cabeçalho fixo
- CSRC = Contributing Source (fontes que contribuíram para o stream)
- Neste projeto: sempre 0 (sem fontes contribuintes)

#### Byte 1: M, PT

```
Bit:  7 | 6   5   4   3   2   1   0
     +---+-------------------------+
     | M |          PT             |
     +---+-------------------------+
```

**M (Marker) - 1 bit:**
- Valor: 0 ou 1
- Significado depende do perfil da aplicação
- Pode indicar: fim de frame, início de fala, etc.
- Neste projeto: sempre 0

**PT (Payload Type) - 7 bits:**
- Valor: 0 a 127
- Identifica o formato do payload (codec)
- Valores padronizados pela RFC 3551
- Neste projeto: 26 (MJPEG)

**Tabela de Payload Types Comuns:**
| PT | Codec | Descrição |
|----|-------|-----------|
| 0  | PCMU  | Áudio G.711 μ-law |
| 8  | PCMA  | Áudio G.711 A-law |
| 26 | JPEG  | Vídeo MJPEG       |
| 31 | H261  | Vídeo H.261       |
| 32 | MPV   | Vídeo MPEG-1/2    |
| 96-127 | Dinâmico | Definido pela aplicação |

#### Bytes 2-3: Sequence Number

```
Byte 2:  Bits 15-8 (byte alto)
Byte 3:  Bits 7-0  (byte baixo)
```

**Sequence Number - 16 bits:**
- Valor: 0 a 65535 (depois volta para 0)
- Incrementado em 1 para cada pacote RTP enviado
- Usado para:
  - Detectar perda de pacotes
  - Reordenar pacotes fora de ordem
  - Detectar duplicatas

**Exemplo:**
```
Pacote 1: seqNum = 100
Pacote 2: seqNum = 101
Pacote 3: seqNum = 102
[Pacote 4 perdido]
Pacote 5: seqNum = 104  ← Cliente detecta perda (103 faltando)
```

#### Bytes 4-7: Timestamp

```
Byte 4:  Bits 31-24
Byte 5:  Bits 23-16
Byte 6:  Bits 15-8
Byte 7:  Bits 7-0
```

**Timestamp - 32 bits:**
- Valor: 0 a 4294967295
- Reflete o instante de amostragem do primeiro byte do payload
- Usado para:
  - Sincronização de reprodução
  - Cálculo de jitter
  - Sincronização áudio/vídeo (com RTCP)
- Neste projeto: timestamp Unix (segundos desde 1970)

**Unidade do Timestamp:**
- Depende do codec
- Para vídeo: geralmente clock de 90 kHz
- Para áudio: taxa de amostragem (ex: 8 kHz, 48 kHz)
- Neste projeto: segundos (simplificado)

#### Bytes 8-11: SSRC

```
Byte 8:  Bits 31-24
Byte 9:  Bits 23-16
Byte 10: Bits 15-8
Byte 11: Bits 7-0
```

**SSRC (Synchronization Source) - 32 bits:**
- Identificador único da fonte do stream
- Escolhido aleatoriamente no início da sessão
- Permite distinguir múltiplas fontes
- Neste projeto: sempre 0 (simplificado)

## Implementação Prática: RtpPacket.py

### Estrutura da Classe

```python
HEADER_SIZE = 12

class RtpPacket:
    header = bytearray(HEADER_SIZE)
    
    def __init__(self):
        pass
    
    def encode(self, version, padding, extension, cc, seqnum, 
               marker, pt, ssrc, payload):
        # Codifica pacote RTP
    
    def decode(self, byteStream):
        # Decodifica pacote RTP
    
    def version(self):
        # Retorna versão
    
    def seqNum(self):
        # Retorna número de sequência
    
    def timestamp(self):
        # Retorna timestamp
    
    def payloadType(self):
        # Retorna tipo de payload
    
    def getPayload(self):
        # Retorna payload
    
    def getPacket(self):
        # Retorna pacote completo
```

### Método encode() - Codificação no Servidor

**Código Completo com Análise:**

```python
def encode(self, version, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
    timestamp = int(time())
    header = bytearray(HEADER_SIZE)
```

**1. Obtém timestamp atual:**
```python
timestamp = int(time())
```
- `time()` retorna segundos desde 1/1/1970 (Unix epoch)
- Convertido para inteiro
- Exemplo: 1705420800 (15 de janeiro de 2024)

**2. Cria array de bytes para o cabeçalho:**
```python
header = bytearray(HEADER_SIZE)
```
- `bytearray`: array mutável de bytes
- Tamanho: 12 bytes
- Inicializado com zeros

**3. Codifica Byte 0 (V, P, X, CC):**

```python
self.header[0] = version << 6
self.header[0] = self.header[0] | padding << 5
self.header[0] = self.header[0] | extension << 4
self.header[0] = self.header[0] | cc
```

**Análise bit a bit:**

```
Passo 1: version << 6
  version = 2 (binário: 00000010)
  2 << 6 = 10000000 (desloca 6 bits à esquerda)
  header[0] = 10000000

Passo 2: padding << 5
  padding = 0 (binário: 00000000)
  0 << 5 = 00000000
  header[0] | 00000000 = 10000000

Passo 3: extension << 4
  extension = 0 (binário: 00000000)
  0 << 4 = 00000000
  header[0] | 00000000 = 10000000

Passo 4: cc
  cc = 0 (binário: 00000000)
  header[0] | 00000000 = 10000000

Resultado final: header[0] = 10000000 (0x80)
```

**Por que usar operações bit a bit?**
- Empacota múltiplos valores em um único byte
- Eficiente em termos de espaço
- Padrão em protocolos de rede

**4. Codifica Byte 1 (M, PT):**

```python
self.header[1] = marker << 7
self.header[1] = self.header[1] | pt
```

**Análise:**
```
Passo 1: marker << 7
  marker = 0 (binário: 00000000)
  0 << 7 = 00000000
  header[1] = 00000000

Passo 2: pt
  pt = 26 (binário: 00011010)
  header[1] | 00011010 = 00011010

Resultado final: header[1] = 00011010 (0x1A = 26 decimal)
```

**5. Codifica Bytes 2-3 (Sequence Number):**

```python
self.header[2] = seqnum >> 8
self.header[3] = seqnum
```

**Análise:**
```
seqnum = 1234 (binário: 00000100 11010010)

Byte alto (header[2]):
  seqnum >> 8 = 00000100 (desloca 8 bits à direita)
  header[2] = 4

Byte baixo (header[3]):
  seqnum & 0xFF = 11010010 (pega apenas os 8 bits inferiores)
  header[3] = 210

Verificação:
  (4 << 8) | 210 = (1024) | 210 = 1234 ✓
```

**Por que dividir em dois bytes?**
- Sequence number é 16 bits (2 bytes)
- Rede transmite bytes individuais
- Byte alto primeiro (big-endian)

**6. Codifica Bytes 4-7 (Timestamp):**

```python
self.header[4] = (timestamp >> 24) & 0xFF
self.header[5] = (timestamp >> 16) & 0xFF
self.header[6] = (timestamp >> 8) & 0xFF
self.header[7] = timestamp & 0xFF
```

**Análise com exemplo:**
```
timestamp = 1705420800 (0x65A4E000 em hexadecimal)
Binário: 01100101 10100100 11100000 00000000

Byte 4 (bits 31-24):
  timestamp >> 24 = 01100101
  & 0xFF = 01100101
  header[4] = 101 (0x65)

Byte 5 (bits 23-16):
  timestamp >> 16 = 01100101 10100100
  & 0xFF = 10100100
  header[5] = 164 (0xA4)

Byte 6 (bits 15-8):
  timestamp >> 8 = 01100101 10100100 11100000
  & 0xFF = 11100000
  header[6] = 224 (0xE0)

Byte 7 (bits 7-0):
  timestamp & 0xFF = 00000000
  header[7] = 0 (0x00)

Resultado: [0x65, 0xA4, 0xE0, 0x00] = 1705420800
```

**Por que usar & 0xFF?**
- Garante que apenas os 8 bits inferiores sejam usados
- Evita problemas com sinal (números negativos)
- Máscara de bits: 0xFF = 11111111

**7. Codifica Bytes 8-11 (SSRC):**

```python
self.header[8] = ssrc >> 24
self.header[9] = ssrc >> 16
self.header[10] = ssrc >> 8
self.header[11] = ssrc
```

**Análise:**
```
ssrc = 0 (simplificado neste projeto)

header[8] = 0 >> 24 = 0
header[9] = 0 >> 16 = 0
header[10] = 0 >> 8 = 0
header[11] = 0

Resultado: [0x00, 0x00, 0x00, 0x00] = 0
```

**8. Anexa Payload:**

```python
self.payload = payload
```

**Payload:**
- Dados JPEG do frame de vídeo
- Tamanho variável (tipicamente 10-50 KB por frame)
- Não modificado, apenas anexado ao cabeçalho

### Método decode() - Decodificação no Cliente

**Código:**

```python
def decode(self, byteStream):
    self.header = bytearray(byteStream[:HEADER_SIZE])
    self.payload = byteStream[HEADER_SIZE:]
```

**Análise:**

```
byteStream recebido via UDP:
  [12 bytes de cabeçalho][N bytes de payload]

Passo 1: Extrai cabeçalho
  byteStream[:HEADER_SIZE] = byteStream[0:12]
  Copia primeiros 12 bytes para self.header

Passo 2: Extrai payload
  byteStream[HEADER_SIZE:] = byteStream[12:]
  Copia do byte 12 até o final para self.payload
```

**Exemplo prático:**
```python
byteStream = b'\x80\x1a\x04\xd2...[15234 bytes de JPEG]'

self.header = bytearray(b'\x80\x1a\x04\xd2\x65\xa4\xe0\x00\x00\x00\x00\x00')
self.payload = byteStream[12:]  # 15234 bytes de JPEG
```

### Métodos de Extração

**1. version() - Extrai versão:**

```python
def version(self):
    return int(self.header[0] >> 6)
```

**Análise:**
```
header[0] = 10000000 (0x80)

Passo 1: Desloca 6 bits à direita
  10000000 >> 6 = 00000010

Passo 2: Converte para int
  int(00000010) = 2

Resultado: version = 2
```

**2. seqNum() - Extrai número de sequência:**

```python
def seqNum(self):
    seqNum = self.header[2] << 8 | self.header[3]
    return int(seqNum)
```

**Análise:**
```
header[2] = 4 (byte alto)
header[3] = 210 (byte baixo)

Passo 1: Desloca byte alto 8 bits à esquerda
  4 << 8 = 1024 (binário: 00000100 00000000)

Passo 2: OR com byte baixo
  1024 | 210 = 1234
  (00000100 00000000) | (00000000 11010010) = 00000100 11010010

Resultado: seqNum = 1234
```

**3. timestamp() - Extrai timestamp:**

```python
def timestamp(self):
    timestamp = (self.header[4] << 24 | 
                 self.header[5] << 16 | 
                 self.header[6] << 8 | 
                 self.header[7])
    return int(timestamp)
```

**Análise:**
```
header[4] = 101 (0x65)
header[5] = 164 (0xA4)
header[6] = 224 (0xE0)
header[7] = 0 (0x00)

Passo 1: Reconstrói valor de 32 bits
  (101 << 24) = 1694498816
  (164 << 16) = 10747904
  (224 << 8) = 57344
  (0) = 0

Passo 2: OR de todos os valores
  1694498816 | 10747904 | 57344 | 0 = 1705420800

Resultado: timestamp = 1705420800
```

**4. payloadType() - Extrai tipo de payload:**

```python
def payloadType(self):
    pt = self.header[1] & 127
    return int(pt)
```

**Análise:**
```
header[1] = 00011010 (26 decimal)

Passo 1: AND com 127 (0x7F = 01111111)
  00011010 & 01111111 = 00011010

Resultado: pt = 26 (MJPEG)
```

**Por que & 127?**
- 127 = 01111111 (7 bits setados)
- Remove o bit de marker (bit 7)
- Isola apenas os 7 bits do payload type

**5. getPayload() - Retorna payload:**

```python
def getPayload(self):
    return self.payload
```

**6. getPacket() - Retorna pacote completo:**

```python
def getPacket(self):
    return self.header + self.payload
```

**Análise:**
```
self.header = bytearray de 12 bytes
self.payload = bytes de N bytes

Concatenação:
  header + payload = pacote RTP completo
  [12 bytes][N bytes] = [12+N bytes]
```

## Uso Prático no Servidor

**Em ServerWorker.py:**

```python
def makeRtp(self, payload, frameNbr):
    version = 2
    padding = 0
    extension = 0
    cc = 0
    marker = 0
    pt = 26  # MJPEG
    seqnum = frameNbr
    ssrc = 0
    
    rtpPacket = RtpPacket()
    rtpPacket.encode(version, padding, extension, cc, 
                     seqnum, marker, pt, ssrc, payload)
    
    return rtpPacket.getPacket()
```

**Fluxo:**
```
1. Lê frame JPEG do arquivo (payload)
2. Obtém número do frame (seqnum)
3. Cria objeto RtpPacket
4. Chama encode() com parâmetros
5. Obtém pacote completo com getPacket()
6. Envia via UDP
```

**Exemplo concreto:**
```python
payload = b'\xff\xd8\xff\xe0...'  # 15234 bytes de JPEG
frameNbr = 42

packet = makeRtp(payload, frameNbr)

# packet agora contém:
# [12 bytes de cabeçalho RTP][15234 bytes de JPEG]
# Total: 15246 bytes

# Envia via UDP
rtpSocket.sendto(packet, (clientAddress, clientPort))
```

## Uso Prático no Cliente

**Em Client.py:**

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
```

**Fluxo:**
```
1. Recebe pacote UDP (data)
2. Cria objeto RtpPacket
3. Chama decode(data)
4. Extrai seqNum com seqNum()
5. Verifica se não é pacote atrasado
6. Extrai payload com getPayload()
7. Escreve frame em arquivo
8. Atualiza display
```

## Detecção de Perda de Pacotes

**Lógica no Cliente:**

```python
currFrameNbr = rtpPacket.seqNum()

if currFrameNbr > self.frameNbr:
    self.frameNbr = currFrameNbr
    # Processa frame
else:
    # Descarta frame atrasado
```

**Exemplo de cenário:**

```
Cliente espera frame 100
  │
  ▼
Recebe frame 100 → Processa
  │
  ▼
Recebe frame 101 → Processa
  │
  ▼
Recebe frame 103 → Processa (frame 102 perdido!)
  │
  ▼
Recebe frame 102 → Descarta (atrasado)
```

**Por que descartar frames atrasados?**
- Em streaming ao vivo, frame atrasado é inútil
- Melhor pular frame do que atrasar reprodução
- Mantém sincronização temporal

## Cálculo de Jitter (Conceito)

Embora não implementado neste projeto, o timestamp permite calcular jitter:

```
Jitter = variação no tempo de chegada dos pacotes

Exemplo:
  Pacote 1: enviado em t=0, recebido em t=100ms
  Pacote 2: enviado em t=50, recebido em t=180ms
  
  Atraso esperado: 100ms
  Atraso real pacote 2: 130ms
  Jitter: 30ms
```

**Fórmula:**
```
D(i) = (R(i) - S(i)) - (R(i-1) - S(i-1))

Onde:
  R(i) = tempo de recepção do pacote i
  S(i) = timestamp do pacote i
  D(i) = variação de atraso
```

## Limitações e Melhorias Possíveis

### Limitações Atuais

1. **Timestamp Simplificado:**
   - Usa segundos Unix (baixa resolução)
   - Deveria usar clock de 90 kHz para vídeo

2. **Sem CSRC:**
   - Não suporta múltiplas fontes contribuintes
   - Limitado a uma única fonte

3. **Sem Extensões:**
   - Não suporta cabeçalhos de extensão
   - Sem metadados adicionais

4. **Sem RTCP:**
   - Não há feedback de qualidade
   - Sem estatísticas de perda/jitter

### Melhorias Possíveis

**1. Timestamp de Alta Resolução:**
```python
# Ao invés de:
timestamp = int(time())

# Usar:
timestamp = int(time() * 90000) % (2**32)  # Clock de 90 kHz
```

**2. Suporte a Fragmentação:**
```python
# Para payloads grandes, fragmentar em múltiplos pacotes RTP
def fragmentPayload(payload, maxSize=1400):
    fragments = []
    for i in range(0, len(payload), maxSize):
        fragments.append(payload[i:i+maxSize])
    return fragments
```

**3. Detecção Avançada de Perda:**
```python
def detectLoss(self, seqNum):
    expected = (self.lastSeqNum + 1) % 65536
    if seqNum != expected:
        lost = (seqNum - expected) % 65536
        print(f"Perdidos {lost} pacotes")
    self.lastSeqNum = seqNum
```

## Resumo do Protocolo RTP

### Pontos-Chave

1. **Cabeçalho de 12 bytes** contém informações essenciais
2. **Sequence Number** permite detectar perda e reordenar
3. **Timestamp** permite sincronização temporal
4. **Payload Type** identifica o codec
5. **Operações bit a bit** empacotam dados eficientemente
6. **Separação cabeçalho/payload** facilita processamento

### Fluxo Completo

```
Servidor:
  Frame JPEG → encode() → [Header][Payload] → UDP

Cliente:
  UDP → [Header][Payload] → decode() → Frame JPEG
```

---

**Próximo:** [04-PROTOCOLO-RTSP.md](04-PROTOCOLO-RTSP.md) - Análise Profunda do Protocolo RTSP
