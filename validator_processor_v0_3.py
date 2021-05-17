from PIL import Image, ImageChops
import os
import math
import hashlib
import exiftool
import csv
import shutil
import json
import simplejson
import copy
import subprocess


verbose = True

class Roots(object):
	def __init__(self):
		self.processed_root = None
		self.content_root = None
		self.fixed = None
		self.original = None
		self.processed_root = None
		self.originals_root = None
		self.summary_root = None

class Summary_Text(object):
	def __init__(self):
		self.textlines = []
		self.verbose = False

	def add_line(self, text):
		if type(text) != str:
			print ("Input not str:", text)
			quit()

		self.textlines.append(text)
		if self.verbose:
			print (text)

class Image_Data_Container(object):
	def __init__(self):
		self.original_filepath = None
		self.pil_basic_md = None
		self.format_md = None
		self.exiftool_md = None
		self.auto_made = False
		self.rmse_value = None
		self.rmse_same = None
		self.working_file_path = None
		self.item_root = None
		self.image_root = None
		self.jhove_report = None
		self.format = None
		self.filename = None
		self.file_identifer = None

	def make_package(self):
		parts = self.original_filepath.split(os.sep)
		self.filename = parts[-1]
		for p in parts:
			if p.lower().startswith("fl"):
				self.file_identifer = p
		if not self.file_identifer:
			if p.lower().startswith("ie"):
				self.file_identifer = p
		if not self.file_identifer:
			self.file_identifer = self.filename.replace(".", "|")

		export = 	{"generic":{"original_filepath":self.original_filepath,
								"jhove_report":self.jhove_report,
								"auto_made":self.auto_made,
								"working_file_path":self.working_file_path,
								"rmse_value":self.rmse_value,
								"rmse_same":self.rmse_same,
								"filename":self.filename,
								"file_identifer":self.file_identifer},

					"pil_basic_md":self.pil_basic_md,
					"format_md":self.format_md,
					"exiftool_md_raw":self.exiftool_md_raw, 
					"exiftool_md_cleaned":self.exiftool_md_cleaned}

		filename = "metadata.json"
		filepath = os.path.join(self.image_root, filename)

		with open(filepath, 'w') as outfile:
			simplejson.dump(str(export), outfile, indent=4, sort_keys=True)

class Comparisions(object):
	def __init__(self):
		self.deltas = [["source", "field", "A", "B"]]
		self.md_check_basic = None
		self.md_check_format = None
		self.md_check_exiftool = None
		self.md_check_jhove = None

	def reset(self):
		self.deltas = [["source", "field", "A", "B"]]
		self.md_check_basic = None
		self.md_check_format = None
		self.md_check_exiftool = None
		self.md_check_jhove = None
	
	def finalise(self):
		if len(self.deltas) > 1:
			with open(os.path.join(a.item_root, "differences.csv"), "w", encoding="utf8", newline="") as data:
				writer = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
				writer.writerows(self.deltas)


def do_jhove(f, dest):
	"""Calls JHOVE for both images and traps the results
	Will fail if jhove isn't on the host system - TODO (clean up jhove fail)"""
	module_lookup = {
				"AIFF":" -m aiff-hul ",
				"ASCII":" -m ascii-hul ",
				"BYTESTREAM":" -m bytestream=hul ",
				"GIF":" -m gif-hul ",
				"HTML":" -m html-hul ",
				"JPEG":" -m jpeg-hul ",
				"JPEG2000":" -m jpeg2000-hul ",
				"PDF":" -m pdf-hul ",
				"TIFF":" -m tiff-hul ",
				"UTF8":" -m utf8-hul ",
				"WAV":" -m wave-hul ",
				"XML":" -m xml-hul "}

	if a.format not in module_lookup:
		print ("format", a.format, "not in lookup for JHOVE - fix this here")
	module = module_lookup[a.format]
	cmd = f'''jhove {module} "{f}" > "{dest}"'''
	subprocess.call(cmd, shell=True)

def exiftool_check(verbose=verbose):
	"""calls the exiftool (through command line) for both images and traps the results
	Will fail if exiftool isn't on the host system - TODO (clean up exiftool fail)"""
	with exiftool.ExifTool() as et:
		md1 = a.exiftool_md = et.get_metadata(a.working_file_path)
		md2 = b.exiftool_md = et.get_metadata(b.working_file_path)

		a.exiftool_md_cleaned = a.exiftool_md_raw = copy.deepcopy(md1)
		b.exiftool_md_cleaned = b.exiftool_md_raw = copy.deepcopy(md2)

		for key in list(a.exiftool_md_cleaned.keys()):
			if key.startswith("File:"):
				del a.exiftool_md_cleaned[key]

		for key in list(b.exiftool_md_cleaned.keys()):
			if key.startswith("File:"):
				del b.exiftool_md_cleaned[key]

		del a.exiftool_md_cleaned["SourceFile"]
		del b.exiftool_md_cleaned["SourceFile"]
		del a.exiftool_md_cleaned['ExifTool:ExifToolVersion']
		del b.exiftool_md_cleaned['ExifTool:ExifToolVersion']
		
		try:
			del a.exiftool_md_cleaned['EXIF:ThumbnailOffset']
			del b.exiftool_md_cleaned['EXIF:ThumbnailOffset']
		except KeyError:
			pass

		try:
			del a.exiftool_md_cleaned['JFIF:ThumbnailTIFF']
			del b.exiftool_md_cleaned['JFIF:ThumbnailTIFF']
		except KeyError:
			pass


		try:
			del a.exiftool_md_cleaned['EXIF:StripOffsets']
			del b.exiftool_md_cleaned['EXIF:StripOffsets']
		except KeyError:
			pass


		if verbose:
			used_keys = []

			a.exiftool_md_cleaned = {k: a.exiftool_md_cleaned [k] for k in sorted(a.exiftool_md_cleaned )}
			b.exiftool_md_cleaned = {k: b.exiftool_md_cleaned [k] for k in sorted(b.exiftool_md_cleaned )}

			for k, v in a.exiftool_md_cleaned.items():

				#### empty data item normaliser ####
				if k in a.exiftool_md_cleaned:
					if a.exiftool_md_cleaned[k] == "":
						a.exiftool_md_cleaned[k] = "--Empty--"
					if a.exiftool_md_cleaned[k] == []:
						a.exiftool_md_cleaned[k] = "--Empty--"
					if a.exiftool_md_cleaned[k] == "none":
						a.exiftool_md_cleaned[k] = "--Empty--"
				else:
					a.exiftool_md_cleaned[k] = "--Empty--"


				if k in b.exiftool_md_cleaned:
					if b.exiftool_md_cleaned[k] == "":
						b.exiftool_md_cleaned[k] = "--Empty--"
					if b.exiftool_md_cleaned[k] == []:
						b.exiftool_md_cleaned[k] = "--Empty--"
					if b.exiftool_md_cleaned[k] == "none":
						b.exiftool_md_cleaned[k] = "--Empty--"
				else:
					b.exiftool_md_cleaned[k] = "--Empty--"

				if k not in used_keys:
					used_keys.append(k)
				if k not in b.exiftool_md_cleaned:
					summary.add_line(f"Exiftool - {k} mismatch: \n\tA: {a.exiftool_md_cleaned[k]} \n\tB: --Empty--")
					master.deltas.append(["Exiftool ", k, a.exiftool_md_cleaned[k], None])
				elif a.exiftool_md_cleaned[k] != b.exiftool_md_cleaned[k]:
					summary.add_line( f"Exiftool - {k} mismatch: \n\tA: {a.exiftool_md_cleaned[k]} \n\tB: {b.exiftool_md_cleaned[k]}")
					master.deltas.append(["Exiftool ", k, a.exiftool_md_cleaned[k], b.exiftool_md_cleaned[k]])


			for k, v in b.exiftool_md_cleaned.items():
				if k not in used_keys:
					if k not in a.exiftool_md_cleaned:
						summary.add_line(f"Exiftool - {k} mismatch: \n\tA: --Empty--  \n\tB: {b.exiftool_md_cleaned[k]}")
						master.deltas.append(["Exiftool ", k, None, b.exiftool_md_cleaned[k]])

					elif a.exiftool_md_cleaned[k] != b.exiftool_md_cleaned[k]:
						summary.add_line(f"Exiftool - {k} mismatch: \n\tA: {a.exiftool_md_cleaned[k]} \n\tB: {b.exiftool_md_cleaned[k]}")
						master.deltas.append(["Exiftool ", k, a.exiftool_md_cleaned[k], b.exiftool_md_cleaned[k]])


		return a.exiftool_md_cleaned == b.exiftool_md_cleaned

def jhove_check():
	with open(b.jhove_report) as data:
		text = data.read()
		if "Status: Well-Formed and valid" in text:
			return True
		else:
			return False

def use_exiftool_to_make_htmldump():

	a.htmldump_outfile = os.path.join(a.item_root, "ORIGINAL", "exiftool_htmldump.html")
	b.htmldump_outfile = os.path.join(a.item_root, "NEW", "exiftool_htmldump.html")

	cmd = f'''exiftool -htmldump "{a.working_file_path}" > "{a.htmldump_outfile}"'''
	subprocess.call(cmd, shell=True)
	cmd = f'''exiftool -htmldump "{b.working_file_path}" > "{b.htmldump_outfile}"'''
	subprocess.call(cmd, shell=True)

def use_exiftool_to_set_exif():
	"""
	export
	# exiftool -json "c:/Users/Phil/Images" > "c:/Users/Phil/test.json"


	import 
	exiftool -json=r"c:/Users/Phil/test.json" "c:/Users/Phil/Images"


	export all... 

	exiftool -ee3 -U -G3:1 -api requestall=3 -api largefilesupport
	# """
	# my_temp_json_file = r"e:\\temp_json.json"
	# cmd = f'''exiftool -u -U  -ee3 -U -G3:1 -api requestall=3 -api largefilesupport -json "{a.working_file_path}" > "{my_temp_json_file}"'''
	# # cmd = f'''exiftool -u -U -json "{a.working_file_path}" > "{my_temp_json_file}"'''
	# subprocess.call(cmd, shell=True)

	# with open(my_temp_json_file) as json_file:
	# 	data = json.load(json_file)
	# 	data[0]['SourceFile'] = b.working_file_path.lower()
	# 	data[0]['Directory'] = b.image_root.lower()

	# with open(my_temp_json_file, 'w') as outfile:
	# 	outfile.write(simplejson.dumps(data, indent=4, sort_keys=True))
	


	# cmd = f'''exiftool -q -all:all -xmp -json="{my_temp_json_file}" "{b.working_file_path}"'''
	# subprocess.call(cmd, shell=True)

	# if os.path.exists(my_temp_json_file):
	# 	os.remove(my_temp_json_file)

	cmd   = f'exiftool.exe -ext TIF -all:all -xmp  -TagsFromFile {a.working_file_path} {b.working_file_path} '

def get_exif_from_source_file():
	my_temp_json_file = r"e:\\temp_json.json"

	# cmd = f'''exiftool -u -U  -ee3 -U -G3:1 -api requestall=3 -api largefilesupport -json "{a.working_file_path}" > "{my_temp_json_file}"'''
	cmd = f'''exiftool -u -U  -json "{a.working_file_path}" > "{my_temp_json_file}"'''
	subprocess.call(cmd, shell=True)

	with open(my_temp_json_file) as f:

		my_exif = json.load(f)

	if os.path.exists(my_temp_json_file):
		os.remove(my_temp_json_file)

	return my_exif

def make_difference_images(im1, im2):
	"""If there is a none zero RMSe value, a difference image (and its inverse) is created.
	This is useful as visual indicator for what the actaul difference is. 
	THe biatonal image are a thresholded representation of the diff, with the theshold set at max_level - 1, 2, 3, 4 and 5 respectively
	This is useful to see where the diff is in real terms - consider it an exaggeration of the diff we can see.  
	"""
	diff_folder = os.path.join(a.item_root, "difference_images")
	if not os.path.exists(diff_folder):
		os.makedirs(diff_folder)

	difference = ImageChops.difference(im1, im2)
	difference = ImageChops.invert(difference)

	difference.save(os.path.join(diff_folder, "diff.png"))
	difference_inverted = ImageChops.invert(difference)
	difference_inverted.save(os.path.join(diff_folder, "diff_inverted.png"))
	
	thresh = 254
	fn = lambda x : 255 if x > thresh else 0
	diff_1 = difference.convert('L').point(fn, mode='1')
	diff_1.save(os.path.join(diff_folder, "bilevel_001.png"))

	thresh = 253
	fn = lambda x : 255 if x > thresh else 0
	diff_2 = difference.convert('L').point(fn, mode='1')
	diff_2.save(os.path.join(diff_folder, "bilevel_002.png"))

	thresh = 252
	fn = lambda x : 255 if x > thresh else 0
	diff_3 = difference.convert('L').point(fn, mode='1')
	diff_3.save(os.path.join(diff_folder, "bilevel_003.png"))

	thresh = 251
	fn = lambda x : 255 if x > thresh else 0
	diff_4 = difference.convert('L').point(fn, mode='1')
	diff_4.save(os.path.join(diff_folder, "bilevel_004.png"))

	thresh = 250
	fn = lambda x : 255 if x > thresh else 0
	diff_5 = difference.convert('L').point(fn, mode='1')
	diff_5.save(os.path.join(diff_folder, "bilevel_005.png"))

def image_payload_identical(im1, im2, verbose=verbose, make_diff=True):
	rms_value = rmsdiff(im1, im2)
	a.rms_value = rms_value
	b.rms_value = rms_value
	if verbose == True and rms_value!= 0.0:
		print ("RMS:", rms_value)
		summary.textlines.append(["RMS:", rms_value])
	if rms_value == 0:
		a.rmse_same = b.rmse_same = True
		return True
	else:
		a.rmse_same = b.rmse_same = False
		make_difference_images(im1, im2)
		master.deltas.append(["RMSE check", "RMSE", rms_value, rms_value])
		return False

def metadata_payload_identical(im1, im2):
	"""selector for what checks to do. uses image format to send image to correct parser
	add new parsers here
	returns only True or False"""
	md_diff = md_check_basic(im1, im2)
	a.format = im1.format
	b.format = im2.format

	if im1.format != im2.format:
		return md_diff

	else:
		if im1.format == "GIF":
			fmt_diff = gif_md_check(im1, im2)
			if verbose:
				print ("GIF checks completed")
			return all([fmt_diff, md_diff])

		elif im1.format == "JPEG":
			fmt_diff = jpeg_md_check(im1, im2)
			if verbose:
				print ("JPEG checks completed")
			return all([fmt_diff, md_diff])

		elif im1.format == "TIFF":
			fmt_diff = tiff_md_check(im1, im2)
			if verbose:
				print ("TIFF checks completed")
			return all([fmt_diff, md_diff])

		else:
			print ("no parser for:", im1.format)
			return md_diff

def handle_pil_exif_block(im1, im2):
	for tag, value in im1._getexif().items():
		print (tag, value)
	print (im1._getexif())
	print (im2._getexif())

def tiff_md_check(im1, im2, verbose=verbose):
	supported_keys =  ['compression', 'dpi', 'icc_profile', 'resolution']

	my_keys =  list(im1.info.keys())
	for key in my_keys:
		if key not in supported_keys:
			print (f"The key '{key}' in format {a.format} is not included. Add to {a.format.lower()}_md_check() and continue")
			quit()

	try:
		im1_dpi  = im1.info['dpi']
	except KeyError:
		im1_dpi = None

	try:
		im2_dpi  = im2.info['dpi']
	except KeyError:
		im2_dpi = None


	try:
		im1_compression  = im1.info['compression'].strip()
	except KeyError:
		im1_compression = None

	try:
		im2_compression  = im2.info['compression'].strip()
	except KeyError:
		im2_compression = None

	try:
		im1_icc_profile  = im1.info['icc_profile'].strip()
	except KeyError:
		im1_icc_profile = None

	try:
		im2_icc_profile  = im2.info['icc_profile'].strip()
	except KeyError:
		im2_icc_profile = None

	try:
		im1_resolution  = im1.info['resolution']
	except KeyError:
		im1_resolution = None

	try:
		im2_resolution  = im2.info['resolution']
	except KeyError:
		im2_resolution = None



	dpi = im1_dpi == im2_dpi
	compression = im1_compression == im2_compression
	icc_profile = im1_icc_profile == im2_icc_profile
	resolution = im1_resolution == im2_resolution

	if not dpi:
		master.deltas.append(["PIL TIFF", "dpi", im1_dpi, im2_dpi])
		if verbose:
			line = f"PIL TIFF - dpi mismatch: \n\tA: {im1_dpi}\n\tB: {im2_dpi}"
			print (line)
			summary.textlines.append(line)

	if not dpi:
		master.deltas.append(["PIL TIFF", "icc_profile", im1_icc_profile, im2_icc_profile])
		if verbose:
			line = f"PIL TIFF - icc_profile mismatch: \n\tA: {im1_icc_profile}\n\tB: {im2_icc_profile}"
			print (line)
			summary.textlines.append(line)

	if not compression:
		master.deltas.append(["PIL TIFF", "compression", im1_compression, im2_compression])
		if verbose:
			line = f"PIL TIFF - compression mismatch: \n\tA: {im1_compression}\n\tB: {im2_compression}"
			print (line)
			summary.textlines.append(line)

	if not compression:
		master.deltas.append(["PIL TIFF", "resolution", im1_resolution, im2_resolution])
		if verbose:
			line = f"PIL TIFF - resolution mismatch: \n\tA: {im1_resolution}\n\tB: {im2_resolution}"
			print (line)
			summary.textlines.append(line)

	a.format_md = {"format":"TIFF",
					"dpi":im1_dpi,
					"compression":im1_compression,
					'icc_profile':im1_icc_profile,
					'resolution':im1_resolution}

	b.format_md = {"format":"TIFF",
					"dpi":im2_dpi,
					"compression":im2_compression,
					'icc_profile':im2_icc_profile,
					'resolution':im2_resolution}	


	return all([dpi, compression, icc_profile, resolution, True])

def gif_md_check(im1, im2, verbose=verbose):
	"""checks that all GIF specific md is identica between 2 image objects"""

	supported_keys =  ['version', 'background', 'transparency', 'duration', 'extension',  ]
	my_keys =  list(im1.info.keys())
	for key in my_keys:
		if key not in supported_keys:
			print (f"The key '{key}' in format {a.format} is not included. Add to {a.format.lower()}_md_check() and continue")
			quit()


	try:
		im1_version  = im1.info['version']
	except KeyError:
		im1_version = None

	try:
		im1_background  = im1.info['background']
	except KeyError:
		im1_background = None

	try:
		im1_transparency  = im1.info['transparency']
	except KeyError:
		im1_transparency = None

	try:
		im1_duration = im1.info['duration']
	except KeyError:
		im1_duration = None

	try:
		im1_extension = im1.info['extension']
	except KeyError:
		im1_extension = None

	try:
		im2_version = im2.info['version']
	except KeyError:
		im1_version = None

	try:
		im2_background  = im2.info['background']
	except KeyError:
		im2_background = None

	try:
		im2_transparency  = im2.info['transparency']
	except KeyError:
		im2_transparency = None

	try:
		im2_duration = im2.info['duration']
	except KeyError:
		im2_duration = None

	try:
		im2_extension = im2.info['extension']
	except KeyError:
		im2_extension = None

	if im1_version != im2_version:
		master.deltas.append(["PIL GIF", "version", im1_version, im2_version])
		if verbose:
			line = f"PIL GIF - version mismatch: \n\tA: {im1_version}\n\tB: {im2_version}"
			print (line)
			summary.textlines.append(line)

	if im1_background != im2_background:
		master.deltas.append(["PIL GIF", "background", im1_background, im2_background])
		if verbose:
			line = f"PIL GIF - background mismatch: \n\tA: {im1_background}\n\tB: {im2_background}"
			print (line)
			summary.textlines.append(line)

	if im1_transparency != im2_transparency:
		master.deltas.append(["PIL GIF ", "transparency", im1_transparency, im2_transparency])
		if verbose:
			line = f"PIL GIF - transparency mismatch: \n\tA: {im1_transparency}\n\tB: {im2_transparency}"
			print (line)
			summary.textlines.append(line)

	if im1_duration != im2_duration:
		master.deltas.append(["PIL GIF", "duration", im1_duration, im2_duration])
		if verbose:
			line = f"PIL GIF - duration mismatch: \n\tA: {im1_duration}\n\tB: {im2_duration}"
			print (line)
			summary.textlines.append(line)

	if im1_extension != im2_extension:
		master.deltas.append(["PIL GIF", "extension", im1_extension, im2_extension])
		if verbose:
			line = f"PIL GIF - extension mismatch: \n\tA: {im1_extension}\n\tB: {im2_extension}"
			print (line)
			summary.textlines.append(line)

	version = im1_version == im2_version
	background = im1_background == im2_background
	transparency = im1_transparency == im2_transparency
	duration = im1_duration == im2_duration
	extension = im1_extension == im2_extension

	a.format_md = {"format":"GIF",
					"version":im1_version,
					"background":im1_background,
					"transparency":im1_transparency,
					"duration":im1_duration,
					"extension":im1_extension}

	b.format_md = {"format":"GIF",
					"version":im2_version,
					"background":im2_background,
					"transparency":im2_transparency,
					"duration":im2_duration,
					"extension":im2_extension}

	return all([version, background, transparency, duration, extension, True])

def jpeg_md_check(im1, im2, verbose=verbose):

	supported_keys =  ['dpi', 'jfif', 'jfif_version', 'jfif_unit', 'jfif_density', 'icc_profile', 'exif']
	my_keys =  list(im1.info.keys())
	for key in my_keys:
		if key not in supported_keys:
			print (f"The key '{key}' in format {a.format} is not included. Add to {a.format.lower()}_md_check() and continue")
			quit()

	try:
		im1_dpi  = im1.info['dpi']
	except KeyError:
		im1_dpi = None

	try:
		im2_dpi  = im2.info['dpi']
	except KeyError:
		im2_dpi = None


	try:
		im1_jfif = im1.info['jfif']
	except KeyError:
		im1_jfif = None

	try:
		im2_jfif = im2.info['jfif']
	except KeyError:
		im2_jfif = None


	try:
		im1_jfif_version = im1.info['jfif_version']
	except KeyError:
		im1_jfif_version = None

	try:
		im2_jfif_version = im2.info['jfif_version']
	except KeyError:
		im2_jfif_version = None


	try:
		im1_jfif_unit = im1.info['jfif_unit']
	except KeyError:
		im1_jfif_unit = None

	try:
		im2_jfif_unit = im2.info['jfif_unit']
	except KeyError:
		im2_jfif_unit = None


	try:
		im1_jfif_density = im1.info['jfif_density']
	except KeyError:
		im1_jfif_density = None

	try:
		im2_jfif_density = im2.info['jfif_density']
	except KeyError:
		im2_jfif_density = None


	try:
		im1_icc_profile = im1.info['icc_profile']
	except KeyError:
		im1_icc_profile = None

	try:
		im2_icc_profile = im2.info['icc_profile']
	except KeyError:
		im2_icc_profile = None


	try:
		im1_exif = im1.info['exif']
	except KeyError:
		im1_exif = None

	try:
		im2_exif = im2.info['exif']
	except KeyError:
		im2_exif = None

	
	if im1_exif != im2_exif:
		handle_pil_exif_block(im1, im2)
		master.deltas.append(["PIL JPEG", "EXIF", "", ""])
		if verbose:
			line = f"PIL JPEG - EXIF mismatch"
			print (line)
			summary.textlines.append(line)

	if im1_dpi != im2_dpi:
		master.deltas.append(["PIL JPEG", "DPI", im1_dpi, im2_dpi])
		if verbose:
			line = f"PIL JPEG - dpi mismatch: \n\tA: {im1_dpi}\n\tB: {im2_dpi}"
			print (line)
			summary.textlines.append(line)

	if im1_jfif != im2_jfif:
		master.deltas.append(["PIL JPEG", "JFIF", im1_jfif, im2_jfif])
		if verbose:
			line = f"PIL JPEG - jfif mismatch: \n\tA: {im1_jfif}\n\tB: {im2_jfif}"
			print (line)
			summary.textlines.append(line)

	if im1_jfif_version != im2_jfif_version:
		master.deltas.append(["PIL JPEG", "JFIF version", im1_jfif_version, im2_jfif_version])
		if verbose:
			line = f"PIL JPEG - JFIF version mismatch: \n\tA: {im1_jfif_version}\n\tB: {im2_jfif_version}"
			print (line)
			summary.textlines.append(line)

	if im1_jfif_unit != im2_jfif_unit:
		master.deltas.append(["PIL JPEG", "JFIF unit", im1_jfif_unit, im2_jfif_unit])
		if verbose:
			line = f"PIL JPEG - JFIF unit mismatch: \n\tA: {im1_jfif_unit}\n\tB: {im2_jfif_unit}"
			print (line)
			summary.textlines.append(line)

	if im1_jfif_density != im2_jfif_density:
		master.deltas.append(["PIL JPEG", "JFIF density", im1_jfif_density, im2_jfif_density])
		if verbose:
			line = f"PIL JPEG - JFIF density mismatch: \n\tA: {im1_jfif_density}\n\tB: {im2_jfif_density}"
			print (line)
			summary.textlines.append(line)	

	if im1_icc_profile != im2_icc_profile:
		master.deltas.append(["PIL JPEG", "icc profile", im1_icc_profile, im2_icc_profile])
		if verbose:
			line = f"PIL JPEG -  ICC profile mismatch: \n\tA: {im1_icc_profile}\n\tB: {im2_icc_profile}"
			print (line)
			summary.textlines.append(line)

	exif_block = im1_exif == im2_exif
	dpi = im1_dpi == im2_dpi
	jfif = im1_jfif == im2_jfif
	jfif_version = im1_jfif_version == im2_jfif_version
	jfif_density = im1_jfif_density == im2_jfif_density
	jfif_unit = im1_jfif_unit == im2_jfif_unit
	icc_colour_profile = im1_icc_profile == im2_icc_profile

	a.format_md = {"format":"JPEG",
					"exif_block":im1_exif,
					"dpi":im1_dpi,
					"jfif":im1_jfif,
					"jfif_version":im1_jfif_version,
					"jfif_density":im1_jfif_density,
					"jfif_unit":im1_jfif_unit,
					"icc_colour_profile":im1_icc_profile}

	b.format_md = {"format":"JPEG",
					"exif_block":im2_exif,
					"dpi":im2_dpi,
					"jfif":im2_jfif,
					"jfif_version":im2_jfif_version,
					"jfif_density":im2_jfif_density,
					"jfif_unit":im2_jfif_unit,
					"icc_colour_profile":im2_icc_profile}


	return all([exif_block, dpi, jfif, jfif_version, jfif_density, jfif_unit, icc_colour_profile, True])

def md_check_basic(im1, im2, verbose=verbose):
	"""Returns the most basic image checks
	Size as tuple (W, H), palette as a list, band names
	Returns true if A == B for all fields, false is any not""" 
	im1_size = im1.size	
	im2_size = im2.size
	im1_palette = im1.getpalette()
	im2_palette = im2.getpalette()
	im1_bands = im1.getbands()
	im2_bands = im2.getbands()

	a.pil_basic_md = {"size":im1_size, "palette":im1_palette, "bands":im1_bands}
	b.pil_basic_md = {"size":im2_size, "palette":im2_palette, "bands":im2_bands}

	
	if not im1_size == im2_size:
		master.deltas.append(["PIL basic", "size", im1_size, im2_size])
		if verbose:
			print (f"size mismatch: \nA: {im1_size}\nB: {im2_size}")
	if not im1_palette == im2_palette:
		master.deltas.append(["PIL basic", "palette", im1_palette, im2_palette])
		if verbose:
			print (f"palette mismatch: \nA: {im1_palette}\nB: {im2_palette}")
	if not  im1_bands == im2_bands:
		master.deltas.append(["PIL basic", "bands", im1_bands, im2_bands])
		if verbose:
			print (f"bands mismatch: \nA: {im1_bands}\nB: { im2_bands}")

	size = im1_size == im2_size
	palette = im1_palette == im2_palette
	bands = im1_bands == im2_bands

	return all([size, palette,  bands, True])

def rmsdiff(im1, im2):
	"""returns rmse (float) between two Image items"""
	diff = ImageChops.difference(im1, im2)
	h = diff.histogram()
	sq = (value*((idx%256)**2) for idx, value in enumerate(h))
	sum_of_squares = sum(sq)
	rms = math.sqrt(sum_of_squares/float(im1.size[0] * im1.size[1]))
	return rms

def md5(fname):
	"""returns md5 digest of file"""
	hash_md5 = hashlib.md5()
	with open(fname, "rb") as f:
		for chunk in iter(lambda: f.read(4096), b""):
			hash_md5.update(chunk)
	return hash_md5.hexdigest()

def make_new_image(im1, show_image=False):
	"""handler for the new image maker
	refer to https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html for save instructions"""
	file_format = im1.format
	if file_format == "GIF":
		im1.save(b.working_file_path)
		if verbose:
			line = f"New GIF file made {b.working_file_path}"
			print (line)
			summary.textlines.append(line)

		if show_image:
			im2 = Image.open(b.working_file_path)
			im2.show()

	elif file_format == "JPEG":
		im1.save(b.working_file_path, quality=100, subsampling="keep", icc_profile=im1.info.get('icc_profile'), exif=im1.info['exif'])
		if verbose:
			line = "New JPEG file made {b.working_file_path}"
			print (line)
			summary.textlines.append(line)

		if show_image:
			im2 = Image.open(b.working_file_path)
			im2.show()

	elif file_format == "TIFF":
		my_exif  =  get_exif_from_source_file()

		try:
			im1.save(b.working_file_path, quality=100, compression=im1.info['compression'], exif=im1.getexif())
		except:
			print ("TIFF copy via PILLOW hit tuple error... reverting to shutil.copy2")
			shutil.copy2(a.working_file_path, b.working_file_path)

		use_exiftool_to_set_exif()
		
		if verbose:
			line = f"New TIFF file made {b.working_file_path}"
			print (line)
			summary.textlines.append(line)
		if show_image:
			im2 = Image.open(b.working_file_path)
			im2.show()

	else:
		print (f"No reprover included for {file_format}")
		print ("Add to function: make_new_image() to proceed")
		quit()

	b.auto_made = True

def set_up_files_package(init_src, dest=False):
	source_folder, a_fname = init_src.rsplit(os.sep, 1)
	folder_parts = source_folder.split(os.sep)
	file_key = a_fname.replace(".", "_")
	local_root = os.path.join(roots.processed_root, folder_parts[-1]) 
	my_root = a.item_root = b.item_root = local_root+os.sep+file_key
	working_dest_root = b.image_root = os.path.join(my_root, "NEW")
	working_src_root =  a.image_root = os.path.join(my_root, "ORIGINAL")

	if flush:
		if os.path.exists(my_root):
			try:
				shutil.rmtree(my_root)
			except FileNotFoundError:
				pass

	a.original_filepath = init_src

	if dest:
		b.original_filepath = dest
		source_folder, b_fname = dest.rsplit(os.sep, 1)
	else:
		b.original_filepath = None


	if not os.path.exists(working_src_root):
		os.makedirs(working_src_root)

	if not os.path.exists(working_dest_root):
		os.makedirs(working_dest_root)
	
	shutil.copy2(init_src, working_src_root)
	if dest:
		shutil.copy2(dest, working_dest_root)

	a.working_file_path = os.path.join(my_root, "ORIGINAL", a_fname)
	b.working_file_path = os.path.join(my_root, "NEW" , b_fname)

def process_image(src, dest=False):
	set_up_files_package(src, dest=dest)
	im1 = Image.open(a.working_file_path)
	summary.add_line(f"Working on {src}")
	if not os.path.exists(b.working_file_path) or dest==False:
		make_new_image(im1)
	a.jhove_report = os.path.join(a.image_root, "jhove.txt")
	b.jhove_report = os.path.join(b.image_root, "jhove.txt")

	im2 = Image.open(b.working_file_path)
	master.rms_check = image_payload_identical(im1, im2)
	line = f"RMS check: {master.rms_check}"
	print (line)
	summary.textlines.append(line)
	
	master.md_check_basic = metadata_payload_identical(im1, im2)
	line = f"Tech data check: {master.md_check_basic}" 
	print (line)
	summary.textlines.append(line)

	master.md_check_exiftool = exiftool_check()
	line = f"Exiftool check: {master.md_check_exiftool}"
	print (line)
	summary.textlines.append(line)

	do_jhove(a.working_file_path, a.jhove_report)
	do_jhove(b.working_file_path, b.jhove_report)
	
	master.md_check_jhove = jhove_check()
	line = f"JHOVE check: {master.md_check_jhove}"
	print (line)
	summary.textlines.append(line)
	print ()

	logger()
	a.make_package()
	b.make_package()
	do_jhove(a.working_file_path, a.jhove_report)
	do_jhove(b.working_file_path, b.jhove_report)

	use_exiftool_to_make_htmldump()
	master.finalise()
	

	if all([master.rms_check, master.md_check_basic , master.md_check_exiftool, True]):
		with open(os.path.join(a.item_root, "OK"), "wb") as data:
			pass
	else:
		with open(os.path.join(a.item_root, "DELTAS"), "wb") as data:
			pass

def logger(filename="log.csv"):
	lines = [["MD Block", "Field", "Same?","A" ,"B"]]
	lines.append(["Generic","filepath","",a.working_file_path, b.working_file_path])
	lines.append(["Generic","auto_made","","N/A", b.auto_made])
	lines.append(["Generic","rmse",a.rmse_same,"N/A", b.rms_value])
	lines.append(["Generic","jhove_report","", a.jhove_report, b.jhove_report])
	lines.append(["","","",""])

	##### PIL basic 
	for key in list(a.pil_basic_md.keys()):
		lines.append(["PIL basic MD", key, a.pil_basic_md[key]==b.pil_basic_md[key],a.pil_basic_md[key], b.pil_basic_md[key]])
	lines.append(["","","",""])

	### format specific md
	if a.format_md == None:
		print (f"MD extraction missing data. Make sure theres a format parser for {a.format}")
		quit()
	all_keys = list(set(list(a.format_md.keys())+list(b.format_md.keys())))
	
	for key in all_keys:
		if key not in a.format_md:
			a.format_md[key] = "N/A"
		if key not in b.format_md:
			b.format_md[key] = "N/A"

		if a.format_md[key] in ["", None]:
			a.format_md[key] = "None"
		if b.format_md[key] in ["", None]:
			b.format_md[key] = "None"
		lines.append(["Format MD", key, a.format_md[key]==b.format_md[key], a.format_md[key], b.format_md[key]])
	lines.append(["","","",""])

	#### exiftool md
	all_keys = list(set(list(a.exiftool_md.keys())+list(b.exiftool_md.keys())))

	for key in all_keys:
		if key not in a.exiftool_md:
			a.exiftool_md[key] = "N/A"
		if key not in b.exiftool_md:
			b.exiftool_md[key] = "N/A"

		if a.exiftool_md[key] in ["", None]:
			a.exiftool_md[key] = "None"
		if b.exiftool_md[key] in ["", None]:
			b.exiftool_md[key] = "None"
		lines.append(["Exiftool MD", key, a.exiftool_md[key]==b.exiftool_md[key], a.exiftool_md[key], b.exiftool_md[key]])
	lines.append(["","","",""])

	filename = os.path.join(a.item_root, filename)

	with open(filename, "w", encoding="utf8",newline='' ) as data:
		 writer = csv.writer(data, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
		 writer.writerows(lines)

def make_list_of_files_from_set_folder():
	my_files = []
	my_folder = roots.originals_root
	line = f"Getting files from: {my_folder}"
	print (line)
	# summary.textlines.append(line)

	for folder in [os.path.join(my_folder, x) for x in os.listdir(my_folder)]:
		for f in [os.path.join(my_folder, folder, x) for x in os.listdir(folder)]:
			my_files.append(f) 
	
	my_files = [x.replace("/", os.sep) for x in my_files]

	line = f"Added {len(my_files)} files"
	print (line)
	# summary.textlines.append(line)
	# summary.textlines.append("\n")
	
	return my_files 

def process_summaries():
	print (summaries)
	# quit()

def process_set():
	roots.processed_root = os.path.join(roots.final_root, set_id)
	roots.processed_root = roots.processed_root.replace("/", os.sep)
	roots.originals_root =f"{roots.content_root}/{set_id}/original".replace("/", os.sep)
	roots.fixed_root = 	f"{roots.content_root}/{set_id}/fixed".replace("/", os.sep)
	files = make_list_of_files_from_set_folder()

	summaries = []

	for i, init_src in enumerate(files):
		master.reset()
		summary.textlines = []
		dest_src = init_src.replace(roots.originals_root, roots.fixed_root) 
		
		line = f"{i+1}/{len(files)} Out-file found OK: {os.path.exists(dest_src)} - {dest_src}"
		print (line)
		summary.textlines.append(line)
		if i < starts_at:
			line = f"Skipping {i} - done"
			print (line)
			summary.textlines.append(line)
		else:
			process_image(init_src, dest=dest_src)
			line = f"file #{i+1} completed\n\n_______________\n"
			print (line)
			summary.textlines.append(line)
			summaries.append([a.file_identifer, master.md_check_basic, master.md_check_exiftool, master.md_check_format, master.md_check_jhove, master.rms_check]) 




	line = "\n#### Summary of checks for set ####\n"
	print (line)
	summary.textlines.append(line)
	line = "ID\t\t\t\tMD basic\tExiftool\tFormat\t\tJhove\t\tRMSe"
	print (line)
	summary.textlines.append(line)
	roots.summary_root, __ = roots.processed_root.rsplit(os.sep, 1)
	roots.summary_root = os.path.join(roots.summary_root, "summary_files")

	for item in summaries:
		line = f"{item[0]}\t\t{item[1]}\t\t{item[2]}\t\t{item[3]}\t\t{item[4]}\t\t{item[5]}"
		print (line)
		line = f"{item[0]}\t{item[1]}\t\t{item[2]}\t\t{item[3]}\t\t{item[4]}\t\t{item[5]}"
		summary.textlines.append(line)

	summary_file = os.path.join(roots.summary_root,f"{set_id}.txt")
	with open(summary_file, "w", encoding="utf8") as data:
		lines = "\n".join(summary.textlines)
		data.write(lines)


a = Image_Data_Container()
b = Image_Data_Container()

roots = Roots()
summary = Summary_Text()
master = Comparisions()
flush = True
verbose = False
starts_at = 0

set_id = "fmt_353_12"
roots.final_root = "E:/completed_cleans"
roots.content_root = r"E:/"


process_set()
