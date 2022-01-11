import PIL
from PIL import Image, ImageTk
from tkinter import *
import cv2


class MovieButtonTest:
	def __init__(self, window):
		self.window = window
		self.delay = 15
		window.title("User Interface")
		self.video_source = "movie.mov"
		self.vid = 0
		self.canvas = Canvas(window, width = 400, height = 400)
		self.canvas.pack()
		self.hiButton = Button(window, text="hello", command = lambda: self.feedCallBack(window,"movie.mov"))
		self.hiButton.pack()
		self.getFeedButton = Button(window, text = "Get Feed", \
									command = self.feedCallBack(window,"movie.mov"))
		self.getFeedButton.pack()

	def update(self):
		ret, frame = self.get_frame()

		if ret:
			self.photo = ImageTk.PhotoImage(image = Image.fromarray(frame))
			self.canvas.create_image(0, 0, image = self.photo, anchor = NW)
		self.window.after(self.delay, self.update)

	#def callback(self):
	#	self.guess = Test()
	#	print('hi')

	def feedCallBack(self, window, video_source):
		self.vid = cv2.VideoCapture(video_source)
		self.update()

		#self.window.after(self.delay, self.update)

	def get_frame(self):
		ret, frame = self.vid.read()
		if ret:
			return (ret, cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
		else:
			return (ret, None)


root = Tk()
m = MovieButtonTest(root)
mainloop()