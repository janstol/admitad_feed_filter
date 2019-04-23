from tkinter import Tk, Frame, messagebox
from screens import StartScreen, ProcessingScreen


class AdmitadFeedFilterApp(Tk):

	def __init__(self, *args, **kwargs):
		Tk.__init__(self, *args, **kwargs)
		self.title('Aliexpress Feed Filter (v0.1.1)')
		# Tk.iconbitmap(self, default=icon.ico)

		w, h = 500, 370  # window width, height
		ws = self.winfo_screenwidth()  # width of the screen
		hs = self.winfo_screenheight()  # height of the screen
		x = (ws / 2) - (w / 2)
		y = (hs / 2) - (h / 2)

		self.geometry('%dx%d+%d+%d' % (w, h, x, y))
		self.resizable(width=False, height=False)

		container = Frame(self)
		container.pack(side='top', fill='both', expand=True)
		container.grid_rowconfigure(0, weight=1)
		container.grid_columnconfigure(0, weight=1)

		self.exit = False
		self.frames = {}

		# app data
		self.file = None
		self.output_dir = None
		self.commission = None
		self.categories = []
		self.maxsize = None
		self.end_date = None

		for P in (StartScreen, ProcessingScreen):
			frame = P(container, self)
			self.frames[P] = frame
			frame.grid(row=0, column=0, sticky='nsew')

		self.show_frame(StartScreen)

	def show_frame(self, controller):
		frame = self.frames[controller]
		frame.tkraise()

	def show_err_dialog(self, messages):
		error = ""
		for e in messages:
			error += e + "\n"
		messagebox.showerror('Error', error)

	def show_ask_dialog(self, title, message):
		return messagebox.askokcancel(title, message)


def main():
	app = AdmitadFeedFilterApp()
	app.mainloop()


if __name__ == '__main__':
	main()
