# Projeto RTP Video Streaming

Implementação de um servidor e cliente de streaming de vídeo usando o protocolo RTP (Real-time Transport Protocol) com recursos de QoS e segurança.

## Estrutura do Projeto

```
trab_redes/
├── server.py              # Servidor RTP que transmite vídeo
├── client.py              # Cliente RTP que recebe e exibe vídeo
├── requirements.txt       # Dependências Python
├── video.mp4             # Arquivo de vídeo (você precisa adicionar)
└── README.md             # Este arquivo
```

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Adicione um arquivo de vídeo chamado `video.mp4` na pasta do projeto.

## Como Usar

### 1. Iniciar o Cliente (primeiro)
Em um terminal:
```bash
python client.py
```

### 2. Iniciar o Servidor
Em outro terminal:
```bash
python server.py
```

Ou especifique um arquivo de vídeo diferente:
```bash
python server.py meu_video.mp4
```

### 3. Parar a Transmissão
- Pressione `Ctrl+C` no servidor ou cliente
- Ou pressione `q` na janela do vídeo

## Funcionalidades Implementadas

### 1. Protocolo RTP (RFC 3550)
- **Cabeçalho RTP de 12 bytes** com todos os campos padrão:
  - Version (2 bits): 2
  - Padding, Extension, CC (6 bits): 0
  - Marker (1 bit): 1 no último pacote do quadro
  - Payload Type (7 bits): 26 (JPEG)
  - Sequence Number (16 bits): incrementa a cada pacote
  - Timestamp (32 bits): clock de 90kHz (padrão para vídeo)
  - SSRC (32 bits): identificador aleatório do stream

### 2. Fragmentação por MTU
- Cada frame JPEG é dividido em chunks de até 1400 bytes
- Respeita o MTU da rede para evitar fragmentação IP
- Payload máximo: 1400 - 12 (header) = 1388 bytes

### 3. QoS (Quality of Service)
- **DSCP Marking**: Marca pacotes com DSCP EF (0xB8) para priorização
- **Estatísticas em tempo real**:
  - Pacotes recebidos
  - Pacotes perdidos (detectados por gaps no sequence number)
  - Taxa de perda (%)
  - Jitter (variação de atraso) em milissegundos
- **Jitter Buffer**: Buffer de 10 pacotes para compensar variações

### 4. Segurança (SRTP-like)
- **Criptografia AES-GCM** do payload RTP
- Header RTP permanece em claro (como no SRTP real)
- Nonce derivado do sequence number
- Autenticação e integridade garantidas pelo GCM
- Chave pré-compartilhada de 256 bits

## Demonstração para Apresentação

### 1. Captura com Wireshark
```
Filtro: udp.port == 5004
```

Você verá:
- Pacotes UDP com 12 bytes de header RTP visível
- Payload criptografado (não é possível ver o JPEG)
- Sequence numbers incrementando
- Timestamps com clock de 90kHz

### 2. Análise de um Pacote RTP

Exemplo de header (12 bytes em hexadecimal):
```
80 9A 00 01 00 00 0B B8 12 34 56 78
│  │  │     │           │
│  │  │     │           └─ SSRC (4 bytes)
│  │  │     └─ Timestamp (4 bytes)
│  │  └─ Sequence Number (2 bytes)
│  └─ Marker + Payload Type
└─ Version + flags
```

### 3. Estatísticas Exibidas

O cliente mostra na tela:
- Frame atual
- Sequence number
- Timestamp
- SSRC
- Pacotes perdidos
- Jitter em ms

E imprime estatísticas a cada 30 frames:
```
--- Statistics ---
Packets received: 450
Packets lost: 2
Loss rate: 0.44%
Jitter: 1.23 ms
------------------
```

## Conceitos Técnicos

### RTP (Real-time Transport Protocol)
- Protocolo da camada de aplicação (sobre UDP)
- Não garante entrega, mas adiciona informações para sincronização
- Sequence numbers permitem detectar perda e reordenação
- Timestamps permitem sincronização de áudio/vídeo

### QoS (Quality of Service)
- **DSCP (Differentiated Services Code Point)**: Campo no header IP que indica prioridade
- **EF (Expedited Forwarding)**: Classe de serviço de baixa latência para tráfego em tempo real
- **Jitter**: Variação estatística do atraso entre pacotes
- **Jitter Buffer**: Compensa variações de rede antes de exibir

### Segurança (SRTP)
- **AES-GCM**: Modo de operação que combina criptografia e autenticação
- **Nonce**: Número usado uma vez, derivado do sequence number
- **AAD (Additional Authenticated Data)**: Header RTP é autenticado mas não criptografado
- Protege contra espionagem e modificação de dados

## Parâmetros Configuráveis

### server.py
- `MTU_SIZE = 1400`: Tamanho máximo do pacote
- `CLOCK_RATE = 90000`: Clock RTP (90kHz é padrão para vídeo)
- `DSCP_EF = 0xB8`: Valor DSCP para marcação QoS
- `JPEG_QUALITY = 80`: Qualidade da compressão JPEG

### client.py
- `JITTER_BUFFER_SIZE = 10`: Tamanho do buffer de jitter
- `socket.settimeout(5.0)`: Timeout para recepção de pacotes

## Troubleshooting

### Erro: "Could not open video file"
- Certifique-se de que o arquivo `video.mp4` existe
- Ou especifique o caminho correto: `python server.py caminho/para/video.mp4`

### Erro: "Address already in use"
- A porta 5004 já está em uso
- Feche outros programas ou mude a porta no código

### Vídeo não aparece no cliente
- Inicie o cliente ANTES do servidor
- Verifique se não há firewall bloqueando a porta 5004
- Teste com `127.0.0.1` (localhost) primeiro

### Muitos pacotes perdidos
- Rede congestionada
- Tente reduzir a qualidade JPEG no servidor
- Ou reduza o FPS do vídeo

## Referências

- [RFC 3550 - RTP: A Transport Protocol for Real-Time Applications](https://www.rfc-editor.org/rfc/rfc3550)
- [RFC 3711 - The Secure Real-time Transport Protocol (SRTP)](https://www.rfc-editor.org/rfc/rfc3711)
- [RFC 2474 - Definition of the Differentiated Services Field (DS Field)](https://www.rfc-editor.org/rfc/rfc2474)

## Autores

Projeto desenvolvido para a disciplina de Redes de Computadores.
