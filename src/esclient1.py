from datetime import datetime
from elasticsearch import Elasticsearch

# sys related utils
import logging
import sys
import os
import json
import dateutil.parser

# import 
import enron_file_parser


ENRON_MAILDIR_PATH = '/home/mprakash/Documents/enron-data/maildir'
# ENRON_MAILDIR_PATH = '/Users/manoj/Documents/Projects/tprojs/machine_learning/enron_data/maildir'
es = Elasticsearch()

log = logging.getLogger()
log.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
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
			# print  'path->', dir_path, 'file->', yfile
			file_list.append(dir_path+'/'+yfile)
	return file_list


def create_es_doc_object(doc_id, headers, content_text):
	required_fields = ['FROM', 'TO', 'CC', 'BCC','X-FROM', 'X-TO', 'X-CC', 'X-BCC']
	es_dict = {k:v for k,v in headers.iteritems() if k.upper() in required_fields and v}
	es_dict['content'] = content_text
	es_dict['doc_id'] = doc_id
	es_dict['sent_time'] = (dateutil.parser.parse(headers['Date'])).isoformat()
	# print "es dict", es_dict
	# print 'sent time', es_dict['sent_time']
	return es_dict



def file_2_esdoc(file_path, relative_path):
	try:
		parser = enron_file_parser.EnronParser()
		headers, content_text = parser.parse_file(file_path)
		es_doc = create_es_doc_object(relative_path, headers, content_text)
		return es_doc
	except:
		log.error('Error in parsing ->')
		log.error(file_path)
		raise
		# return None


def stream_paragraph(enron_maildir_path):
	file_array = all_enron_file_list(enron_maildir_path)
	# file_array = ['allen-p/_sent_mail/1.']
	for x in file_array:
		log.info('read enron file %s', x)
		try:
			yield file_2_esdoc(enron_maildir_path + '/' + x, x)
		except:
			log.error('Error in parsing and creating es doc -> %s', x)
		
		log.info('Moving on to next file parsing');	

def populate_es(esdoc_dict):
	if(esdoc_dict is not None):
		# print 'doc_id for es ', esdoc_dict['doc_id']
		res = es.index(index='enron_commindex', doc_type='emaildb', id=esdoc_dict['doc_id'], body=json.dumps(esdoc_dict))
		# print res
	else:
		log.error('Ignoring. None object cannot be created in ES')




# doc = {
# 	'channel':'email',
# 	'network':'enron',
# 	'text':'ingest this first',
# 	'sent_time':datetime.now()
# }

# res = es.index(index='test-index', doc_type='emaildb', id=1, body=doc)
# print res



def main():
	log.info('read enron file and populate es')
	for x in stream_paragraph(ENRON_MAILDIR_PATH):
		try:
			populate_es(x)
		except:
			log.error('Error in populating ES')
	log.error('Population to ES completed')

if __name__ == '__main__':
	main()


