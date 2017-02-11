import glob
import re
import os
import json
import sys

# firstWordDiscardList = ['Message-ID:', 'Date:','From:','To:', 'Cc:', 'Subject:', 'Bcc:','Mime-Version:',
# 'Content-Type:','Content-Transfer-Encoding:','X-From:', 'X-To:', 'X-cc:','X-bcc:','X-Folder:', 'X-Origin:', 'X-FileName:','>','?']

ignoreLineList = ['--Original Message--','-- Original Message --','From:','Sent:','To:', 'Subject:', '-- Forwarded by']

attachRegEx1 = re.compile('- .*\.(zip|doc|pdf|gif|jpg|jpeg|htm|html)')
attachRegEx2 = re.compile('<<.*\.(zip|doc|pdf|gif|jpg|jpeg|htm|html)>>')
attachDetector = [attachRegEx1, attachRegEx2]

threadStartRegEx1 = re.compile('--\s*Original Message\s*--')
# threadStartRegEx2 = re.compile('-- Original Message --')
threadStartRegEx3 = re.compile('-- Forwarded by')
threadStartRegEx4 = re.compile('[oO]n \d{2}\/\d{2}\/\d{4} \d{2}:\d{2}:\d{2} (AM|PM)$')
threadStartDetector = [threadStartRegEx1,threadStartRegEx3,threadStartRegEx4]

# checks for header pattern, lines starting like this - From: blah
headerRegEx = re.compile('^([\w-]*:)')

# we will remove the lines of these characters, if the are in prefix before parsing them
fixLineStart = '>' # greaterthan,  space or question mark

# ../../../enron-experiments/enron-data/maildir/taylor-m/all_documents/46.
folderpathregexpr = re.compile('maildir\/(\w*-\w)\/(\w*)\/(\d*)\.$')

tokenReplace = {'=20':' ','=01,':'\'', '=02=05':'. ', '=02=07':'\''}

lineEndReplace = {'=':''}

# also ignore lines with only one or two words, because they represent finishing part or signature



# salutation, receiver name, finishing, sendername, sender signature, 


class MainHeaderSection():
	def __init__(self):
		self.currentHeaderName = None
		self.currentHeaderVal = None
		self.completeFlag = False
		self.headers = {}

	def emittingStoppedAtEmptyLine(self):
		# print "main header finished"
		pass

	def emitted(self, s_line):
		# print 'header line emitted', s_line
		# s_stripped_line = s_line.strip('> ?')
		if(headerRegEx.search(s_line) != None):
			# print self.file.name, 'it is a header line'
			if(self.currentHeaderName != None):
				self.headers[self.currentHeaderName] = self.currentHeaderVal.strip()
			(headerName, value) = self.parseHeaderLine(s_line) 
			self.currentHeaderName = headerName
			self.currentHeaderVal = value.strip()
			self.headers[self.currentHeaderName] = self.currentHeaderVal
		
		else:
			# continuation of the existing header, so append the value
			self.currentHeaderVal = self.currentHeaderVal + s_line.strip()
			self.headers[self.currentHeaderName] = self.currentHeaderVal

	def parseHeaderLine(self, s_line):
		headerList = s_line.split(':', 1)
		return (headerList[0], headerList[1])

	def writeOutHeaders(self, o_writer):
		print "writing out headers", self.headers
		filtered_dict = {k:v for k,v in self.headers.iteritems() if k.upper() in ['FROM', 'TO', 'CC', 'BCC','X-FROM', 'X-TO', 'X-CC', 'X-BCC'] and v}
		print "filtered dict", filtered_dict
		participantLine = json.dumps(filtered_dict)
		o_writer.writelines(participantLine)

	def get_headers_dict(self):
		filtered_dict = {k:v for k,v in self.headers.iteritems() if k.upper() in ['FROM', 'TO', 'CC', 'BCC','X-FROM', 'X-TO', 'X-CC', 'X-BCC'] and v}
		return filtered_dict

	def parseCompleted(self):
		self.completeFlag = True

	def parseComplete(self):
		return self.completeFlag

	def parse(self, pobj_walker):
		# pobj_walker.run_to_empty_line()
		pobj_walker.emit_until_empty_line(self)
		self.parseCompleted()



class ThreadHeaderSection():
	def __init__(self):
		self.currentHeaderParser = None
		self.prevHeaderParser = None
		self.completeFlag = False

	def parseCompleted(self):
		self.completeFlag = True

	def parseComplete(self):
		return self.completeFlag

	def parse(self, pobj_walker):
		pobj_walker.run_to_thread_empty_line()
		self.parseCompleted()

class MainContentSection():
	def __init__(self, o_writer):
		# self.o_walker = o_walker
		self.o_writer = o_writer
		self.b_has_attachments = False
		self.b_has_original_thread = False

	def parse(self, o_walker):
		o_walker.emit_until_pattern(None, self)

	def emitted(self, s_line):
		# print 'content', s_line

		s_transformed_line = replaceUnwantedAnywhere(s_line)
		ref = attachmentRef(s_line)
		if(ref):
			self.b_has_attachments = True
		else:
			# print 'Ignoring content writing'
			self.o_writer.writelines(s_line)

	def emittingStoppedAtPattern(self, s_line):
		# print 'emittingStoppedAtPattern - ', s_line
		self.b_has_original_thread = True

	def contains_attachments(self):
		return self.b_has_attachments

	def contains_original_thread(self):
		return self.b_has_original_thread

class HierarchichalThreadSection():
	def __init__(self, o_writer):
		self.o_original_stack = []
		self.current_thread = None
		self.o_writer = o_writer
		self.o_walker = None

	class OriginalThreadSection:
		def __init__(self, o_writer):
			self.o_writer = o_writer

		def emitted(self, s_line):
			s_stripped_line = s_line.lstrip(fixLineStart)

			ref = attachmentRef(s_line)
			if(ref):
				self.b_has_attachments = True
			else:
				#print 'ignoring thread content writing'
				self.o_writer.writelines(s_stripped_line)


	def parse(self, o_walker):
		# print 'new thread detected'
		self.o_walker = o_walker
		originalThread = self.OriginalThreadSection(self.o_writer)
		self.current_thread = originalThread
		self.o_original_stack.append(originalThread)

		o_thread_header_section = ThreadHeaderSection()
		o_thread_header_section.parse(self.o_walker)

		o_walker.emit_until_pattern(None, self )
		
	def emittingStoppedAtPattern(self, s_line):
		# print 'still older thread detected'
		originalThread = self.OriginalThreadSection(self.o_writer)
		self.current_thread = originalThread
		self.o_original_stack.append(originalThread)

		o_thread_header_section = ThreadHeaderSection()
		o_thread_header_section.parse(self.o_walker)

		self.o_walker.emit_until_pattern(None, self )

	def emitted(self, s_line):
		# print 'thread content', s_line
		o_current_thread = self.current_thread
		o_current_thread.emitted(s_line)

		
class LineWalker:
	def __init__(self, filepath):
		self.file = open(filepath, 'r')
		# self.l_reply_stack = []

	def filename(self):
		return os.path.basename(self.file.name)

	def close(self):
		self.file.close()

	def next_line(self):
		s_line = next(self.file, None)
		if(s_line == None):
			return s_line

		s_fixed_line = s_line

		s_next_line = ''
		if(s_line.strip().endswith('=')):
			s_next_line = self.next_line()
			if(s_next_line != None):
				s_fixed_line = s_line.strip() + s_next_line

		return s_fixed_line

	# def peek_next_line(self):
	# 	pos = self.file.tell()
	# 	s_line = self.file.next(None)
	# 	self.file.seek(pos)
	# 	return s_line

	def run_to_empty_line(self):
		while ( True):
			s_line = next(self.file, None)
			if(s_line == None):
				return

			# print s_line
			# s_stripped_line = s_line.strip('> ?')
			# if(headerRegEx.search(s_stripped_line) != None):
			# 	print self.file.name, 'it is a header line'
			# 	continue
			if(s_line.strip()):
				# print self.file.name, 'while(true) looking for next empty line'
				continue
			else:
				# print self.file.name, 'Empty Line. End of Header'
				return

	def run_to_thread_empty_line(self):
		while ( True):
			s_line = next(self.file, None)
			if(s_line == None):
				return
			# print s_line
			s_stripped_line = s_line.strip('> ?')
			# if(headerRegEx.search(s_stripped_line) != None):
			# 	print self.file.name, 'it is a header line'
			# 	continue
			if(s_stripped_line.strip()):
				# print self.file.name, 'while(true) looking for next empty line'
				continue
			else:
				# print self.file.name, 'Empty Line. End of Header'
				return

	def emit_until_pattern(self, s_stop_pattern, o_callback ):
		while(True):
			s_line = self.next_line()
			if(s_line == None):
				return
			else:
				# check if this line contains this pattern
				if(thread_start_check(s_line)):
					# currentLength = len(self.l_reply_stack)
					# self.l_reply_stack.append(currentLength+1)
					o_callback.emittingStoppedAtPattern(s_line)
					return
				else:
					# emit this line to the callback object
					o_callback.emitted(s_line)

	def emit_until_empty_line(self, o_callback):
		while ( True):
			s_line = next(self.file, None)
			if(s_line == None):
				return

			# print s_line
			# s_stripped_line = s_line.strip('> ?')
			# if(headerRegEx.search(s_stripped_line) != None):
			# 	# print self.file.name, 'it is a header line'
			# 	continue
			if(s_line.strip()):
				# print self.file.name, 'while(true) looking for next empty line'
				o_callback.emitted(s_line)
			else:
				# print self.file.name, 'Empty Line. End of Header'
				o_callback.emittingStoppedAtEmptyLine()
				return


class OutputWriter:
	def __init__(self, o_walker, s_output_folder, fileout_name ):
		self.o_walker = o_walker
		# self.o_file_writer = open(s_output_folder+'/'+fileout_name,'w')
		self.content_buffer_list = []

	def writelines(self, s_line):
		# self.o_file_writer.writelines(s_line)
		self.content_buffer_list.append(s_line)

	def get_output(self):
		return ''.join(self.content_buffer_list)


	def close(self):
		# self.o_file_writer.close()
		pass





class EnronParser:

	def generate_unique_file_name(self, pathoffile):
		regexmatch = folderpathregexpr.search(pathoffile)
		path = regexmatch.group(0)
		uniqfilename = path.replace('/','_')
		return uniqfilename

	def parse(self, o_file_walker, o_file_writer):
		
		# first, parse the headers
		o_header_section = MainHeaderSection()
		o_header_section.parse(o_file_walker)
		# o_header_section.writeOutHeaders(o_file_writer)
		header_dict = o_header_section.get_headers_dict()

		# now parse the main body
		o_main_content_section = MainContentSection(o_file_writer)
		o_main_content_section.parse(o_file_walker)

		# now parse the replies/threads
		if(o_main_content_section.contains_original_thread()):
			o_hierarchical_thread_section = HierarchichalThreadSection(o_file_writer)
			o_hierarchical_thread_section.parse(o_file_walker)

		# close the file walker and writer
		o_file_walker.close()
		o_file_writer.close()

		content_text = o_file_writer.get_output()

		return (header_dict, content_text)

		
	def start(self, s_input_folder, s_output_folder):
		print 'start the work'
		fileList = glob.glob(s_input_folder+'/all_documents/*')
		print 'no of files', str(len(fileList))
		errorlist = []
		for fStr in fileList:
			try:
				o_walker = LineWalker(fStr)
				print 'fileinname', fStr
				fileout_name = self.generate_unique_file_name(fStr)
				print 'fileoutname', fileout_name
				o_writer = OutputWriter(o_walker,s_output_folder, fileout_name)
				print 'processing ', fStr
				self.parse(o_walker,o_writer)
			except:
				errorlist.append(fStr)
				e = sys.exc_info()

				print 'processing error in file', fStr, e

		print 'Error Summary:'		
		for x in errorlist:
			print x


	def startOneFile(self, s_input_folder, s_file_name, s_output_folder):
		o_walker = LineWalker(s_input_folder+'/'+s_file_name)
		o_writer = OutputWriter(o_walker,s_output_folder, s_file_name)
		print 'processing ', s_file_name
		return self.parse(o_walker,o_writer)

	def parse_file(self, s_input_file_name):

		o_walker = LineWalker(s_input_file_name)
		o_writer = OutputWriter(o_walker,None, None)
		print 'processing ', s_input_file_name
		return self.parse(o_walker,o_writer)

			


def attachmentRef(line):
	for detector in attachDetector:
		if( (detector.search(line)) != None ):
			return True

	return False

def salutationRef(line):
	return False

def thread_start_check(line):
	# for ignoreMark in ignoreLineList:
	# 	if( (line.find(ignoreMark)) != -1 ):
	# 		return True
	# return False
	for detector in threadStartDetector:
		if( (detector.search(line)) != None ):
			return True

	return False


# def dropLine(line):
# 	for firstWord in firstWordDiscardList:
# 		if(line.startswith(firstWord)):
# 			return True

# 	for ignoreMark in ignoreLineList:
# 		if( (line.find(ignoreMark)) != -1 ):
# 			return True

# 	if(salutationRef(line)):
# 		return True

# 	if(attachmentRef(line)):
# 		return True


	# also ignore lines with only one or two words, because they represent finishing part or signature

	return False

def replaceUnwantedAnywhere(line):
	changedLine = line
	for k, v in tokenReplace.iteritems():
		changedLine = changedLine.replace(k,v)
	return changedLine

def rreplace(s, old, new, occurrence):
	li = s.rsplit(old, occurrence)
	return new.join(li)

def replaceUnwantedAtEnd(line):
	changedLine = line
	for k, v in lineEndReplace.iteritems():
		# print 'checking for ending with ', k, 'on this line', changedLine
		if(changedLine.rstrip().endswith(k)):
			# print changedLine
			changedLine = rreplace(changedLine, k, v, 1)
			# print 'replaced line', changedLine
	return changedLine

def writeOneLine(f, line):
	# file = open("newfile.txt", "w")
	f.writelines(line)





# readOneFile('../enron-data/maildir/lay-k/notes_inbox/398.')

# browseFolder('/home/mprakash/Documents/enron-data/maildir/lay-k', 'output/participants-2');

