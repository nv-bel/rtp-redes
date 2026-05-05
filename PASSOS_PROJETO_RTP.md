# Passos para Criar Projeto de Servidor RTP de Vídeo

## 1. Definir Escopo e Linguagem

Use **Python** — é a opção mais simples para apresentar e explicar.

### Bibliotecas necessárias:
- `socket` (UDP nativo)
- `opencv-python` (ler quadros do vídeo)
- `struct` (montar cabeçalho RTP)
- `cryptography` (parte de segurança)

### Estrutura mínima de pastas:
```
trab_redes/
├── server.py
├── client.py
├── video.mp4
└── requirements.txt
```

## 2. Entender o Cabeçalho RTP (12 bytes fixos)

Você precisa montar manualmente para mostrar que entende o protocolo:

| Campo | Bits | O que colocar |
|---|---|---|
| Version | 2 | 2 |
| Padding, Extension, CC | 6 | 0 |
| Marker | 1 | 1 no último pacote do quadro |
| Payload Type | 7 | 26 (JPEG) |
| Sequence Number | 16 | incrementa a cada pacote |
| Timestamp | 32 | tempo do quadro (clock 90kHz é o padrão de vídeo) |
| SSRC | 32 | identificador aleatório do streamer |

Isso é montado com `struct.pack('!BBHII', ...)`.

## 3. Servidor (`server.py`) — Fluxo

1. Abrir vídeo com `cv2.VideoCapture("video.mp4")`
2. Criar socket UDP: `socket.socket(AF_INET, SOCK_DGRAM)`
3. Loop por quadro:
   - Ler frame → comprimir em JPEG (`cv2.imencode('.jpg', frame)`)
   - Quebrar em chunks (~1400 bytes para caber na MTU)
   - Para cada chunk: montar header RTP (incrementa seq, marker=1 só no último) + payload
   - `sock.sendto(pacote, (ip, porta))`
   - Incrementar timestamp (ex.: +3000 a 30 fps com clock 90kHz)
   - `time.sleep(1/fps)` para respeitar a taxa

## 4. Cliente (`client.py`) — Fluxo

1. `bind` em uma porta UDP
2. Receber pacotes, ler header RTP (`struct.unpack`)
3. Juntar chunks até receber `marker=1`
4. Decodificar JPEG e exibir com `cv2.imshow`
5. Imprimir seq/timestamp na tela — bom para a apresentação

## 5. QoS (Quality of Service)

Formas simples e explicáveis:

### DSCP/ToS no socket
Marcar prioridade na camada IP:
```python
sock.setsockopt(IPPROTO_IP, IP_TOS, 0xB8)  # DSCP EF (Expedited Forwarding)
```

### Buffer de jitter no cliente
Fila ordenada por sequence number antes de exibir.

### Estatísticas
Contar pacotes perdidos (gaps na seq) e calcular jitter — mostrar na tela.

## 6. Segurança

Mais simples de explicar: **criptografar o payload RTP** (mantendo o header em claro, como faz o SRTP de verdade):

### Implementação com AES-GCM
```python
AESGCM(key).encrypt(nonce, payload, aad=header_rtp)
```

### Detalhes:
- O nonce pode ser derivado do `sequence number` (igual ao SRTP real)
- Chave pré-compartilhada entre server e client (constante no código, para simplificar)
- Fala sobre autenticação (GCM já dá integridade) na apresentação

## 7. Roteiro da Apresentação

1. Mostra o vídeo tocando no cliente
2. Abre Wireshark filtrando `udp.port == 5004` → mostra os pacotes RTP reais
3. Explica um pacote: header de 12 bytes + payload cifrado
4. Mostra estatísticas de QoS (perda, jitter) no terminal
5. Mostra o que acontece se desligar a criptografia (Wireshark vê o JPEG)

## 8. Ordem de Implementação Sugerida

1. Servidor envia UDP simples com JPEG (sem RTP)
2. Adiciona header RTP manual
3. Adiciona fragmentação por MTU
4. Implementa cliente que reagrupa e exibe
5. Adiciona DSCP + estatísticas (QoS)
6. Adiciona AES-GCM (Segurança)

## Conceitos Importantes para Explicar

### RTP (Real-time Transport Protocol)
- Protocolo da camada de aplicação para transmissão de dados em tempo real
- Roda sobre UDP (não garante entrega, mas é mais rápido)
- Adiciona sequence numbers e timestamps para sincronização

### QoS (Quality of Service)
- Mecanismos para priorizar tráfego de vídeo na rede
- DSCP marca pacotes para roteadores priorizarem
- Jitter buffer compensa variações de atraso

### Segurança (SRTP)
- Criptografia do payload mantém privacidade
- Autenticação garante integridade dos dados
- AES-GCM combina ambos de forma eficiente

## Recursos Adicionais

- RFC 3550 (RTP): https://www.rfc-editor.org/rfc/rfc3550
- RFC 3711 (SRTP): https://www.rfc-editor.org/rfc/rfc3711
- RFC 2474 (DSCP): https://www.rfc-editor.org/rfc/rfc2474
