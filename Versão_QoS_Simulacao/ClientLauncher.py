from tkinter import Tk
from Client import Client

if __name__ == "__main__":
	serverAddr = "127.0.0.1"
	serverPort = 554
	rtpPort = 5004
	fileName = "movie.Mjpeg"

	root = Tk()

	# Cria um novo cliente
	app = Client(root, serverAddr, serverPort, rtpPort, fileName)
	app.master.title("RTPClient")
	root.mainloop()