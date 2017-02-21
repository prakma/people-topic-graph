# gensim modules
from gensim import utils
from gensim.models.doc2vec import TaggedDocument
from gensim.models import Doc2Vec

# random shuffle
from random import shuffle

# numpy
import numpy

# classifier
from sklearn.linear_model import LogisticRegression
from sklearn.externals import joblib

# sys related utils
import logging
import sys
import os

# enron parser
import enron_file_parser

log = logging.getLogger()
log.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

ENRON_MAILDIR_PATH = '/Users/manoj/Documents/Projects/tprojs/machine_learning/enron_data/maildir'

# class TaggedLineSentence(object):
#     def __init__(self, sources):
#         self.sources = sources

#         flipped = {}

#         # make sure that keys are unique
#         for key, value in sources.items():
#             if value not in flipped:
#                 flipped[value] = [key]
#             else:
#                 raise Exception('Non-unique prefix encountered')

#     def __iter__(self):
#         for source, prefix in self.sources.items():
#             with utils.smart_open(source) as fin:
#                 for item_no, line in enumerate(fin):
#                     yield TaggedDocument(utils.to_unicode(line).split(), [prefix + '_%s' % item_no])

#     def to_array(self):
#         self.sentences = []
#         for source, prefix in self.sources.items():
#             with utils.smart_open(source) as fin:
#                 for item_no, line in enumerate(fin):
#                     self.sentences.append(TaggedDocument(utils.to_unicode(line).split(), [prefix + '_%s' % item_no]))
#         return self.sentences

#     def sentences_perm(self):
#         shuffle(self.sentences)
# 	return self.sentences
        

def all_enron_file_list(enron_maildir_path):
	file_list = [] # ex ['lay-k/inbox/10.', 'skilling-j/notes-inbox/46.', .....]
	for root, dirs, files in os.walk(enron_maildir_path):
		# path = root.split(os.sep)
		# print((len(path) - 1) * '---', os.path.basename(root))
		# for file in files:
		# 	print(len(path) * '---', file)

		dir_path = os.path.relpath(root, enron_maildir_path)
		# print 'root->', dir_path
		for file in files:
			# print  'path->', dir_path, 'file->', file
			file_list.append(dir_path+'/'+file)
	return file_list

log.info('preparing file list')

file_array = all_enron_file_list(ENRON_MAILDIR_PATH)

# def stream_enron_files(enron_maildir_path):
# 	for x in file_array:
# 		yield enron_maildir_path + '/' + x

def file_content(file_path):
	try:
		parser = enron_file_parser.EnronParser()
		header, content_text = parser.parse_file(file_path)
		gensim_doc = TaggedDocument(utils.to_unicode(content_text).lower().split(), [file_path])
		return gensim_doc
	except:
		log.error('Error in parsing ->')
		log.error(file_path)
		# return "PARSE_ERROR"
		return TaggedDocument(utils.to_unicode("PARSE_ERROR").lower().split(), [file_path])

def stream_paragraph(enron_maildir_path):
	for x in file_array:
		yield file_content(enron_maildir_path + '/' + x)

def stream_random_paragraphs(enron_maildir_path):
	shuffle(file_array)
	for x in file_array:
		yield file_content(enron_maildir_path + '/' + x)


log.info('source load')
sources = {'test-neg.txt':'TEST_NEG', 'test-pos.txt':'TEST_POS', 'train-neg.txt':'TRAIN_NEG', 'train-pos.txt':'TRAIN_POS', 'train-unsup.txt':'TRAIN_UNS'}

log.info('TaggedDocument')
# sentences = TaggedLineSentence(sources)

log.info('D2V')
model = Doc2Vec(min_count=1, window=10, size=100, sample=1e-4, negative=5, workers=7)
model.build_vocab(stream_paragraph(ENRON_MAILDIR_PATH))

log.info('Epoch')
for epoch in range(10):
	log.info('EPOCH: {}'.format(epoch))
	model.train(stream_random_paragraphs(ENRON_MAILDIR_PATH))

log.info('Model Save')
model.save('./enron_doc2vec_model.d2v')


