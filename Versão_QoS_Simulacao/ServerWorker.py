from random import randint
import threading, socket

from VideoStream import VideoStream
from RtpPacket import RtpPacket

class ServerWorker:
	SETUP = 'SETUP'
	PLAY = 'PLAY'
	PAUSE = 'PAUSE'
	TEARDOWN = 'TEARDOWN'

	TX_RAPIDA_CMD = 'TX_RAPIDA'
	TX_NORMAL_CMD = 'TX_NORMAL'
	TX_LENTA_CMD = 'TX_LENTA'

	# Perfis simples de velocidade de transmissão
	TX_RAPIDA = 0.01
	TX_NORMAL = 0.05
	TX_LENTA = 1.00
	
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT

	OK_200 = 0
	FILE_NOT_FOUND_404 = 1
	CON_ERR_500 = 2
	
	clientInfo = {}
	
	def __init__(self, clientInfo):
		self.clientInfo = clientInfo

		# Velocidade padrão: transmissão normal
		self.transmission_delay = self.TX_NORMAL
		
	def run(self):
		threading.Thread(target=self.recvRtspRequest).start()
	
	# Recebe solicitação RTSP do cliente
	def recvRtspRequest(self):
		connSocket = self.clientInfo['rtspSocket'][0]
		while True:            
			data = connSocket.recv(256)
			if data:
				print("Dados recebidos:\n" + data.decode("utf-8"))
				self.processRtspRequest(data.decode("utf-8"))
	
	# Processa solicitação RTSP enviada pelo cliente
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
				
				# Obtém a porta RTP/UDP da última linha
				self.clientInfo['rtpPort'] = request[2].split(' ')[3]
		
		elif requestType == self.PLAY:
			if self.state == self.READY:
				print("Processando PLAY\n")
				print("Velocidade de transmissão aplicada - intervalo de envio =", self.transmission_delay)
				
				self.state = self.PLAYING
				
				self.clientInfo["rtpSocket"] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				
				# Define prioridade alta para os pacotes RTP (QoS via DSCP)
				self.clientInfo["rtpSocket"].setsockopt(socket.IPPROTO_IP, socket.IP_TOS, 0xB8) 

				self.replyRtsp(self.OK_200, seq[1])
				
				self.clientInfo['event'] = threading.Event()
				self.clientInfo['worker'] = threading.Thread(target=self.sendRtp) 
				self.clientInfo['worker'].start()
		
		elif requestType == self.PAUSE:
			if self.state == self.PLAYING:
				print("Processando PAUSE\n")
				self.state = self.READY
				
				self.clientInfo['event'].set()
				self.replyRtsp(self.OK_200, seq[1])
		
		elif requestType == self.TEARDOWN:
			print("Processando TEARDOWN\n")

			self.clientInfo['event'].set()
			self.replyRtsp(self.OK_200, seq[1])
			
			self.clientInfo['rtpSocket'].close()

		elif requestType == self.TX_RAPIDA_CMD:
			self.transmission_delay = self.TX_RAPIDA
			print("Velocidade de transmissão alterada para RÁPIDA")
			print("Novo delay:", self.transmission_delay)
			self.replyRtsp(self.OK_200, seq[1])

		elif requestType == self.TX_NORMAL_CMD:
			self.transmission_delay = self.TX_NORMAL
			print("Velocidade de transmissão alterada para NORMAL")
			print("Novo delay:", self.transmission_delay)
			self.replyRtsp(self.OK_200, seq[1])

		elif requestType == self.TX_LENTA_CMD:
			self.transmission_delay = self.TX_LENTA
			print("Velocidade de transmissão alterada para LENTA")
			print("Novo delay:", self.transmission_delay)
			self.replyRtsp(self.OK_200, seq[1])
			
	# Envia pacotes RTP por UDP
	def sendRtp(self):
		while True:
			# Controla o intervalo de envio dos pacotes RTP
			self.clientInfo['event'].wait(self.transmission_delay)
			
			if self.clientInfo['event'].isSet(): 
				break 
				
			data = self.clientInfo['videoStream'].nextFrame()

			# Se não houver mais frames, encerra o envio RTP
			if not data:
				print("Fim do vídeo. Encerrando transmissão RTP.")
				break

			frameNumber = self.clientInfo['videoStream'].frameNbr()

			try:
				address = self.clientInfo['rtspSocket'][1][0]
				port = int(self.clientInfo['rtpPort'])

				self.clientInfo['rtpSocket'].sendto(
					self.makeRtp(data, frameNumber),
					(address, port)
				)

			except:
				print("Socket RTP indisponível. Encerrando transmissão.")
				break

	# RTP - Empacotando dados de vídeo
	def makeRtp(self, payload, frameNbr):
		version = 2
		padding = 0
		extension = 0
		cc = 0
		marker = 0
		pt = 26
		seqnum = frameNbr		
		ssrc = 0 
		
		rtpPacket = RtpPacket()
		rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
		
		return rtpPacket.getPacket()
		
	# Envia resposta RTSP para o cliente
	def replyRtsp(self, code, seq):
		if code == self.OK_200:
			print("200 OK")
			reply = 'RTSP/1.0 200 OK\nCSeq: ' + seq + '\nSession: ' + str(self.clientInfo['session'])
			connSocket = self.clientInfo['rtspSocket'][0]
			connSocket.send(reply.encode())
		
		elif code == self.FILE_NOT_FOUND_404:
			print("404 NOT FOUND")

		elif code == self.CON_ERR_500:
			print("500 CONNECTION ERROR")