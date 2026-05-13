
class VideoStream:
	def __init__(self, filename):
		self.filename = filename
		try:
			self.file = open(filename, 'rb')
		except:
			raise IOError
		self.frameNum = 0
		
	# Obtém o próximo frame
	def nextFrame(self):
		data = self.file.read(5) # Obtém o tamanho do frame através do 5 primeiros bits
		if data: 
			framelength = int(data)
			data = self.file.read(framelength) # Lê o frame atual
			self.frameNum += 1
		return data
		
	# Obtém o número do frame
	def frameNbr(self):
		return self.frameNum