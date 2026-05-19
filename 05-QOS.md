# 05 - Quality of Service (QoS) em Streaming de Vídeo

## Introdução ao QoS

Quality of Service (QoS) refere-se a mecanismos que garantem níveis específicos de desempenho para diferentes tipos de tráfego em uma rede. Em streaming de vídeo, QoS é crucial para garantir baixa latência e reprodução suave.

## Por que QoS é Necessário?

### Problema: Tráfego Competindo por Recursos

Em uma rede típica, múltiplos tipos de tráfego competem pelos mesmos recursos:

```
┌─────────────────────────────────────────────────────────┐
│                    Rede Compartilhada                   │
│                                                         │
│  [Streaming de Vídeo] ─┐                                │
│  [Download de Arquivo] ─┤                               │
│  [Navegação Web]       ─┼──► [Router] ──► [Internet]    │
│  [Email]               ─┤                               │
│  [VoIP]                ─┘                               │
└─────────────────────────────────────────────────────────┘
```

**Sem QoS:**
- Todos os pacotes tratados igualmente
- Streaming pode sofrer com latência variável (jitter)
- Downloads grandes podem congestionar a rede
- Vídeo pode travar ou ter qualidade degradada

**Com QoS:**
- Tráfego prioritário (vídeo, voz) tem preferência
- Latência garantida para aplicações sensíveis
- Melhor experiência do usuário

## Modelo DiffServ (Differentiated Services)

### Conceito

DiffServ é um modelo de QoS que classifica e gerencia tráfego de rede através de marcação de pacotes.

**Princípio:**
```
Pacote IP → Marcado com DSCP → Roteadores tratam baseado na marcação
```

### Campo TOS (Type of Service) no Cabeçalho IP

```
Cabeçalho IPv4:
 0                   1                   2                   3
 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|Version|  IHL  |Type of Service|          Total Length         |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|         Identification        |Flags|      Fragment Offset    |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|  Time to Live |    Protocol   |         Header Checksum       |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                       Source Address                          |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
|                    Destination Address                        |
+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
```

**Campo Type of Service (8 bits):**
```
 0   1   2   3   4   5   6   7
+---+---+---+---+---+---+---+---+
|         DSCP          |  ECN  |
+---+---+---+---+---+---+---+---+
```

**DSCP (Differentiated Services Code Point) - 6 bits:**
- Bits 0-5 do campo TOS
- Define a classe de serviço
- Valores: 0 a 63

**ECN (Explicit Congestion Notification) - 2 bits:**
- Bits 6-7 do campo TOS
- Notificação de congestionamento
- Não usado neste projeto

## DSCP: Classes de Serviço

### Valores DSCP Padronizados

| DSCP | Binário | Decimal | Nome | Uso Típico |
|------|---------|---------|------|------------|
| EF | 101110 | 46 | Expedited Forwarding | Voz, vídeo ao vivo |
| AF41 | 100010 | 34 | Assured Forwarding 4-1 | Vídeo streaming |
| AF31 | 011010 | 26 | Assured Forwarding 3-1 | Streaming de alta prioridade |
| AF21 | 010010 | 18 | Assured Forwarding 2-1 | Dados de alta prioridade |
| AF11 | 001010 | 10 | Assured Forwarding 1-1 | Dados de baixa prioridade |
| BE | 000000 | 0 | Best Effort | Tráfego padrão |

### EF (Expedited Forwarding)

**DSCP = 46 (101110 em binário)**

**Características:**
- Mais alta prioridade
- Baixa latência garantida
- Baixo jitter
- Baixa perda de pacotes
- Usado para tráfego sensível ao tempo

**Aplicações:**
- VoIP (telefonia IP)
- Videoconferência
- Streaming de vídeo ao vivo
- Jogos online

**Comportamento nos Roteadores:**
```
┌─────────────────────────────────────┐
│           Fila do Router            │
├─────────────────────────────────────┤
│ [EF] ──► Processado imediatamente   │
│ [AF41] ──► Fila de alta prioridade  │
│ [AF31] ──► Fila de média prioridade │
│ [BE] ──► Fila de baixa prioridade   │
└─────────────────────────────────────┘
```

## Implementação de QoS no Projeto

### Código no Servidor (ServerWorker.py)

**Localização:** Linha 83 do arquivo ServerWorker.py

```python
elif requestType == self.PLAY:
    if self.state == self.READY:
        print("Processando PLAY\n")
        self.state = self.PLAYING
        
        # Cria socket UDP para RTP
        self.clientInfo["rtpSocket"] = socket.socket(
            socket.AF_INET, socket.SOCK_DGRAM
        )
        
        # Define prioridade alta para os pacotes RTP (QoS via DSCP)
        self.clientInfo["rtpSocket"].setsockopt(
            socket.IPPROTO_IP, socket.IP_TOS, 0xB8
        )
```

### Análise Detalhada

**1. Criação do Socket UDP:**
```python
self.clientInfo["rtpSocket"] = socket.socket(
    socket.AF_INET,      # Família de endereços IPv4
    socket.SOCK_DGRAM    # Tipo de socket: UDP
)
```

**2. Configuração de QoS:**
```python
self.clientInfo["rtpSocket"].setsockopt(
    socket.IPPROTO_IP,   # Nível: IP
    socket.IP_TOS,       # Opção: Type of Service
    0xB8                 # Valor: DSCP + ECN
)
```

### Decodificação do Valor 0xB8

**0xB8 em diferentes bases:**
```
Hexadecimal: 0xB8
Decimal: 184
Binário: 10111000
```

**Separação em DSCP e ECN:**
```
Binário: 10111000
         ├─────┤├┤
         DSCP   ECN

DSCP (6 bits): 101110 = 46 decimal = EF (Expedited Forwarding)
ECN (2 bits): 00 = Sem notificação de congestionamento
```

**Cálculo:**
```
DSCP = 46 (decimal)
DSCP << 2 = 46 * 4 = 184 (desloca 2 bits para incluir ECN)
184 em hexadecimal = 0xB8
```

**Verificação:**
```python
dscp = 46
ecn = 0
tos = (dscp << 2) | ecn
print(hex(tos))  # 0xb8
```

### Método setsockopt()

**Sintaxe:**
```python
socket.setsockopt(level, optname, value)
```

**Parâmetros:**

**level (socket.IPPROTO_IP):**
- Define o nível do protocolo
- `IPPROTO_IP`: Opções no nível IP
- Outras opções: `SOL_SOCKET`, `IPPROTO_TCP`, etc.

**optname (socket.IP_TOS):**
- Nome da opção a ser configurada
- `IP_TOS`: Type of Service (campo TOS do cabeçalho IP)
- Permite marcar pacotes com DSCP

**value (0xB8):**
- Valor a ser atribuído
- 0xB8 = DSCP 46 (EF) + ECN 0
- Marca todos os pacotes enviados por este socket

### Efeito na Rede

**Pacote RTP sem QoS:**
```
┌─────────────────────────────────────────────────────┐
│                  Cabeçalho IP                       │
├─────────────────────────────────────────────────────┤
│ TOS: 00000000 (DSCP=0, BE - Best Effort)          │
│ ...                                                 │
├─────────────────────────────────────────────────────┤
│                  Cabeçalho UDP                      │
├─────────────────────────────────────────────────────┤
│                  Cabeçalho RTP                      │
├─────────────────────────────────────────────────────┤
│                  Payload (JPEG)                     │
└─────────────────────────────────────────────────────┘
```

**Pacote RTP com QoS (0xB8):**
```
┌─────────────────────────────────────────────────────┐
│                  Cabeçalho IP                       │
├─────────────────────────────────────────────────────┤
│ TOS: 10111000 (DSCP=46, EF - Expedited Forwarding)  │
│ ...                                                 │
├─────────────────────────────────────────────────────┤
│                  Cabeçalho UDP                      │
├─────────────────────────────────────────────────────┤
│                  Cabeçalho RTP                      │
├─────────────────────────────────────────────────────┤
│                  Payload (JPEG)                     │
└─────────────────────────────────────────────────────┘
```

### Comportamento nos Roteadores

**Router com suporte a DiffServ:**

```
Pacote chega com DSCP=46 (EF)
        │
        ▼
Router lê campo TOS
        │
        ▼
Identifica DSCP=46 (EF)
        │
        ▼
Coloca em fila de alta prioridade
        │
        ▼
Processa antes de pacotes BE
        │
        ▼
Encaminha com baixa latência
```

**Comparação de Filas:**

```
┌─────────────────────────────────────────────────────┐
│                  Router Queue                       │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Fila EF (Expedited Forwarding):                    │
│  [RTP Video] → Processado imediatamente             │
│                                                     │
│  Fila AF (Assured Forwarding):                      │
│  [HTTP] [HTTPS] → Processado em seguida             │
│                                                     │
│  Fila BE (Best Effort):                             │
│  [Email] [FTP] [Torrent] → Processado por último    │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Benefícios do QoS no Streaming

### 1. Latência Reduzida

**Sem QoS:**
```
Pacote RTP enviado → Fila com outros pacotes → Atraso variável → Cliente
Latência: 50-500ms (variável)
```

**Com QoS (EF):**
```
Pacote RTP enviado → Fila prioritária → Atraso mínimo → Cliente
Latência: 10-50ms (consistente)
```

### 2. Jitter Reduzido

**Jitter = Variação na latência**

**Sem QoS:**
```
Pacote 1: 100ms
Pacote 2: 250ms  ← Jitter: 150ms
Pacote 3: 80ms   ← Jitter: 170ms
Pacote 4: 300ms  ← Jitter: 220ms

Resultado: Reprodução irregular, frames pulando
```

**Com QoS:**
```
Pacote 1: 20ms
Pacote 2: 25ms   ← Jitter: 5ms
Pacote 3: 22ms   ← Jitter: 3ms
Pacote 4: 24ms   ← Jitter: 2ms

Resultado: Reprodução suave
```

### 3. Perda de Pacotes Reduzida

**Sem QoS (congestionamento):**
```
Router com buffer cheio:
  [BE][BE][BE][BE][BE][BE][BE][BE]
  
Novo pacote RTP chega → Buffer cheio → Pacote descartado
Taxa de perda: 5-10%
```

**Com QoS:**
```
Router com buffer cheio:
  [EF][EF][AF][AF][BE][BE][BE][BE]
  
Novo pacote RTP (EF) chega → Descarta pacote BE → Pacote RTP aceito
Taxa de perda: <1%
```

## Cenários de Teste

### Cenário 1: Rede Sem Congestionamento

```
Largura de banda disponível: 100 Mbps
Tráfego de vídeo: 5 Mbps
Outros tráfegos: 10 Mbps

Resultado:
  - Sem QoS: Funciona bem
  - Com QoS: Funciona bem
  
Conclusão: QoS não faz diferença significativa
```

### Cenário 2: Rede Congestionada

```
Largura de banda disponível: 10 Mbps
Tráfego de vídeo: 5 Mbps
Outros tráfegos: 20 Mbps (downloads, uploads)

Sem QoS:
  - Latência: 200-800ms
  - Jitter: 300ms
  - Perda: 8%
  - Experiência: Vídeo travando, qualidade ruim

Com QoS (EF):
  - Latência: 20-50ms
  - Jitter: 10ms
  - Perda: <1%
  - Experiência: Vídeo suave, boa qualidade
```

### Cenário 3: Múltiplos Streams

```
Largura de banda disponível: 50 Mbps
3 streams de vídeo: 5 Mbps cada
Outros tráfegos: 40 Mbps

Sem QoS:
  - Todos os streams competem igualmente
  - Qualidade inconsistente
  - Alguns streams podem travar

Com QoS (EF):
  - Streams de vídeo têm prioridade
  - Qualidade consistente para todos
  - Outros tráfegos ajustam-se automaticamente
```

## Limitações e Considerações

### 1. Suporte de Rede

**Requisito:**
- Roteadores devem suportar DiffServ
- Configuração adequada nos roteadores
- Políticas de QoS configuradas

**Realidade:**
```
Rede Doméstica:
  - Roteadores simples podem ignorar DSCP
  - QoS pode não ter efeito

Rede Corporativa:
  - Roteadores gerenciados suportam DiffServ
  - QoS funciona conforme esperado

Internet Pública:
  - ISPs podem remarcar ou ignorar DSCP
  - QoS limitado ao domínio local
```

### 2. Configuração do Sistema Operacional

**Linux:**
```bash
# Verificar se TOS está sendo setado
tcpdump -vv -i eth0 | grep tos

# Configurar iptables para marcar pacotes
iptables -t mangle -A OUTPUT -p udp --dport 5004 -j DSCP --set-dscp 46
```

**Windows:**
```powershell
# Verificar política de QoS
Get-NetQosPolicy

# Criar política de QoS
New-NetQosPolicy -Name "RTP Video" -DSCPAction 46 -NetworkProfile All
```

### 3. Permissões

**Alguns sistemas requerem privilégios elevados:**

```python
# Pode falhar sem permissões adequadas
try:
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)
except PermissionError:
    print("Permissão negada para configurar QoS")
    # Continua sem QoS
```

## Alternativas e Extensões

### 1. Outros Valores DSCP

**Para diferentes tipos de streaming:**

```python
# Vídeo ao vivo (mais crítico)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)  # EF (46)

# Vídeo sob demanda (menos crítico)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x88)  # AF41 (34)

# Streaming de áudio
sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)  # EF (46)

# Download de vídeo (não tempo real)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0x48)  # AF21 (18)
```

### 2. QoS Adaptativo

**Ajustar DSCP baseado em condições:**

```python
def setQoS(self, networkCondition):
    if networkCondition == "excellent":
        dscp = 0  # Best Effort (sem necessidade de prioridade)
    elif networkCondition == "good":
        dscp = 34  # AF41
    elif networkCondition == "poor":
        dscp = 46  # EF (máxima prioridade)
    
    tos = dscp << 2
    self.rtpSocket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, tos)
```

### 3. Monitoramento de QoS

**Verificar se QoS está funcionando:**

```python
import socket

# Obter valor TOS atual
tos = sock.getsockopt(socket.IPPROTO_IP, socket.IP_TOS)
dscp = tos >> 2
print(f"DSCP atual: {dscp}")

# Verificar se é EF
if dscp == 46:
    print("QoS configurado corretamente (EF)")
else:
    print(f"QoS não está em EF, valor atual: {dscp}")
```

## Comparação: Com e Sem QoS

### Métricas de Desempenho

| Métrica | Sem QoS | Com QoS (EF) | Melhoria |
|---------|---------|--------------|----------|
| Latência Média | 150ms | 30ms | 80% |
| Jitter | 100ms | 10ms | 90% |
| Perda de Pacotes | 5% | 0.5% | 90% |
| Frames Perdidos | 50/1000 | 5/1000 | 90% |
| Qualidade Percebida | Ruim | Excelente | - |

### Experiência do Usuário

**Sem QoS:**
```
[Frame 1] → 100ms → [Frame 2] → 300ms → [Frame 4] (Frame 3 perdido)
                                         ↓
                                    Vídeo trava
```

**Com QoS:**
```
[Frame 1] → 20ms → [Frame 2] → 22ms → [Frame 3] → 21ms → [Frame 4]
                                                           ↓
                                                    Vídeo suave
```

## Implementação Prática: Passo a Passo

### 1. Criar Socket UDP

```python
rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
```

### 2. Configurar QoS

```python
# Definir DSCP = 46 (EF)
dscp = 46
ecn = 0
tos = (dscp << 2) | ecn  # 0xB8

# Aplicar ao socket
rtpSocket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, tos)
```

### 3. Enviar Pacotes

```python
# Todos os pacotes enviados por este socket terão DSCP=46
rtpSocket.sendto(rtpPacket, (clientAddress, clientPort))
```

### 4. Verificar (Opcional)

```python
# Verificar valor TOS
current_tos = rtpSocket.getsockopt(socket.IPPROTO_IP, socket.IP_TOS)
print(f"TOS configurado: {hex(current_tos)}")  # 0xb8
```

## Resumo de QoS

### Pontos-Chave

1. **QoS garante qualidade** em redes congestionadas
2. **DSCP marca pacotes** com classe de serviço
3. **EF (46) é a mais alta prioridade** para tempo real
4. **setsockopt() configura TOS** no socket
5. **0xB8 = DSCP 46 (EF)** para streaming de vídeo
6. **Roteadores processam EF primeiro** reduzindo latência
7. **Benefícios: menor latência, jitter e perda**

### Código Essencial

```python
# Configurar QoS para streaming de vídeo
rtpSocket.setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8)
```

---

**Próximo:** [06-FLUXO-EXECUCAO.md](06-FLUXO-EXECUCAO.md) - Fluxo de Execução Detalhado
