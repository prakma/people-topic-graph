import spacy
en_nlp = spacy.load('en')
en_doc = en_nlp('Hello, world. Here are two sentences.')
print 'spacy parsed doc'

print((w.text, w.pos_) for w in doc)
print en_doc

def readOneFile(filePath, outputFolderStr):
	f = open(filePath, 'r')
	content = f.read()
	f.close()
	return content

def nlp_hello():
	en_doc = en_nlp('Hello, world. Here are two sentences.')
	print 'spacy parsed doc'

	print((w.text, w.pos_) for w in doc)
	# print en_doc

def nlp_out(filecontent):
	en_doc = en_nlp('Hello, world. Here are two sentences.')
	print 'spacy parsed doc'

	print((w.text, w.pos_) for w in doc)
	print en_doc


def start( fileName ):
	nlp_hello(
		readOneFile(fileName) )


if __name__ == '__main__':
	print 'this program needs 1 arguments - path to the file to read'
	print 'arguments provided', sys.argv[1], sys.argv[2]
	start(sys.argv[2])
	
	