# Guia de Apresentação - Projeto RTP

## Preparação Antes da Apresentação

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Criar Vídeo de Teste (se necessário)
```bash
python create_test_video.py 10
```
Isso cria um vídeo de 10 segundos chamado `video.mp4`.

### 3. Instalar Wireshark
- Download: https://www.wireshark.org/download.html
- Configurar filtro: `udp.port == 5004`

## Roteiro da Apresentação (15-20 minutos)

### Parte 1: Introdução (2 min)

**O que vamos mostrar:**
- Sistema de streaming de vídeo usando RTP
- Implementação completa de servidor e cliente
- Recursos de QoS e Segurança

**Tecnologias:**
- Python 3
- Protocolo RTP (RFC 3550)
- UDP para transporte
- AES-GCM para criptografia

### Parte 2: Conceitos Teóricos (3 min)

#### RTP (Real-time Transport Protocol)
- Protocolo da camada de aplicação
- Roda sobre UDP (não garante entrega)
- Adiciona informações para sincronização:
  - **Sequence Number**: detecta perda e reordenação
  - **Timestamp**: sincronização temporal (clock 90kHz)
  - **SSRC**: identifica a fonte do stream

#### Estrutura do Cabeçalho RTP (12 bytes)
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

- **V (Version)**: 2
- **M (Marker)**: 1 no último pacote do frame
- **PT (Payload Type)**: 26 (JPEG)
- **Sequence Number**: incrementa a cada pacote
- **Timestamp**: clock de 90kHz
- **SSRC**: identificador do stream

### Parte 3: Demonstração Prática (8 min)

#### Passo 1: Iniciar Wireshark
1. Abrir Wireshark
2. Selecionar interface de rede (Loopback para teste local)
3. Aplicar filtro: `udp.port == 5004`
4. Iniciar captura

#### Passo 2: Iniciar Cliente
```bash
python client.py
```

**Mostrar na tela:**
- Cliente aguardando pacotes
- Porta 5004 aberta

#### Passo 3: Iniciar Servidor
```bash
python server.py
```

**Mostrar na tela:**
- Informações do vídeo (FPS, total de frames)
- SSRC gerado
- QoS configurado (DSCP EF)
- Frames sendo enviados

#### Passo 4: Observar o Vídeo
**No cliente, apontar para:**
- Vídeo sendo exibido em tempo real
- Informações sobrepostas:
  - Frame atual
  - Sequence number
  - Timestamp
  - SSRC
  - Pacotes perdidos
  - Jitter

#### Passo 5: Analisar Wireshark
**Selecionar um pacote e mostrar:**

1. **Camada UDP:**
   - Porta origem/destino: 5004
   - Tamanho do pacote

2. **Cabeçalho RTP (12 bytes):**
   - Expandir detalhes do RTP
   - Mostrar cada campo:
     - Version: 2
     - Marker: 0 ou 1
     - Payload Type: 26
     - Sequence Number: incrementando
     - Timestamp: valores crescentes
     - SSRC: constante

3. **Payload Criptografado:**
   - Dados após os 12 bytes
   - Aparência aleatória (criptografado)
   - Não é possível ver o JPEG

#### Passo 6: Demonstrar Análise de Pacote
```bash
python analyze_rtp.py
```

Copiar bytes de um pacote do Wireshark e colar no analisador.

**Exemplo de saída:**
```
RTP PACKET ANALYSIS
============================================================
Header (12 bytes):
  Raw: 80 9a 00 01 00 00 0b b8 12 34 56 78

Version (V): 2
Padding (P): 0
Extension (X): 0
CSRC Count (CC): 0
Marker (M): 1 (Last packet of frame)
Payload Type (PT): 26 (JPEG)
Sequence Number: 1
Timestamp: 3000 (0x00000BB8)
  -> Time: 0.033s (at 90kHz clock)
SSRC: 305419896 (0x12345678)

Payload: 1388 bytes (encrypted)
```

### Parte 4: QoS (Quality of Service) (3 min)

#### Conceitos Implementados:

**1. DSCP (Differentiated Services Code Point)**
- Marca pacotes no campo ToS do IP
- Valor usado: 0xB8 (EF - Expedited Forwarding)
- Roteadores podem priorizar esses pacotes

**Código:**
```python
sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)
```

**2. Detecção de Perda de Pacotes**
- Analisa gaps no sequence number
- Calcula taxa de perda

**3. Medição de Jitter**
- Variação estatística do atraso
- Fórmula: `J(i) = J(i-1) + (|D(i-1,i)| - J(i-1))/16`
- Exibido em milissegundos

**Mostrar estatísticas no terminal:**
```
--- Statistics ---
Packets received: 450
Packets lost: 2
Loss rate: 0.44%
Jitter: 1.23 ms
------------------
```

### Parte 5: Segurança (3 min)

#### Implementação SRTP-like:

**1. Criptografia AES-GCM**
- AES: Advanced Encryption Standard (256 bits)
- GCM: Galois/Counter Mode
- Combina criptografia + autenticação

**2. Estrutura:**
- Header RTP: **em claro** (necessário para roteamento)
- Payload: **criptografado**
- Tag de autenticação: incluída pelo GCM

**3. Nonce (Number used Once):**
```python
nonce = struct.pack('!Q', sequence_number) + b'\x00\x00\x00\x00'
```
- Derivado do sequence number
- Garante que cada pacote tem nonce único

**4. AAD (Additional Authenticated Data):**
```python
encrypted = aesgcm.encrypt(nonce, payload, aad=header_rtp)
```
- Header RTP é autenticado mas não criptografado
- Detecta modificações no header

**Demonstração:**
1. Mostrar no Wireshark que o payload está criptografado
2. Explicar que sem a chave correta, não é possível:
   - Ver o conteúdo do vídeo
   - Modificar os dados sem detecção

### Parte 6: Perguntas Frequentes (1 min)

**Por que UDP e não TCP?**
- Vídeo em tempo real não pode esperar retransmissões
- Melhor perder alguns frames do que ter atraso
- RTP adiciona informações para lidar com perdas

**Por que clock de 90kHz?**
- Padrão do RTP para vídeo (RFC 3550)
- Permite precisão de ~11 microsegundos
- Compatível com MPEG e H.264

**Por que fragmentar em 1400 bytes?**
- MTU típico da Ethernet: 1500 bytes
- 1500 - 20 (IP) - 8 (UDP) - 12 (RTP) = 1460 bytes
- 1400 deixa margem de segurança

## Comandos Úteis Durante a Apresentação

### Ver estatísticas em tempo real:
```bash
# No servidor (a cada 30 frames)
Frame 30/300 | Seq: 45 | TS: 90000 | Size: 15234 bytes | Packets: 11
```

### Filtros Wireshark úteis:
```
udp.port == 5004                    # Todos os pacotes RTP
rtp                                 # Se Wireshark detectar RTP
udp.port == 5004 && udp.length > 100  # Pacotes grandes
```

### Analisar pacote específico:
```bash
python analyze_rtp.py "80 9a 00 01 00 00 0b b8 12 34 56 78 ..."
```

## Troubleshooting Durante a Apresentação

### Vídeo não aparece:
1. Verificar se cliente foi iniciado primeiro
2. Verificar firewall
3. Testar com `127.0.0.1`

### Muitos pacotes perdidos:
1. Normal em redes congestionadas
2. Explicar que é esperado em UDP
3. Mostrar como o sistema detecta e reporta

### Wireshark não mostra pacotes:
1. Verificar interface correta (Loopback para localhost)
2. Verificar filtro: `udp.port == 5004`
3. Reiniciar captura

## Pontos Fortes para Destacar

1. **Implementação Completa do RTP**
   - Header manual (não usamos biblioteca pronta)
   - Demonstra entendimento profundo do protocolo

2. **QoS Real**
   - DSCP marking funcional
   - Estatísticas precisas
   - Jitter buffer implementado

3. **Segurança Robusta**
   - AES-GCM é usado em SRTP real
   - Autenticação + criptografia
   - Nonce derivado corretamente

4. **Código Limpo e Educacional**
   - Bem comentado
   - Fácil de entender
   - Pronto para demonstração

## Conclusão

Este projeto demonstra:
- Compreensão profunda de protocolos de rede
- Implementação de conceitos de tempo real
- Aplicação de segurança em comunicações
- Capacidade de trabalhar com RFCs e padrões

**Mensagem final:** Sistema completo e funcional de streaming de vídeo com RTP, QoS e segurança, pronto para uso educacional e demonstração de conceitos de redes.
