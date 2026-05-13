from tkinter import *
import tkinter.messagebox as tkMessageBox
from PIL import Image, ImageTk
import socket, threading, os
from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"

class Client:
	INIT = 0
	READY = 1
	PLAYING = 2
	state = INIT
	
	SETUP = 0
	PLAY = 1
	PAUSE = 2
	TEARDOWN = 3
	TX_RAPIDA = 4
	TX_NORMAL = 5
	TX_LENTA = 6
	
	# Iniciação
	def __init__(self, master, serveraddr, serverport, rtpport, filename):
		self.master = master
		self.master.protocol("WM_DELETE_WINDOW", self.handler)
		self.createWidgets()
		self.serverAddr = serveraddr
		self.serverPort = int(serverport)
		self.rtpPort = int(rtpport)
		self.fileName = filename
		self.rtspSeq = 0
		self.sessionId = 0
		self.requestSent = -1
		self.teardownAcked = 0
		self.connectToServer()
		self.frameNbr = 0
		self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) # Cria novo socket de datagrama para receber pacotes RTP do servidor
		
	# Constrói a interface gráfica
	def createWidgets(self):
		# Cria botão Setup
		self.setup = Button(self.master, width=20, padx=3, pady=3)
		self.setup["text"] = "Setup"
		self.setup["command"] = self.setupMovie
		self.setup.grid(row=1, column=0, padx=2, pady=2)
		
		# Cria botão Play		
		self.start = Button(self.master, width=20, padx=3, pady=3)
		self.start["text"] = "Play"
		self.start["command"] = self.playMovie
		self.start.grid(row=1, column=1, padx=2, pady=2)
		
		# Cria botão Pause			
		self.pause = Button(self.master, width=20, padx=3, pady=3)
		self.pause["text"] = "Pause"
		self.pause["command"] = self.pauseMovie
		self.pause.grid(row=1, column=2, padx=2, pady=2)
		
		# Cria botão Teardown
		self.teardown = Button(self.master, width=20, padx=3, pady=3)
		self.teardown["text"] = "Teardown"
		self.teardown["command"] =  self.exitClient
		self.teardown.grid(row=1, column=3, padx=2, pady=2)

		# Cria botão transmissão rápida
		self.txRapida = Button(self.master, width=20, padx=3, pady=3)
		self.txRapida["text"] = "Rápida"
		self.txRapida["command"] = self.setTxRapida
		self.txRapida.grid(row=2, column=0, padx=2, pady=2)

		# Cria botão transmissão normal
		self.txNormal = Button(self.master, width=20, padx=3, pady=3)
		self.txNormal["text"] = "Normal"
		self.txNormal["command"] = self.setTxNormal
		self.txNormal.grid(row=2, column=1, padx=2, pady=2)

		# Cria botão transmissão lenta
		self.txLenta = Button(self.master, width=20, padx=3, pady=3)
		self.txLenta["text"] = "Lenta"
		self.txLenta["command"] = self.setTxLenta
		self.txLenta.grid(row=2, column=2, padx=2, pady=2)
		
		# Cria label para exibir o filme
		self.label = Label(self.master, height=19)
		self.label.grid(row=0, column=0, columnspan=4, sticky=W+E+N+S, padx=5, pady=5) 
	
	# Handler do botão Setup
	def setupMovie(self):
		if self.state == self.INIT:
			self.sendRtspRequest(self.SETUP)
	
	# Handler do botão Teardown
	def exitClient(self):
		self.sendRtspRequest(self.TEARDOWN)		
		self.master.destroy() # Fecha a janela da interface gráfica
		os.remove(CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT) # Deleta a imagem cache do video

	# Handler do botão Pause
	def pauseMovie(self):
		if self.state == self.PLAYING:
			self.sendRtspRequest(self.PAUSE)
	
	# Handler do botão Play
	def playMovie(self):
		if self.state == self.READY:
			# Cria uma nova thread para escutar pacotes RTP
			threading.Thread(target=self.listenRtp).start()
			self.playEvent = threading.Event()
			self.playEvent.clear()
			self.sendRtspRequest(self.PLAY)

	# Handler do botão transmissão rápida
	def setTxRapida(self):
		if self.state != self.INIT:
			self.sendRtspRequest(self.TX_RAPIDA)

	# Handler do botão transmissão normal
	def setTxNormal(self):
		if self.state != self.INIT:
			self.sendRtspRequest(self.TX_NORMAL)

	# Handler do botão transmissão lenta
	def setTxLenta(self):
		if self.state != self.INIT:
			self.sendRtspRequest(self.TX_LENTA)
	
	# Escuta pacotes RTP
	def listenRtp(self):		
		while True:
			try:
				data = self.rtpSocket.recv(20480)
				if data:
					rtpPacket = RtpPacket()
					rtpPacket.decode(data)
					
					currFrameNbr = rtpPacket.seqNum()
					print("Número de sequência atual: " + str(currFrameNbr))
										
					if currFrameNbr > self.frameNbr: # Descarta o pacote atrasado
						self.frameNbr = currFrameNbr
						self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
			except:
				# Para de escutar mediante solicitação PAUSE ou TEARDOWN
				if self.playEvent.isSet(): 
					break
				
				# Fecha socket RTP ao receber ACK mediante solicitação TEARDOWN
				if self.teardownAcked == 1:
					self.rtpSocket.shutdown(socket.SHUT_RDWR)
					self.rtpSocket.close()
					break

	# Escreve o frame recebido em um arquivo de imagem temporário e retorna o arquivo de imagem					
	def writeFrame(self, data):
		cachename = CACHE_FILE_NAME + str(self.sessionId) + CACHE_FILE_EXT
		file = open(cachename, "wb")
		file.write(data)
		file.close()
		
		return cachename
	
	# Atualiza o arquivo de imagem como um frame de vídeo na interface gráfica
	def updateMovie(self, imageFile):
		photo = ImageTk.PhotoImage(Image.open(imageFile))
		self.label.configure(image = photo, height=288) 
		self.label.image = photo
		
	# Conecta ao servidor e começa uma nova sessão RTSP/TCP	
	def connectToServer(self):
		self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		try:
			self.rtspSocket.connect((self.serverAddr, self.serverPort))
		except:
			tkMessageBox.showwarning('Conexão Falhou', 'Conexão com \'%s\' falhou.' %self.serverAddr)
	
	# Envia solicitação RTSP ao servidor
	def sendRtspRequest(self, requestCode):
		# Solicitação Setup
		if requestCode == self.SETUP and self.state == self.INIT:
			threading.Thread(target=self.recvRtspReply).start()

            # Atualiza o número de sequência RTSP
			self.rtspSeq = 1
			
            # Escreve a solicitação RTSP a ser enviada
			request = "SETUP " + str(self.fileName) + "\n " + str(self.rtspSeq) + " \n RTSP/1.0 RTP/UDP " + str(self.rtpPort)
			self.rtspSocket.send(request.encode())
			
            # Acompanha a solicitação enviada
			self.requestSent = self.SETUP
		
		# Solicitação Play
		elif requestCode == self.PLAY and self.state == self.READY:
			# Atualiza o número de sequência RTSP
			self.rtspSeq = self.rtspSeq + 1 
			
            # Escreve a solicitação RTSP a ser enviada
			request = "PLAY " + "\n " + str(self.rtspSeq) 
			self.rtspSocket.send(request.encode("utf-8"))
			print ('-'*60 + "\nSolicitação PLAY enviada ao Servidor...\n" + '-'*60)
			
			# Acompanha a solicitação enviada
			self.requestSent = self.PLAY
		
		# Solicitação Pause
		elif requestCode == self.PAUSE and self.state == self.PLAYING:
			# Atualiza o número de sequência RTSP
			self.rtspSeq = self.rtspSeq + 1
			
			# Escreve a solicitação RTSP a ser enviada
			request = "PAUSE " + "\n " + str(self.rtspSeq)
			self.rtspSocket.send(request.encode("utf-8"))
			print ('-'*60 + "\nSolicitação PAUSE enviada ao Servidor...\n" + '-'*60)
			
            # Acompanha a solicitação enviada
			self.requestSent = self.PAUSE
			
		# Solicitação Teardown
		elif requestCode == self.TEARDOWN and not self.state == self.INIT:
			# Atualiza o número de sequência RTSP
			self.rtspSeq = self.rtspSeq + 1
			
			# Escreve a solicitação RTSP a ser enviada
			request = "TEARDOWN " + "\n " + str(self.rtspSeq)
			self.rtspSocket.send(request.encode("utf-8"))
			print ('-'*60 + "\nSolicitação TEARDOWN enviada ao Servidor...\n" + '-'*60)

			# Acompanha a solicitação enviada
			self.requestSent = self.TEARDOWN

		# Solicitação transmissão rápida
		elif requestCode == self.TX_RAPIDA and self.state != self.INIT:
			# Atualiza o número de sequência RTSP
			self.rtspSeq = self.rtspSeq + 1

			# Escreve a solicitação RTSP a ser enviada
			request = "TX_RAPIDA " + "\n " + str(self.rtspSeq)
			self.rtspSocket.send(request.encode("utf-8"))
			print ('-'*60 + "\nSolicitação transmissão RÁPIDA enviada ao Servidor...\n" + '-'*60)

			# Acompanha a solicitação enviada
			self.requestSent = self.TX_RAPIDA

		# Solicitação transmissão normal
		elif requestCode == self.TX_NORMAL and self.state != self.INIT:
			# Atualiza o número de sequência RTSP
			self.rtspSeq = self.rtspSeq + 1

			# Escreve a solicitação RTSP a ser enviada
			request = "TX_NORMAL " + "\n " + str(self.rtspSeq)
			self.rtspSocket.send(request.encode("utf-8"))
			print ('-'*60 + "\nSolicitação transmissão NORMAL enviada ao Servidor...\n" + '-'*60)

			# Acompanha a solicitação enviada
			self.requestSent = self.TX_NORMAL

		# Solicitação transmissão lenta
		elif requestCode == self.TX_LENTA and self.state != self.INIT:
			# Atualiza o número de sequência RTSP
			self.rtspSeq = self.rtspSeq + 1

			# Escreve a solicitação RTSP a ser enviada
			request = "TX_LENTA " + "\n " + str(self.rtspSeq)
			self.rtspSocket.send(request.encode("utf-8"))
			print ('-'*60 + "\nSolicitação transmissão LENTA enviada ao Servidor...\n" + '-'*60)

			# Acompanha a solicitação enviada
			self.requestSent = self.TX_LENTA

		else:
			return
		
		print('\nDados enviados:\n\n' + request)
	
	# Recebe resposta RTSP do servidor
	def recvRtspReply(self):
		while True:
			reply = self.rtspSocket.recv(1024)
			
			if reply: 
				self.parseRtspReply(reply.decode("utf-8"))
			
			# Encerra o socket RTSP mediante solicitação Teardown
			if self.requestSent == self.TEARDOWN:
				self.rtspSocket.shutdown(socket.SHUT_RDWR)
				self.rtspSocket.close()
				break
	
	# Analisa a resposta RTSP do servidor
	def parseRtspReply(self, data):
		lines = data.split('\n')
		seqNum = int(lines[1].split(' ')[1])
		
		# Processa apenas se o número de sequência da resposta do servidor for igual ao da solicitação
		if seqNum == self.rtspSeq:
			session = int(lines[2].split(' ')[1])
			# Novo ID de sessão RTSP
			if self.sessionId == 0:
				self.sessionId = session
			
			# Processa apenas se o ID de sessão for igual
			if self.sessionId == session:
				if int(lines[0].split(' ')[1]) == 200: 
					if self.requestSent == self.SETUP:
						# Atualiza o estado RTSP
						print ("\nAtualizando estado RTSP...") 
						self.state = self.READY 
						
                        # Abre a porta RTP
						print ("\nConfigurando porta RTP para stream de vídeo...") 
						self.openRtpPort() 
			
					elif self.requestSent == self.PLAY:
						self.state = self.PLAYING
						print ('-'*60 + "\nCliente está PLAYING...\n" + '-'*60) 

					elif self.requestSent == self.PAUSE:
						self.state = self.READY
						
						# O thread de reprodução é encerrado e um novo thread é criado em seguida
						self.playEvent.set()
			
					elif self.requestSent == self.TEARDOWN:
						self.state = self.INIT
						
						# Sinalizar teardownAcked para encerrar o socket
						self.teardownAcked = 1 

					elif self.requestSent == self.TX_RAPIDA:
						print("Transmissão RÁPIDA confirmada pelo servidor.")

					elif self.requestSent == self.TX_NORMAL:
						print("Transmissão NORMAL confirmada pelo servidor.")

					elif self.requestSent == self.TX_LENTA:
						print("Transmissão LENTA confirmada pelo servidor.")
	
	# Abre o socket RTP conectado a uma porta específica
	def openRtpPort(self):
		self.rtpSocket.settimeout(0.5) # Seta o valor de timeout do socket para 0.5 segundos
		
		# Conecta o socket ao endereço usando a porta RTP dada pelo usuário cliente
		try:
			self.rtpSocket.bind((self.serverAddr, self.rtpPort)) # Cuidado com o formato do endereço, o rtpPort deve ser maior que 1024
			print ("\nPorta RTP conectada com successo!")
		except:
			tkMessageBox.showwarning('Não foi possível conectar', 'Não foi possível conectar na PORTA=%d' %self.rtpPort)

	# Handler ao fechar explicitamente a janela da interface gráfica
	def handler(self):
		self.pauseMovie()
		if tkMessageBox.askokcancel("Sair?", "Tem certeza que deseja sair?"):
			self.exitClient()
		else: # Quando o usuário pressionar cancelar, retomar reprodução do filme.
			self.playMovie()