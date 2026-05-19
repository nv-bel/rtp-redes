# Sistema de Streaming de Vídeo com RTP/RTSP e QoS

## Descrição do Projeto

Este projeto implementa um sistema completo de streaming de vídeo utilizando os protocolos **RTP (Real-time Transport Protocol)** e **RTSP (Real Time Streaming Protocol)**, com suporte a **Quality of Service (QoS)** através de marcação DSCP.

Desenvolvido como trabalho prático da disciplina de Redes de Computadores, o sistema demonstra na prática os conceitos de:
- Transmissão de mídia em tempo real
- Protocolos de controle de sessão (RTSP)
- Protocolos de transporte de mídia (RTP)
- Qualidade de serviço em redes IP
- Arquitetura cliente-servidor para streaming

## Características Principais

### Protocolos Implementados

**RTP (Real-time Transport Protocol)**
- Encapsulamento de frames de vídeo MJPEG
- Cabeçalho RTP completo (12 bytes) com campos:
  - Version, Padding, Extension, CSRC Count
  - Marker, Payload Type
  - Sequence Number (controle de ordem)
  - Timestamp (sincronização)
  - SSRC (identificação da fonte)
- Transmissão via UDP para baixa latência

**RTSP (Real Time Streaming Protocol)**
- Controle de sessão sobre TCP
- Comandos implementados:
  - `SETUP`: Inicializa sessão e configura transporte
  - `PLAY`: Inicia reprodução do vídeo
  - `PAUSE`: Pausa a reprodução
  - `TEARDOWN`: Encerra a sessão
- Sistema de numeração de sequência (CSeq)
- Gerenciamento de IDs de sessão

### Quality of Service (QoS)

- Marcação DSCP (Differentiated Services Code Point)
- Priorização de tráfego RTP com valor `0xB8` (EF - Expedited Forwarding)
- Configuração via socket option `IP_TOS`
- Garantia de baixa latência para streaming de vídeo

### Interface Gráfica

- Cliente com interface Tkinter
- Controles de reprodução (Setup, Play, Pause, Teardown)
- Visualização em tempo real dos frames
- Sistema de cache para exibição

## Arquitetura do Sistema

```
┌─────────────────┐                    ┌─────────────────┐
│     Cliente     │                    │    Servidor     │
│                 │                    │                 │
│  ┌───────────┐  │   RTSP (TCP)       │  ┌───────────┐  │
│  │   Client  │◄─┼────────────────────┼─►│   Server  │  │
│  │           │  │   Controle de      │  │           │  │
│  │           │  │   Sessão           │  │  Worker   │  │
│  └─────┬─────┘  │                    │  └─────┬─────┘  │
│        │        │                    │        │        │
│  ┌─────▼─────┐  │   RTP (UDP)        │  ┌─────▼─────┐  │
│  │ RtpPacket │◄─┼────────────────────┼──│ RtpPacket │  │
│  │  Decoder  │  │   Streaming de     │  │  Encoder  │  │
│  └───────────┘  │   Vídeo + QoS      │  └───────────┘  │
│                 │                    │        │        │
│  ┌───────────┐  │                    │  ┌─────▼─────┐  │
│  │    GUI    │  │                    │  │VideoStream│  │
│  │ (Tkinter) │  │                    │  │  Reader   │  │
│  └───────────┘  │                    │  └───────────┘  │
└─────────────────┘                    └─────────────────┘
```

## Estrutura de Arquivos

```
rtp-redes/Versão_com_QoS/
├── Server.py              # Servidor RTSP principal
├── ServerWorker.py        # Worker que processa requisições de cada cliente
├── Client.py              # Cliente com interface gráfica
├── ClientLauncher.py      # Launcher do cliente com configurações
├── RtpPacket.py           # Classe para codificação/decodificação RTP
├── VideoStream.py         # Leitor de arquivo de vídeo MJPEG
└── movie.Mjpeg            # Arquivo de vídeo de exemplo
```

## Componentes do Sistema

### 1. Server.py
Servidor principal que:
- Escuta conexões RTSP na porta 554
- Aceita múltiplos clientes
- Delega processamento para ServerWorker

### 2. ServerWorker.py
Worker que gerencia cada cliente:
- Processa comandos RTSP (SETUP, PLAY, PAUSE, TEARDOWN)
- Gerencia máquina de estados (INIT, READY, PLAYING)
- Envia pacotes RTP com QoS habilitado
- Encapsula frames em pacotes RTP

### 3. Client.py
Cliente com interface gráfica:
- Interface Tkinter com controles de reprodução
- Envia comandos RTSP ao servidor
- Recebe e decodifica pacotes RTP
- Exibe frames em tempo real
- Descarta pacotes atrasados

### 4. RtpPacket.py
Implementação do protocolo RTP:
- Método `encode()`: Cria pacote RTP com cabeçalho de 12 bytes
- Método `decode()`: Extrai cabeçalho e payload
- Métodos de acesso: version(), seqNum(), timestamp(), payloadType()

### 5. VideoStream.py
Leitor de arquivo MJPEG:
- Lê frames sequencialmente
- Formato: 5 bytes (tamanho) + frame JPEG
- Controla numeração de frames

## Fluxo de Comunicação

### 1. Estabelecimento de Sessão (SETUP)
```
Cliente                                 Servidor
   │                                       │
   │  SETUP movie.Mjpeg RTSP/1.0           │
   │  CSeq: 1                              │
   │  Transport: RTP/UDP; port=5004        │
   ├──────────────────────────────────────►│
   │                                       │
   │  RTSP/1.0 200 OK                      │
   │  CSeq: 1                              │
   │  Session: 123456                      │
   │◄──────────────────────────────────────┤
   │                                       │
```

### 2. Reprodução (PLAY)
```
Cliente                                 Servidor
   │                                       │
   │  PLAY RTSP/1.0                        │
   │  CSeq: 2                              │
   ├──────────────────────────────────────►│
   │                                       │
   │  RTSP/1.0 200 OK                      │
   │  CSeq: 2                              │
   │◄──────────────────────────────────────┤
   │                                       │
   │  RTP Packets (UDP, DSCP=0xB8)         │
   │◄══════════════════════════════════════┤
   │  Frame 1, Frame 2, Frame 3...         │
   │◄══════════════════════════════════════┤
```

### 3. Pausa (PAUSE)
```
Cliente                                 Servidor
   │                                       │
   │  PAUSE RTSP/1.0                       │
   │  CSeq: 3                              │
   ├──────────────────────────────────────►│
   │                                       │ (Para envio RTP)
   │  RTSP/1.0 200 OK                      │
   │  CSeq: 3                              │
   │◄──────────────────────────────────────┤
```

### 4. Encerramento (TEARDOWN)
```
Cliente                                 Servidor
   │                                       │
   │  TEARDOWN RTSP/1.0                    │
   │  CSeq: 4                              │
   ├──────────────────────────────────────►│
   │                                       │ (Fecha socket RTP)
   │  RTSP/1.0 200 OK                      │
   │  CSeq: 4                              │
   │◄──────────────────────────────────────┤
   │                                       │
   │  (Fecha conexões)                     │ (Libera recursos)
```

## Requisitos

- Python 3.x
- Bibliotecas:
  - `tkinter` (interface gráfica)
  - `PIL` / `Pillow` (processamento de imagens)
  - `socket` (comunicação de rede)
  - `threading` (concorrência)

## Como Executar

### 1. Iniciar o Servidor
```bash
python Server.py 554
```

### 2. Iniciar o Cliente
```bash
python ClientLauncher.py
```

### 3. Usar a Interface
1. Clique em **Setup** para estabelecer conexão
2. Clique em **Play** para iniciar reprodução
3. Clique em **Pause** para pausar
4. Clique em **Teardown** para encerrar

## Detalhes Técnicos de Implementação

### Cabeçalho RTP (12 bytes)

```
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|V=2|P|X|  CC   |M|     PT      |       Sequence Number         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                           Timestamp                           |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                             SSRC                              |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Campos implementados:**
- **V (Version)**: 2 bits = 2 (RTP versão 2)
- **P (Padding)**: 1 bit = 0 (sem padding)
- **X (Extension)**: 1 bit = 0 (sem extensão)
- **CC (CSRC Count)**: 4 bits = 0 (sem fontes contribuintes)
- **M (Marker)**: 1 bit = 0
- **PT (Payload Type)**: 7 bits = 26 (MJPEG)
- **Sequence Number**: 16 bits (número do frame)
- **Timestamp**: 32 bits (tempo Unix)
- **SSRC**: 32 bits = 0 (identificador da fonte)

### QoS via DSCP

```python
# ServerWorker.py linha 83
self.clientInfo["rtpSocket"].setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)
```

**Valor 0xB8 (10111000 em binário):**
- DSCP = 101110 (46 decimal) = EF (Expedited Forwarding)
- ECN = 00
- Classe de serviço: Tráfego de baixa latência (voz/vídeo)

### Controle de Fluxo

**No Cliente:**
- Descarte de pacotes atrasados (linha 105 Client.py)
- Timeout de socket RTP: 0.5 segundos
- Thread separada para recepção RTP

**No Servidor:**
- Intervalo entre frames: 50ms (20 FPS)
- Thread dedicada por cliente
- Event para controle de pausa/teardown

## Documentação Adicional

Para uma compreensão mais profunda do projeto, consulte os guias de apresentação:

1. **[01-INTRODUCAO.md](01-INTRODUCAO.md)** - Conceitos fundamentais de RTP/RTSP
2. **[02-ARQUITETURA.md](02-ARQUITETURA.md)** - Arquitetura detalhada do sistema
3. **[03-PROTOCOLO-RTP.md](03-PROTOCOLO-RTP.md)** - Análise profunda do RTP
4. **[04-PROTOCOLO-RTSP.md](04-PROTOCOLO-RTSP.md)** - Análise profunda do RTSP
5. **[05-QOS.md](05-QOS.md)** - Quality of Service implementado
6. **[06-FLUXO-EXECUCAO.md](06-FLUXO-EXECUCAO.md)** - Fluxo de execução detalhado
7. **[07-COMO-EXECUTAR.md](07-COMO-EXECUTAR.md)** - Guia de execução e testes

## Conceitos de Redes Demonstrados

### 1. Camada de Transporte
- **TCP**: Usado para RTSP (confiabilidade no controle)
- **UDP**: Usado para RTP (baixa latência para mídia)

### 2. Protocolos de Aplicação
- **RTSP**: Protocolo de controle de sessão
- **RTP**: Protocolo de transporte de mídia em tempo real

### 3. Quality of Service
- **DSCP**: Marcação de pacotes para priorização
- **Traffic Class**: EF (Expedited Forwarding)

### 4. Programação de Sockets
- Sockets TCP para controle
- Sockets UDP para dados
- Configuração de opções de socket (TOS)

### 5. Concorrência
- Threads para recepção/envio simultâneos
- Sincronização com Events
- Múltiplos clientes simultâneos

## Possíveis Melhorias

1. **Controle de Congestionamento**: Implementar RTCP para feedback
2. **Buffering Adaptativo**: Ajustar buffer baseado em jitter
3. **Codec Moderno**: Suporte a H.264/H.265
4. **Criptografia**: TLS para RTSP, SRTP para RTP
5. **Métricas**: Taxa de perda, jitter, latência
6. **Multicast**: Suporte a streaming para múltiplos clientes

## Autores

Trabalho desenvolvido para a disciplina de Redes de Computadores - UNEB

## Licença

Projeto educacional - Livre para uso acadêmico

## Referências

- RFC 3550 - RTP: A Transport Protocol for Real-Time Applications
- RFC 2326 - Real Time Streaming Protocol (RTSP)
- RFC 2474 - Definition of the Differentiated Services Field (DS Field)
- RFC 3246 - An Expedited Forwarding PHB (Per-Hop Behavior)
