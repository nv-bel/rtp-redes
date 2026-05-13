from time import time

HEADER_SIZE = 12

class RtpPacket:	
	header = bytearray(HEADER_SIZE)
	
	def __init__(self):
		pass
		
	# Codifica o pacote RTP com campos de cabeçalho e carga útil
	def encode(self, version, padding, extension, cc, seqnum, marker, pt, ssrc, payload):
		timestamp = int(time())
		header = bytearray(HEADER_SIZE)
		
        # O campo versão RTP(v) deve ser setado como 2, os campos padding(P), extension(X), número de fontes de 
		# contribuição (CC) e marcador (M) foram setados como 0 neste lab. Por conta de não termos outras fontes de 
		# contribuição (campo CC == 0), o campo CRSC não existe. Assim, o tamanho do cabeçalho do pacote é de 12 bytes.
        # Tudo a cima feito em ServerWorker.py

		# header[0] = version + padding + extension + cc + marker + pt + seqnum + ssrc
		self.header[0] = version << 6
		self.header[0] = self.header[0] | padding << 5
		self.header[0] = self.header[0] | extension << 4
		self.header[0] = self.header[0] | cc
		self.header[1] = marker << 7
		self.header[1] = self.header[1] | pt
		
		self.header[2] = seqnum >> 8
		self.header[3] = seqnum
		
		self.header[4] = (timestamp >> 24) & 0xFF
		self.header[5] = (timestamp >> 16) & 0xFF
		self.header[6] = (timestamp >> 8) & 0xFF
		self.header[7] = timestamp & 0xFF
		
		self.header[8] = ssrc >> 24
		self.header[9] = ssrc >> 16
		self.header[10] = ssrc >> 8
		self.header[11] = ssrc
		
		# Obtém a carga útil através do argumento
		self.payload = payload
		
	# Decodifica pacote RTP
	def decode(self, byteStream):
		self.header = bytearray(byteStream[:HEADER_SIZE])
		self.payload = byteStream[HEADER_SIZE:]
	
	# Retorna versão RTP
	def version(self):
		return int(self.header[0] >> 6)
	
	# Retorna número de sequência (frame)
	def seqNum(self):
		seqNum = self.header[2] << 8 | self.header[3]
		return int(seqNum)
	
	# Retorna timestamp
	def timestamp(self):
		timestamp = self.header[4] << 24 | self.header[5] << 16 | self.header[6] << 8 | self.header[7]
		return int(timestamp)
	
	# Retorna tipo de carga útil
	def payloadType(self):
		pt = self.header[1] & 127
		return int(pt)
	
	# Retorna carga útil
	def getPayload(self):
		return self.payload
		
	# Retorna pacote RTP
	def getPacket(self):
		return self.header + self.payload