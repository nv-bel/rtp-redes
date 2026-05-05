# Quick Start Guide

## Instalação Rápida

### 1. Instalar dependências
```bash
pip install -r requirements.txt
```

### 2. Criar vídeo de teste
```bash
python create_test_video.py
```

### 3. Executar o projeto

**Terminal 1 - Cliente:**
```bash
python client.py
```

**Terminal 2 - Servidor:**
```bash
python server.py
```

## Estrutura de Arquivos

```
trab_redes/
├── server.py                  # Servidor RTP (transmite vídeo)
├── client.py                  # Cliente RTP (recebe e exibe)
├── requirements.txt           # Dependências Python
├── create_test_video.py       # Cria vídeo de teste
├── analyze_rtp.py             # Analisa pacotes RTP
├── README.md                  # Documentação completa
├── GUIA_APRESENTACAO.md       # Guia para apresentação
└── PASSOS_PROJETO_RTP.md      # Especificação original
```

## Funcionalidades Principais

### ✅ Protocolo RTP Completo
- Cabeçalho de 12 bytes conforme RFC 3550
- Sequence numbers e timestamps
- Fragmentação por MTU (1400 bytes)

### ✅ QoS (Quality of Service)
- DSCP marking (EF - 0xB8)
- Detecção de perda de pacotes
- Medição de jitter
- Estatísticas em tempo real

### ✅ Segurança (SRTP-like)
- Criptografia AES-GCM do payload
- Header RTP em claro (autenticado)
- Nonce derivado do sequence number

## Comandos Úteis

### Criar vídeo com duração específica
```bash
python create_test_video.py 30
```

### Usar vídeo diferente
```bash
python server.py meu_video.mp4
```

### Analisar pacote RTP
```bash
python analyze_rtp.py
```

## Captura com Wireshark

1. Abrir Wireshark
2. Selecionar interface (Loopback para localhost)
3. Filtro: `udp.port == 5004`
4. Iniciar captura
5. Executar cliente e servidor

## Teclas de Atalho

- **Ctrl+C**: Parar servidor/cliente
- **Q**: Fechar janela de vídeo (no cliente)

## Troubleshooting

### Erro: "Could not open video file"
```bash
python create_test_video.py
```

### Erro: "Address already in use"
- Fechar outros programas na porta 5004
- Ou aguardar alguns segundos

### Vídeo não aparece
1. Iniciar cliente ANTES do servidor
2. Verificar firewall
3. Usar localhost (127.0.0.1)

## Informações Técnicas

- **Porta UDP**: 5004
- **Payload Type**: 26 (JPEG)
- **Clock Rate**: 90kHz
- **MTU**: 1400 bytes
- **Criptografia**: AES-GCM-256

## Para Apresentação

Ver arquivo completo: `GUIA_APRESENTACAO.md`

Resumo:
1. Iniciar Wireshark com filtro `udp.port == 5004`
2. Iniciar cliente
3. Iniciar servidor
4. Mostrar vídeo funcionando
5. Analisar pacotes no Wireshark
6. Explicar estatísticas de QoS
7. Demonstrar segurança (payload criptografado)

## Referências

- RFC 3550 (RTP): https://www.rfc-editor.org/rfc/rfc3550
- RFC 3711 (SRTP): https://www.rfc-editor.org/rfc/rfc3711
- RFC 2474 (DSCP): https://www.rfc-editor.org/rfc/rfc2474
