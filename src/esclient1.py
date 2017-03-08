from datetime import datetime
from elasticsearch import Elasticsearch

# sys related utils
import logging
import sys
import os


ENRON_MAILDIR_PATH = '/home/mprakash/Documents/enron-data/maildir'

es = Elasticsearch()

log = logging.getLogger()
log.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)



def all_enron_file_list(enron_maildir_path):
	file_list = [] # ex ['lay-k/inbox/10.', 'skilling-j/notes-inbox/46.', .....]
	for root, dirs, files in os.walk(enron_maildir_path):
		dir_path = os.path.relpath(root, enron_maildir_path)
		folder_name = os.path.basename(dir_path)
		# print 'root->', folder_name, dir_path
		relevant_files = [ file for file in files if folder_name not in ['all_documents']]
		for yfile in relevant_files:
			print  'path->', dir_path, 'file->', yfile
			file_list.append(dir_path+'/'+yfile)
	return file_list


# def stream_enron_files(enron_maildir_path):
# 	for x in file_array:
# 		yield enron_maildir_path + '/' + x

def file_2_esdoc(file_path):
	try:
		parser = enron_file_parser.EnronParser()
		header, content_text = parser.parse_file(file_path)
		es_doc = populate_es_doc(file_path, headers, content_text)
		return es_doc
	except:
		log.error('Error in parsing ->')
		log.error(file_path)
		# return "PARSE_ERROR"
		return TaggedDocument(utils.to_unicode("PARSE_ERROR").lower().split(), [file_path])

def stream_paragraph(enron_maildir_path):
	for x in file_array:
		yield file_2_esdoc(enron_maildir_path + '/' + x)

def populate_es(esdoc, doc_id):
	doc = {}
	res = es.index(index='test-index', doc_type='emaildb', id=1, body=doc)
	print res




# doc = {
# 	'channel':'email',
# 	'network':'enron',
# 	'text':'ingest this first',
# 	'sent_time':datetime.now()
# }

# res = es.index(index='test-index', doc_type='emaildb', id=1, body=doc)
# print res

file_array = all_enron_file_list(ENRON_MAILDIR_PATH)

def main():
	for x

