import os
import queue
import re
from datetime import datetime
from tkinter import Frame, StringVar, IntVar, DoubleVar, ttk, filedialog
from tkinter import LEFT, RIGHT, BOTTOM, CENTER, X

from admitad_feed_filter import AliexpressFeedFilter
from style.fonts import LARGE_FONT

NOW = datetime.now()
CURRENT_DATE = NOW.strftime('%Y-%m-%d')


class StartScreen(Frame):
	"""
	Screen with filter configuration
	"""

	def __init__(self, parent, controller):
		Frame.__init__(self, parent)
		self.controller = controller
		units = ["KB", "MB"]

		self.file = StringVar(value='')
		self.output_dir = StringVar(value='')
		self.commission = DoubleVar(value=15.0)
		self.categories = StringVar(value='')
		self.maxsize = IntVar(value=5)
		self.maxsize_unit = StringVar(value=units[1])
		self.end_date = StringVar(value=CURRENT_DATE)

		# file chooser
		file_group = ttk.LabelFrame(self, text='File input [csv]')
		file_entry = ttk.Entry(file_group, width=59, textvariable=self.file, state='readonly')
		file_button = ttk.Button(file_group, text='Open...', command=self.open_file)

		file_group.grid(row=0, column=0, padx=10, pady=10, sticky='nesw', columnspan=2)
		file_entry.pack(side=LEFT, padx=10, pady=10, fill=X, expand=True)
		file_button.pack(side=RIGHT, padx=10, expand=True)

		# output dir
		file_group = ttk.LabelFrame(self, text='Output directory')
		file_entry = ttk.Entry(file_group, width=59, textvariable=self.output_dir, state='readonly')
		file_button = ttk.Button(file_group, text='Select', command=self.select_out_dir)

		file_group.grid(row=1, column=0, padx=10, sticky='nesw', columnspan=2)
		file_entry.pack(side=LEFT, padx=10, pady=10, fill=X, expand=True)
		file_button.pack(side=RIGHT, padx=10, expand=True)

		# commission
		commission_group = ttk.LabelFrame(self, text='Minimal commission [%]')
		commission_entry = ttk.Entry(commission_group, textvariable=self.commission)

		commission_validator = self.register(self.validate_float)
		commission_entry.config(validate='key', validatecommand=(commission_validator, '%P'))

		commission_group.grid(row=2, column=0, padx=10, pady=10, sticky='nesw')
		commission_entry.pack(pady=10)

		# end date
		end_date_group = ttk.LabelFrame(self, text='End date [YYYY-MM-DD]')
		end_date_entry = ttk.Entry(end_date_group, textvariable=self.end_date)
		end_date_reset = ttk.Button(end_date_group, text='Today', command=lambda: self.end_date.set(CURRENT_DATE))

		end_date_group.grid(row=2, column=1, padx=10, pady=10, sticky='nesw')
		end_date_entry.pack(side=LEFT, pady=10, padx=10)
		end_date_reset.pack(side=LEFT)

		# category filter
		category_group = ttk.LabelFrame(self, text='Categories to filter out (separated by comma)')
		category_entry = ttk.Entry(category_group, textvariable=self.categories, width=75)

		category_group.grid(row=3, column=0, padx=10, sticky='nesw', columnspan=2)
		category_entry.pack(side=LEFT, expand=True, pady=10, padx=10)

		# split file + max file size
		maxsize_group = ttk.LabelFrame(self, text='Max file size [0 = unlimited / don\'t split]')
		maxsize_entry = ttk.Entry(maxsize_group, textvariable=self.maxsize)
		maxsize_unit = ttk.Combobox(maxsize_group, textvariable=self.maxsize_unit, width=5)
		maxsize_unit['values'] = units

		maxsize_validator = self.register(self.validate_maxsize)
		maxsize_entry.config(validate='all', validatecommand=(maxsize_validator, '%d', '%P', '%V'))

		maxsize_group.grid(row=4, column=0, padx=10, pady=10, sticky='nesw')
		maxsize_entry.pack(side=LEFT, pady=10, padx=10)
		maxsize_unit.pack(side=LEFT)

		# run button
		self.run_button = ttk.Button(self, text='Run', command=lambda: self.run_filter())
		self.run_button.grid(row=4, column=1, padx=15, pady=10, sticky='nesw')

	def validate_float(self, inp):
		try:
			float(inp)
			return True
		except ValueError:
			return False

	def validate_int(self, inp):
		try:
			int(inp)
			return True
		except ValueError:
			return False

	def validate_maxsize(self, action, inp, reason):
		if action == 1:  # insertion
			return self.validate_int(inp)
		else:
			if inp == '' and reason == 'focusout':
				self.maxsize.set(0)
			elif inp == '' and reason == 'key':
				return True
			else:
				return self.validate_int(inp)

	def open_file(self):
		file = filedialog.askopenfilename(defaultextension='csv', filetypes=(("csv files", "*.csv"),))
		self.file.set(file)
		self.output_dir.set(os.path.dirname(file))

	def select_out_dir(self):
		directory = filedialog.askdirectory()
		self.output_dir.set(directory)

	def parse_bytes(self, size):
		units = {"B": 1, "KB": 10 ** 3, "MB": 10 ** 6, "GB": 10 ** 9, "TB": 10 ** 12}

		if size != 0:
			number, unit = [i for i in re.split(r'(\d+)', size) if i]
			return int(float(number) * units[unit])

		return 0

	def get_categories_list(self, categories_string):
		if categories_string == '':
			return []
		else:
			return [cat.strip() for cat in categories_string.split(',')]

	def validate_inputs(self):
		error = False
		error_messages = []

		if self.file.get() == '':
			error = True
			error_messages.append('Please select input file')

		if self.output_dir.get() == '':
			error = True
			error_messages.append('Please select output directory')

		if self.end_date.get() == '':
			error = True
			error_messages.append('Please enter end date')
		else:
			try:
				datetime.strptime(self.end_date.get(), '%Y-%m-%d')
			except ValueError:
				error_messages.append("Incorrect date format, should be YYYY-MM-DD")

		try:
			maxsize = self.maxsize.get()
			if maxsize == 0:
				self.maxsize.set(0)
		except:
			self.maxsize.set(0)

		return error, error_messages

	def run_filter(self):

		error, err_messages = self.validate_inputs()

		if error:
			self.controller.show_err_dialog(err_messages)
		else:
			self.controller.file = self.file.get()
			self.controller.output_dir = self.output_dir.get()
			self.controller.commission = float(self.commission.get())
			self.controller.end_date = self.end_date.get()
			self.controller.categories = self.get_categories_list(self.categories.get())
			self.controller.maxsize = self.parse_bytes("{}{}".format(int(self.maxsize.get()), self.maxsize_unit.get()))

			self.controller.show_frame(ProcessingScreen)
			self.controller.frames[ProcessingScreen].start()


class ProcessingScreen(Frame):
	"""
	Screen with filter progress indication
	"""

	def __init__(self, parent, controller):
		Frame.__init__(self, parent)
		self.controller = controller
		self.queue = queue.Queue()
		self.admitad_filter = None

		self.status = StringVar(value='...')

		status = ttk.Label(self, textvariable=self.status, font=LARGE_FONT, wraplength=480, justify=CENTER)
		status.pack(expand=True)

		self.progressbar = ttk.Progressbar(self, orient='horizontal')
		self.progressbar.pack(padx=10, pady=10, expand=True, fill=X)

	def start(self):
		self.controller.protocol("WM_DELETE_WINDOW", self.on_exit)
		print("File: '{}'".format(self.controller.file))
		print("Output dir: '{}'".format(self.controller.output_dir))
		print("Commission: {} %".format(self.controller.commission))
		print("Categories: {}".format(self.controller.categories))
		print("End date: {}".format(self.controller.end_date))
		print("Max size: {}B".format(self.controller.maxsize))

		self.admitad_filter = AliexpressFeedFilter(self.queue, self.controller.file, self.controller.output_dir,
		                                           self.controller.commission, self.controller.end_date,
		                                           self.controller.categories, self.controller.maxsize)
		self.admitad_filter.start()  # run filter on separate thread
		self.after(100, self.update_state)

	def update_state(self):
		try:
			state = self.queue.get(block=False)

			if state['message'] is not None:
				self.status.set(state['message'])
				self.after(100, self.update_state)

			if state['progress'] is not None:
				self.progressbar['value'] = state['progress']
				if state['progress'] == 100:
					print("Done: {} %".format(state['progress']))
					exit_gutton = ttk.Button(self, text='Exit', command=lambda: self.controller.destroy())
					exit_gutton.pack(side=BOTTOM, pady=10)
				self.after(100, self.update_state)

		except queue.Empty:
			self.after(100, self.update_state)
			return

	def on_exit(self):
		if self.controller.show_ask_dialog("Quit", "Do you want to quit?"):
			self.admitad_filter.exit = True
			self.controller.destroy()
