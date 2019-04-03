import csv
import os
import threading
from datetime import datetime


class AliexpressFeedFilter(threading.Thread):
	"""
	Class for filtering Aliexpress CSV feed from https://www.admitad.com/
	"""

	def __init__(self, queue, file, output_dir, commission, end_date, categories, maxsize):
		threading.Thread.__init__(self)
		self.queue = queue

		self.file = file
		self.output_dir = output_dir
		self.out_filename = 'filtered'
		self.commission = commission
		self.end_date = datetime.strptime(end_date, '%Y-%m-%d')
		self.categories = categories
		self.maxsize = maxsize

		self.__cols = {}

		self.queue.put({'progress': 0, 'message': 'Starting...'})
		self.exit = False

	def __get_cols(self, header):
		"""
		Get column names and its indexes from header (first row)

		:param header:  first row (list)
		"""
		self.__cols = {}
		for idx, col in enumerate(header):
			self.__cols[col] = idx

	def __calc_progress(self, total, current):
		"""
		Calculates current progress based on current row number vs total num of rows

		:param total:   total number of rows
		:param current:     current row number
		:return:    number from 0 to 100
		"""
		return current / total * 100

	def __write_row(self, writer, row):
		"""
		Writes row if given conditions are met

		:param writer:
		:param row:
		"""
		if str(row[self.__cols['endDate']]) == '':
			end_date = None
		else:
			end_date = datetime.strptime(str(row[self.__cols['endDate']]), '%Y-%m-%d')

		if row[self.__cols['commissionRate']] == '':
			commission = None
		else:
			commission = float(row[self.__cols['commissionRate']].rstrip("%"))

		category = str(row[self.__cols['categoryId']])

		row[self.__cols['image']] = str(row[self.__cols['image']]).encode('utf-8')
		row[self.__cols['name']] = str(row[self.__cols['name']]).encode('utf-8')
		row[self.__cols['title']] = str(row[self.__cols['title']]).encode('utf-8')
		row[self.__cols['url']] = str(row[self.__cols['url']]).encode('utf-8')

		if end_date is not None and commission is not None and commission >= self.commission and self.end_date <= end_date and category not in self.categories:
			writer.writerow(row)

	def __get_output_filepath(self, part):
		"""
		:param part:
		:return:    string full path to output file
		"""
		return "{}/{}-{}.csv".format(self.output_dir, self.out_filename, part)

	def __filter_csv(self):
		"""
		Opens input file, filters rows and writes them to the new file
		"""
		file_part = 1
		header = None
		output_name = self.__get_output_filepath(file_part)

		# open input (unfiltered) file for reading
		with open(self.file, 'r', encoding="utf8") as input_csv:
			self.queue.put({'progress': None, 'message': "Opening '{}' file for reading...".format(self.file)})
			reader = csv.reader(input_csv, delimiter=';', lineterminator='\n')

			# count total number of rows
			row_count = sum(1 for row in reader)
			print("Rows: {}".format(row_count))
			input_csv.seek(0)  # reset iterator

			reader = csv.reader(input_csv, delimiter=';', lineterminator='\n')

			try:
				output_csv = open(output_name, 'w', encoding="utf-8")
			except PermissionError:
				self.queue.put(
					{'progress': 100, 'message': "ERROR: Permission denied '{}'".format(os.path.basename(output_name))})
				return

			writer = csv.writer(output_csv, delimiter=';', lineterminator='\n')

			self.queue.put({'progress': None, 'message': "Writing to {}".format(self.__get_output_filepath(file_part))})
			for row in reader:

				if self.exit:
					output_csv.close()
					break

				# write header
				if reader.line_num == 1 and 'id' in row:
					header = row
					self.__get_cols(header)
					writer.writerow(header)
					continue

				# check maxsize
				if self.maxsize != 0:
					if output_csv.tell() >= self.maxsize:
						output_csv.close()
						self.queue.put({'progress': None,
						                'message': "Finished writing to {} (reached max size))".format(
							                self.__get_output_filepath(file_part))})
						file_part += 1
						output_csv = open("{}/{}-{}.csv".format(self.output_dir, self.out_filename, file_part), 'w')
						writer = csv.writer(output_csv, delimiter=';', lineterminator='\n')
						self.queue.put({'progress': None,
						                'message': "Writing to {}".format(self.__get_output_filepath(file_part))})
						writer.writerow(header)
						continue
					else:
						self.__write_row(writer, row)
				else:
					self.__write_row(writer, row)

				if reader.line_num % 1000 == 0:
					self.queue.put({'progress': self.__calc_progress(row_count, reader.line_num), 'message': None})

			self.queue.put(
				{'progress': None, 'message': "Finished writing to {}".format(self.__get_output_filepath(file_part))})
			output_csv.close()  # done, close file
			self.queue.put({'progress': 100, 'message': 'DONE'})

	def run(self):
		"""
		Run filtering in thread
		"""
		self.__filter_csv()
