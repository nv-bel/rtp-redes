# 01 - Introdução: Streaming de Vídeo e Protocolos RTP/RTSP

## Objetivo da Apresentação

Este documento introduz os conceitos fundamentais de streaming de vídeo em redes IP, com foco nos protocolos RTP (Real-time Transport Protocol) e RTSP (Real Time Streaming Protocol), que são a base do nosso projeto prático.

## O que é Streaming de Vídeo?

### Definição

Streaming é a transmissão contínua de dados multimídia (áudio/vídeo) através de uma rede, permitindo que o conteúdo seja reproduzido enquanto ainda está sendo recebido, sem necessidade de download completo.

### Diferença: Download vs Streaming

**Download Tradicional:**
```
[Servidor] ──────────► [Cliente]
           100% do arquivo
                ↓
           Reprodução após download completo
```

**Streaming:**
```
[Servidor] ═══════════► [Cliente]
           Fluxo contínuo
                ↓
           Reprodução simultânea ao recebimento
```

### Desafios do Streaming em Tempo Real

1. **Latência**: Atraso entre captura e reprodução
2. **Jitter**: Variação no tempo de chegada dos pacotes
3. **Perda de Pacotes**: Pacotes perdidos na rede
4. **Largura de Banda**: Necessidade de taxa constante
5. **Sincronização**: Áudio e vídeo sincronizados

## Por que UDP para Streaming?

### Comparação TCP vs UDP

| Característica | TCP | UDP |
|----------------|-----|-----|
| Confiabilidade | Garantida (retransmissão) | Não garantida |
| Ordenação | Pacotes ordenados | Sem garantia de ordem |
| Controle de Fluxo | Sim | Não |
| Overhead | Alto | Baixo |
| Latência | Variável (retransmissões) | Baixa e previsível |
| Uso em Streaming | Controle (RTSP) | Dados (RTP) |

### Por que UDP é Melhor para Mídia em Tempo Real?

**Problema com TCP:**
```
Pacote perdido → Retransmissão → Atraso → Buffer cresce → Latência aumenta
```

**Solução com UDP:**
```
Pacote perdido → Descartado → Próximo pacote → Latência constante
```

**Justificativa:**
- Em vídeo ao vivo, um frame atrasado é inútil
- Melhor perder um frame do que atrasar todos os seguintes
- Pequenas perdas são imperceptíveis ao olho humano
- Latência constante é mais importante que perfeição

## Introdução ao RTP (Real-time Transport Protocol)

### O que é RTP?

RTP é um protocolo de camada de aplicação projetado para entregar dados de áudio e vídeo em tempo real sobre redes IP.

**Características:**
- Definido na RFC 3550
- Roda sobre UDP
- Fornece informações de temporização e sequenciamento
- Não garante entrega ou QoS (isso é feito por camadas inferiores)

### Estrutura Básica do RTP

```
┌─────────────────────────────────────┐
│      Cabeçalho RTP (12+ bytes)      │
├─────────────────────────────────────┤
│         Payload (Dados de           │
│         Áudio/Vídeo)                │
└─────────────────────────────────────┘
```

### Principais Campos do RTP

1. **Sequence Number**: Detecta perda e reordena pacotes
2. **Timestamp**: Sincronização e cálculo de jitter
3. **Payload Type**: Identifica o codec (MJPEG, H.264, etc.)
4. **SSRC**: Identifica a fonte do stream

### Exemplo Prático

```
Frame de vídeo (50 KB) → Fragmentado em pacotes RTP
                         ↓
Pacote 1: [RTP Header][Fragmento 1]
Pacote 2: [RTP Header][Fragmento 2]
Pacote 3: [RTP Header][Fragmento 3]
                         ↓
                    Enviado via UDP
```

## Introdução ao RTSP (Real Time Streaming Protocol)

### O que é RTSP?

RTSP é um protocolo de controle de rede para sistemas de streaming de mídia. Funciona como um "controle remoto" para servidores de mídia.

**Características:**
- Definido na RFC 2326
- Roda sobre TCP (confiabilidade no controle)
- Similar ao HTTP em sintaxe
- Controla sessões de streaming

### Analogia: RTSP é como um Controle Remoto

```
┌─────────────────────┐
│  Controle Remoto    │
│                     │
│   [▶ Play]          │ ← PLAY
│   [⏸ Pause]         │ ← PAUSE
│   [⏹ Stop]          │ ← TEARDOWN
│   [⚙ Setup]         │ ← SETUP
└─────────────────────┘
```

### Comandos RTSP Principais

1. **SETUP**: Inicializa sessão e negocia transporte
2. **PLAY**: Inicia ou retoma reprodução
3. **PAUSE**: Pausa reprodução temporariamente
4. **TEARDOWN**: Encerra sessão e libera recursos

### Separação de Responsabilidades

```
RTSP (TCP)                    RTP (UDP)
    │                             │
    │ Controle                    │ Dados
    │ - SETUP                     │ - Frame 1
    │ - PLAY                      │ - Frame 2
    │ - PAUSE                     │ - Frame 3
    │ - TEARDOWN                  │ - Frame 4
    │                             │
    ▼                             ▼
[Confiável, baixo volume]   [Rápido, alto volume]
```

## Arquitetura Típica de Streaming

### Modelo Cliente-Servidor

```
┌──────────────────────────────────────────────────────────┐
│                        CLIENTE                           │
│                                                          │
│  ┌────────────────┐              ┌──────────────────┐   │
│  │ Controle RTSP  │◄────TCP─────►│  Servidor RTSP   │   │
│  │  (Comandos)    │              │   (Controle)     │   │
│  └────────────────┘              └──────────────────┘   │
│         │                                  │            │
│         │                                  │            │
│  ┌──────▼──────────┐            ┌─────────▼─────────┐  │
│  │ Receptor RTP    │◄────UDP────│  Transmissor RTP  │  │
│  │ (Decodifica)    │            │   (Codifica)      │  │
│  └─────────────────┘            └───────────────────┘  │
│         │                                               │
│         ▼                                               │
│  ┌─────────────────┐                                   │
│  │  Player/GUI     │                                   │
│  │  (Exibição)     │                                   │
│  └─────────────────┘                                   │
└──────────────────────────────────────────────────────────┘
```

## Fluxo de Comunicação Simplificado

### Sequência de Eventos

```
1. Cliente conecta ao servidor (TCP)
   │
   ▼
2. Cliente envia SETUP
   │
   ▼
3. Servidor responde OK + Session ID
   │
   ▼
4. Cliente envia PLAY
   │
   ▼
5. Servidor inicia envio de pacotes RTP (UDP)
   │
   ▼
6. Cliente recebe e exibe frames
   │
   ▼
7. Cliente envia PAUSE (opcional)
   │
   ▼
8. Servidor para envio RTP
   │
   ▼
9. Cliente envia TEARDOWN
   │
   ▼
10. Servidor encerra sessão
```

### Exemplo de Mensagens

**SETUP Request:**
```
SETUP movie.Mjpeg RTSP/1.0
CSeq: 1
Transport: RTP/UDP; client_port=5004
```

**SETUP Response:**
```
RTSP/1.0 200 OK
CSeq: 1
Session: 123456
```

**PLAY Request:**
```
PLAY RTSP/1.0
CSeq: 2
Session: 123456
```

**PLAY Response:**
```
RTSP/1.0 200 OK
CSeq: 2
Session: 123456
```

## Codecs de Vídeo

### O que é um Codec?

**Codec** = **Co**dificador + **Dec**odificador

Algoritmo que comprime (codifica) e descomprime (decodifica) dados de vídeo.

### MJPEG (Motion JPEG)

**Usado neste projeto**

- Cada frame é uma imagem JPEG independente
- Simples de implementar
- Não usa compressão temporal (entre frames)
- Taxa de compressão menor que codecs modernos
- Ideal para fins educacionais

**Estrutura:**
```
Frame 1: [JPEG completo]
Frame 2: [JPEG completo]
Frame 3: [JPEG completo]
...
```

### Outros Codecs Comuns

| Codec | Tipo | Uso Típico |
|-------|------|------------|
| H.264/AVC | Temporal | YouTube, Netflix, Streaming geral |
| H.265/HEVC | Temporal | 4K, streaming de alta qualidade |
| VP9 | Temporal | YouTube, WebRTC |
| AV1 | Temporal | Streaming moderno, royalty-free |

## Quality of Service (QoS)

### Por que QoS é Importante?

Em uma rede compartilhada, diferentes tipos de tráfego competem por recursos:

```
Rede sem QoS:
[Email] [Download] [Streaming] [Navegação]
   ↓        ↓          ↓            ↓
   ═════════════════════════════════
        Todos com mesma prioridade
              ↓
   Streaming sofre com latência variável
```

```
Rede com QoS:
[Streaming] ← Alta prioridade
[Navegação] ← Média prioridade
[Download]  ← Baixa prioridade
[Email]     ← Baixa prioridade
   ↓
   Streaming tem latência garantida
```

### DSCP (Differentiated Services Code Point)

Mecanismo para marcar pacotes IP com classe de serviço.

**Campo TOS (Type of Service) no cabeçalho IP:**
```
 0   1   2   3   4   5   6   7
+---+---+---+---+---+---+---+---+
|     DSCP      |  ECN  |
+---+---+---+---+---+---+---+---+
```

**Classes de Serviço:**
- **EF (Expedited Forwarding)**: Baixa latência (voz/vídeo)
- **AF (Assured Forwarding)**: Garantias médias
- **BE (Best Effort)**: Sem garantias (padrão)

## Conceitos de Rede Relevantes

### Portas e Sockets

**Porta**: Número que identifica um serviço/aplicação
- RTSP padrão: 554
- RTP: Dinâmica (negociada via RTSP)

**Socket**: Endpoint de comunicação (IP + Porta)
```python
socket.socket(socket.AF_INET, socket.SOCK_STREAM)  # TCP
socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # UDP
```

### Máquina de Estados

Controle de sessão através de estados:

```
     INIT
       │
       │ SETUP
       ▼
     READY ◄──────┐
       │          │
       │ PLAY     │ PAUSE
       ▼          │
    PLAYING ──────┘
       │
       │ TEARDOWN
       ▼
     INIT
```

### Threading e Concorrência

**Por que usar threads?**

```
Thread Principal (GUI)
    │
    ├─► Thread RTSP (Recebe respostas)
    │
    └─► Thread RTP (Recebe pacotes de vídeo)
```

Permite operações simultâneas:
- Interface responsiva
- Recepção contínua de dados
- Processamento paralelo

## Aplicações Reais

### Onde RTP/RTSP são Usados?

1. **Videoconferência**
   - Zoom, Teams, Google Meet
   - WebRTC (variante do RTP)

2. **Câmeras IP**
   - Sistemas de vigilância
   - Câmeras de segurança

3. **IPTV**
   - Televisão sobre IP
   - Streaming de canais ao vivo

4. **VoIP**
   - Telefonia IP
   - Skype, WhatsApp calls

5. **Streaming de Eventos**
   - Transmissões ao vivo
   - Webinars

## Evolução e Alternativas Modernas

### RTSP vs Alternativas

| Protocolo | Transporte | Latência | Uso Principal |
|-----------|------------|----------|---------------|
| RTSP/RTP | UDP/TCP | Muito baixa | Câmeras IP, IPTV |
| HLS | HTTP/TCP | Alta (6-30s) | VOD, streaming móvel |
| DASH | HTTP/TCP | Alta (6-30s) | VOD, adaptive streaming |
| WebRTC | UDP | Muito baixa | Videoconferência P2P |
| SRT | UDP | Baixa | Streaming profissional |

### Por que ainda estudar RTSP/RTP?

1. **Fundamentos**: Base para entender streaming moderno
2. **Ainda em uso**: Câmeras IP, sistemas legados
3. **Conceitos aplicáveis**: Princípios usados em protocolos modernos
4. **Controle fino**: Mais controle que protocolos HTTP-based

## Resumo dos Conceitos

### Pontos-Chave

1. **Streaming** permite reprodução durante recebimento
2. **UDP** é preferido para mídia em tempo real (baixa latência)
3. **RTP** transporta dados de mídia com informações de temporização
4. **RTSP** controla sessões de streaming (como controle remoto)
5. **QoS** garante qualidade através de priorização de tráfego
6. **Separação de controle e dados** (TCP para controle, UDP para mídia)

### Preparação para Próximas Seções

Agora que entendemos os conceitos fundamentais, nas próximas seções vamos:

1. **Arquitetura**: Como nosso sistema está estruturado
2. **RTP Detalhado**: Implementação prática do protocolo
3. **RTSP Detalhado**: Máquina de estados e comandos
4. **QoS**: Implementação de priorização
5. **Fluxo de Execução**: Passo a passo do sistema
6. **Demonstração**: Execução prática

## Perguntas para Reflexão

1. Por que não usar apenas TCP para tudo?
2. O que acontece se um pacote RTP for perdido?
3. Como o cliente sabe a ordem correta dos frames?
4. Por que separar controle (RTSP) de dados (RTP)?
5. Como QoS ajuda em redes congestionadas?

---

**Próximo:** [02-ARQUITETURA.md](02-ARQUITETURA.md) - Arquitetura Detalhada do Sistema
