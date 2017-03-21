'''
1. Read directory of companies with directory of 10K files broken into multiple sections
	a. Edge case handling for years without matching 10K items
2. Create "Check.txt" file where each line holds data to make a single label in feedforward nn
	a. Each label contains two years, consecutive 10K items (1, 7a, etc), market cap of second year, date, filename, index
	b. Ignore full 10K file each year
	c. Add market cap later through bloomberg terminal
3. Create GloVe vectors for every item in Check.txt
	a. dump vectors in pickle dictionary {filname:GloVe_vector}
4. Gives access to function "construct_feedforward_data"
	a. returns indices, labels, embeddings (all are lists)
	b. indices = 1 to len(check.txt)
	c. labels = bin market caps into X number of bins (X = number output nodes in ff nn)
	d. embeddings = GloVe(yearA_item7a) - GloVe(yearB_item7a)
5. TBD

'''

import os
import pickle
import argparse
import bisect
#import create_glove_embeddings
import csv
import numpy as np
import time




def stringToEmbedding(s):
	replace_punctuation = string.maketrans(string.punctuation, ' '*len(string.punctuation))
	replace_digits = string.maketrans(string.digits, ' '*len(string.digits))

	s = s.lower()
	s = s.translate(replace_punctuation)
	s = s.translate(replace_digits)
	s = re.sub(r'\s+', ' ', s)

	tokens = s.split(' ')
	numTokens = len(tokens)
	tokenVals = np.array([gloveDict.get(token, 0) for token in tokens])
	tokenAverage = np.mean(tokenVals, axis=0)
	return tokenAverage

# This is top-level to play nice with multiprocessing - 
# pass it a gloveDict to open the file.

def createSingleEmbedding(targetPath):
	filename = targetPath.split('\\')[-1]

	file_10k = open(targetPath, 'r')
	fileString = file_10k.read()
	file_10k.close()

	# embedding = stringToEmbedding(fileString, gloveDict)
	embedding = stringToEmbedding(fileString)

	print 'embedded', filename
	return [filename, embedding]


def createInflationDict():
    '''
    Loads the manual-entry inflation_table.txt into a dict to convert
    the market caps to current day currency.
    '''
    f = open('inflation_table.txt', 'r')
    lines = f.readlines()
    f.close()
    inflationDict = {}
    for line in lines:
        year, rate =line.split('\t')
        inflationDict[int(year)] = float(rate)
    return inflationDict

def make_labelfile():
	#company_labels = {}
	ticker_year_change = {}
	inflationDict = createInflationDict()
	print inflationDict

	filename = 'nyse.csv'
	with open(filename, 'rU') as f:
		reader = csv.reader(f)
		next(f)
		for row in reader:
			if row[-1] != "#N/A N/A" and row[-1] != "#N/A Invalid Security": #if at least one valid market cap label
				#year_market_dict = {}
				for year in range(1, len(row)-1):
					if row[year]!= "#N/A N/A" and row[year] != "#N/A Invalid Security" and row[year+1]!= "#N/A N/A" and row[year+1] != "#N/A Invalid Security" : #current year and next year have valid market cap data
						curAdjMc = float(row[year])*inflationDict[1993+year]				
						nextAdjMc = float(row[year+1])*inflationDict[1993+year+1]
						if curAdjMc != 0:
							key = (row[0],year+1993)
							value = (nextAdjMc - curAdjMc)/curAdjMc	#change from current year to next year
							ticker_year_change[key] = value
				# 			year_market_dict[1993+year] = (nextAdjMc - curAdjMc)/curAdjMc
				# if len(year_market_dict) != 0:
				# 	company_labels[row[0]] = year_market_dict
	f.close()

	filename = 'nasdaq.csv'
	with open(filename, 'rU') as f:
		reader = csv.reader(f)
		next(f)
		for row in reader:
			if row[-1] != "#N/A N/A" and row[-1] != "#N/A Invalid Security": #if at least one valid market cap label
				#year_market_dict = {}
				for year in range(1, len(row)-1):
					if row[year]!= "#N/A N/A" and row[year]!= "#N/A Invalid Security" and row[year+1]!= "#N/A N/A" and row[year+1]!= "#N/A Invalid Security":
						curAdjMc = float(row[year])*inflationDict[1993+year]
						nextAdjMc = float(row[year+1])*inflationDict[1993+year+1]
						if curAdjMc != 0:
							key = (row[0],year+1993)
							value = (nextAdjMc - curAdjMc)/curAdjMc	#change from current year to next year
							ticker_year_change[key] = value
				# if len(year_market_dict) != 0:
				# 	company_labels[row[0]] = year_market_dict
	f.close()

	total = len(ticker_year_change)
	#print total
	#print ticker_year_change

	with open(r"labels.pickle", "wb") as output_file:
		pickle.dump(ticker_year_change, output_file)

	return ticker_year_change

# '1c', '1d', '1e', '1f', '1g', '1h', '2', '3', '5', 
# '6', '7b', '7c', '7d', '8', '9c', '9d', '9e', '9f', 
# '9g', '9h', '10', '11', '12', '13', '16a' '16b', '16c'

def get_integer_representation(ticker, year, item, file_to_ints):

	if item == '1c':
		return file_to_ints.get((ticker,year,'1')), file_to_ints.get((ticker,year+1,'1'))
	elif item == '1d':
		return file_to_ints.get((ticker,year,'1a')), file_to_ints.get((ticker,year+1,'1a'))
	elif item == '1e':
		return file_to_ints.get((ticker,year,'1b')), file_to_ints.get((ticker,year+1,'1b'))
	elif item == '1f':
		ir1 = file_to_ints.get((ticker,year,'1'))
		if (ticker,year,'1a') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year,'1a')))
		ir2 = file_to_ints.get((ticker,year+1,'1'))
		if (ticker,year+1,'1a') in file_to_ints:
			ir2.extend(file_to_ints.get((ticker,year+1,'1a')))
		return ir1, ir2
	elif item == '1g':
		ir1 = file_to_ints.get((ticker,year,'1a'))
		if (ticker,year,'1b') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year,'1b')))
		ir2 = file_to_ints.get((ticker,year+1,'1a'))
		if (ticker,year+1,'1b') in file_to_ints:
			ir2.extend(file_to_ints.get((ticker,year+1,'1b')))
		return ir1, ir2
	elif item == '1h':
		ir1 = file_to_ints.get((ticker,year,'1'))
		if (ticker,year,'1a') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year,'1a')))
		if (ticker,year,'1b') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year,'1b')))
		ir2 = file_to_ints.get((ticker,year+1,'1'))
		if (ticker,year+1,'1a') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year+1,'1a')))
		if (ticker,year+1,'1b') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year+1,'1b')))
		return ir1, ir2
	elif item == '2':
		return file_to_ints.get((ticker,year,'2')), file_to_ints.get((ticker,year+1,'2'))
	elif item == '3':
		return file_to_ints.get((ticker,year,'3')), file_to_ints.get((ticker,year+1,'3'))
	elif item == '5':
		return file_to_ints.get((ticker,year,'5')), file_to_ints.get((ticker,year+1,'5'))
	elif item == '6':
		return file_to_ints.get((ticker,year,'6')), file_to_ints.get((ticker,year+1,'6'))
	elif item == '7b':
		return file_to_ints.get((ticker,year,'7')), file_to_ints.get((ticker,year+1,'7'))
	elif item == '7c':
		return file_to_ints.get((ticker,year,'7a')), file_to_ints.get((ticker,year+1,'7a'))
	elif item == '7d':
		ir1 = file_to_ints.get((ticker,year,'7'))
		if (ticker,year,'7a') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year,'1a')))
		ir2 = file_to_ints.get((ticker,year+1,'7'))
		if (ticker,year+1,'1a') in file_to_ints:
			ir2.extend(file_to_ints.get((ticker,year+1,'7a')))
		return ir1, ir2
	elif item == '8':
		return file_to_ints.get((ticker,year,'8')), file_to_ints.get((ticker,year+1,'8'))
	if item == '9c':
		return file_to_ints.get((ticker,year,'9')), file_to_ints.get((ticker,year+1,'9'))
	elif item == '9d':
		return file_to_ints.get((ticker,year,'9a')), file_to_ints.get((ticker,year+1,'9a'))
	elif item == '9e':
		return file_to_ints.get((ticker,year,'9b')), file_to_ints.get((ticker,year+1,'9b'))
	elif item == '9f':
		ir1 = file_to_ints.get((ticker,year,'9'))
		if (ticker,year,'9a') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year,'9a')))
		ir2 = file_to_ints.get((ticker,year+1,'9'))
		if (ticker,year+1,'9a') in file_to_ints:
			ir2.extend(file_to_ints.get((ticker,year+1,'9a')))
		return ir1, ir2
	elif item == '9g':
		ir1 = file_to_ints.get((ticker,year,'9a'))
		if (ticker,year,'9b') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year,'9b')))
		ir2 = file_to_ints.get((ticker,year+1,'9a'))
		if (ticker,year+1,'9b') in file_to_ints:
			ir2.extend(file_to_ints.get((ticker,year+1,'9b')))
		return ir1, ir2
	elif item == '9h':
		ir1 = file_to_ints.get((ticker,year,'9'))
		if (ticker,year,'9a') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year,'9a')))
		if (ticker,year,'9b') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year,'9b')))
		ir2 = file_to_ints.get((ticker,year+1,'9'))
		if (ticker,year+1,'9a') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year+1,'9a')))
		if (ticker,year+1,'9b') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year+1,'9b')))
		return ir1, ir2
	elif item =='10':
		return file_to_ints.get((ticker,year,'10')), file_to_ints.get((ticker,year+1,'10'))
	elif item =='11':
		return file_to_ints.get((ticker,year,'11')), file_to_ints.get((ticker,year+1,'11'))
	elif item =='12':
		return file_to_ints.get((ticker,year,'12')), file_to_ints.get((ticker,year+1,'12'))
	elif item =='13':
		return file_to_ints.get((ticker,year,'13')), file_to_ints.get((ticker,year+1,'13'))
	elif item == '16b':
		return file_to_ints.get((ticker,year,'14')), file_to_ints.get((ticker,year+1,'14'))
	elif item == '16c':
		return file_to_ints.get((ticker,year,'15')), file_to_ints.get((ticker,year+1,'15'))
	elif item == '16d':
		ir1 = file_to_ints.get((ticker,year,'14'))
		if (ticker,year,'15') in file_to_ints:
			ir1.extend(file_to_ints.get((ticker,year,'15')))
		ir2 = file_to_ints.get((ticker,year+1,'14'))
		if (ticker,year+1,'15') in file_to_ints:
			ir2.extend(file_to_ints.get((ticker,year+1,'15')))
		return ir1, ir2
	return None

def get_mcmfd(labels):

	year_median = {}
	year_mcs = {}

	for key in labels:
		if key[1] in year_mcs:
			#print (key[0],key[1])
			#print dic[(key[0],key[1])]
			year_mcs[key[1]].append(labels[(key[0],key[1])])
			#print labels[(key[0],key[1])]
		else:
			year_mcs[key[1]] = [labels[(key[0],key[1])]]
	for year in year_mcs:
		#print year
		l = year_mcs[year]
		median = np.median(np.array(l))
		l.sort()
		
		year_median[year] = median
	return year_median

def make_examples(path, labels, ir_dict):
	fileCounter = 0
	checkfile_lines = []
	ticker_year_dict = {}
	for subdir, dirs, files in os.walk(path):
	 	for f in files:

	 		fileTokens = f.split("_")
	 		fileTokens[-1] = fileTokens[-1].strip(".txt")
	 		if "section" in fileTokens:
	 			filedate = fileTokens[1].split("-")

	 			if (fileTokens[0], int(filedate[0])) not in ticker_year_dict:
	 				ticker_year_dict[(fileTokens[0], int(filedate[0]))] = [fileTokens[-1]]
	 			else:
	 				if fileTokens[-1] not in ticker_year_dict[(fileTokens[0], int(filedate[0]))]:
	 					bisect.insort(ticker_year_dict[(fileTokens[0], int(filedate[0]))], fileTokens[-1])
	 					#ticker_year_dict[(fileTokens[0], filedate[0])].append(fileTokens[-1])
	
	orderedList = ticker_year_dict.items()
	orderedList = sorted(orderedList, key = lambda t: t[0])

	for i in range(0, len(orderedList)):
		if '1' not in orderedList[i][1] and '1a' not in orderedList[i][1] and '1b' not in orderedList[i][1]:
			pass #No operation
		elif '1' not in orderedList[i][1] and '1a' not in orderedList[i][1] and '1b' in orderedList[i][1]:
			orderedList[i][1].extend(('1c'))
		elif '1' not in orderedList[i][1] and '1a' in orderedList[i][1] and '1b' not in orderedList[i][1]:
			orderedList[i][1].extend(('1g'))
		elif '1' not in orderedList[i][1] and '1a' in orderedList[i][1] and '1b' in orderedList[i][1]:
			orderedList[i][1].extend(('1d', '1e', '1g'))
		elif '1' in orderedList[i][1] and '1a' not in orderedList[i][1] and '1b' not in orderedList[i][1]:
			orderedList[i][1].extend(('1h'))
		elif '1' in orderedList[i][1] and '1a' not in orderedList[i][1] and '1b' in orderedList[i][1]:
			orderedList[i][1].extend(('1e', '1f', '1h'))
		elif '1' in orderedList[i][1] and '1a' in orderedList[i][1] and '1b' not in orderedList[i][1]:
			orderedList[i][1].extend(('1c', '1g', '1h'))
		elif '1' in orderedList[i][1] and '1a' in orderedList[i][1] and '1b' in orderedList[i][1]:
			orderedList[i][1].extend(('1c', '1d', '1e', '1f', '1g', '1h'))

		if '7' not in orderedList[i][1] and '7a' not in orderedList[i][1]:
			pass #No operation
		elif '7' not in orderedList[i][1] and '7a' in orderedList[i][1]:
			orderedList[i][1].extend(('7c'))
		elif '7' in orderedList[i][1] and '7a' not in orderedList[i][1]:
			orderedList[i][1].extend(('7d'))
		elif '7' in orderedList[i][1] and '7a' in orderedList[i][1]:
			orderedList[i][1].extend(('7b', '7c', '7d'))

		if '9' not in orderedList[i][1] and '9a' not in orderedList[i][1] and '9b' not in orderedList[i][1]:
			pass #No operation
		elif '9' not in orderedList[i][1] and '9a' not in orderedList[i][1] and '9b' in orderedList[i][1]:
			orderedList[i][1].extend(('9c'))
		elif '9' not in orderedList[i][1] and '9a' in orderedList[i][1] and '9b' not in orderedList[i][1]:
			orderedList[i][1].extend(('9g'))
		elif '9' not in orderedList[i][1] and '9a' in orderedList[i][1] and '9b' in orderedList[i][1]:
			orderedList[i][1].extend(('9d', '9e', '9g'))
		elif '9' in orderedList[i][1] and '9a' not in orderedList[i][1] and '9b' not in orderedList[i][1]:
			orderedList[i][1].extend(('9h'))
		elif '9' in orderedList[i][1] and '9a' not in orderedList[i][1] and '9b' in orderedList[i][1]:
			orderedList[i][1].extend(('9e', '9f', '9h'))
		elif '9' in orderedList[i][1] and '9a' in orderedList[i][1] and '9b' not in orderedList[i][1]:
			orderedList[i][1].extend(('9c', '9g', '9h'))
		elif '9' in orderedList[i][1] and '9a' in orderedList[i][1] and '9b' in orderedList[i][1]:
			orderedList[i][1].extend(('9c', '9d', '9e', '9f', '9g', '9h'))

		if '14' not in orderedList[i][1] and '15' not in orderedList[i][1]:
			pass #No operation
		elif '14' not in orderedList[i][1] and '15' in orderedList[i][1]:
			orderedList[i][1].extend(('16b'))
		elif '14' in orderedList[i][1] and '15' not in orderedList[i][1]:
			orderedList[i][1].extend(('16c'))
		elif '14' in orderedList[i][1] and '15' in orderedList[i][1]:
			orderedList[i][1].extend(('16a', '16b', '16c'))
	


	possible_items = ['1c', '1d', '1e', '1f', '1g', '1h', '2', '3', '5', \
                      '6', '7b', '7c', '7d', '8', '9c', '9d', '9e', '9f', \
                      '9g', '9h', '10', '11', '12', '13', '16a' '16b', '16c']
	training_examples = []
	total_examples = 0


	marketcap_change_median_from_data = get_mcmfd(labels)
	#print marketcap_change_median_from_data

	for i in range(0, len(orderedList)-1):
		if orderedList[i][0][0] == orderedList[i+1][0][0]: #symbols match
			#if label exists for (AA, year)
			for item in possible_items:
				if item in orderedList[i][1] and item in orderedList[i+1][1]:
					if orderedList[i][0] in labels:
						#print "GOT IT"
						#print "Stock found in labels"
						if orderedList[i][0] in labels:
							ir = get_integer_representation(orderedList[i][0][0], orderedList[i][0][1], item, ir_dict) #handle concatenation usage(ticker, year, item)
							if ir != None:
								if ir[0] != None and ir[1] != None: 
									if orderedList[i+1][0] in labels:
										mc_change = labels[orderedList[i+1][0]]	#change market cap of that year
										# if mc_change >= marketcap_change_median_from_data:
										# 	l = 0
										# else:
										# 	l = 1

										example = []
										example.append(orderedList[i][0][0])	#ticker symbol
										example.append(orderedList[i][0][1])	#year 1
										example.append(orderedList[i+1][0][1])	#year 2
										example.append(item)
										example.append(ir)
										example.append(mc_change)	#label 0 = worse than median change, 1 = better than median change
										training_examples.append(example)
										total_examples += 1

								if total_examples%1000 == 0:
									print str(total_examples) + "examples added to training examples..."
	print str(total_examples) + " total training examples created"

	mcs = []
	for each in training_examples:
		mcs.append(each[-1])

	mcs.sort()
	median = mcs[len(mcs)/2]

	for each in training_examples:
		if each[-1] <= median:
			each[-1] = 0
		else:
			each[-1] = 1
	return training_examples



# Opens up the given glove file in the path, creates
# dictionary to be shared as we're doing things.
def createGloveDict(gloveDim='50'):
	t = time.time()
	glovePath = "data_scraping/glove/glove.6B." + gloveDim + 'd.txt'

	if not os.path.isfile('data_scraping/glove/gloveDict_' + gloveDim + '.pkl'):
		print 'Creating new gloveDict'
		newGloveDict = {}
		gloveFile = open(glovePath)
		lines = gloveFile.readlines();
		gloveFile.close()

		for line in lines:
		    split = line.split()
		    word = split[0]
		    embedding = np.float32(split[1:])
		    newGloveDict[word] = embedding

		gloveDict = OrderedDict(newGloveDict)
		pickle.dump(gloveDict, open('data_scraping/glove/gloveDict_' + gloveDim + '.pkl', "wb+" ) )
	else:
		print 'Loading gloveDict'
		gloveDict = pickle.load(open('data_scraping/glove/gloveDict_' + gloveDim + '.pkl'))

	print "took", str(time.time() - t)
	return gloveDict



if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Scrapes Market Cap from SEC db.')
	parser.add_argument('-d','--directory', help='Directory containing financial documents', required=True)
	args = vars(parser.parse_args())
	print 'Looking in directory: ', 
	labels = make_labelfile()

	if not os.path.exists(args['directory']):
		print 'Directory is not a path!'

	t = time.time()
	print 'Loading gloveDict...'
	gloveDict = createGloveDict(gloveDim='50')
	print 'Took ', str(time.time() - t), 'seconds.'

	t = time.time()
	print 'Loading pickle...'
	ir = pickle.load(open('data_scraping/DocumentWordIDDict_60k.pkl'))
	print 'Took ', str(time.time() - t), 'seconds.'

	t = time.time()
	print 'Making examples...'
	examples = make_examples(args['directory'], labels, ir)
	print 'Took ', str(time.time() - t), 'seconds.'

	t = time.time()
	print 'Writing manifest...'
	out = open("manifest_50.txt", 'wb+')
	for i in xrange(len(examples)):
		examples = examples[i]
		ticker, y1, y2, section, ir, label = example
		ir0 = ir[0]
		ir1 = ir[1]
		embedded0 = list(np.mean([gloveDict[integer] for integer in ir0], axis=0))
		embedded1 = list(np.mean([gloveDict[integer] for integer in ir1], axis=0))

		outList = [i, label, ','.join(embedded0), ','.join(embedded1)]
		outString = ','.join(outList)
		out.write(outString + '\n')
	out.close()
	print 'Took ', str(time.time() - t), 'seconds.'

									# example.append(orderedList[i][0][0])	#ticker symbol
									# example.append(orderedList[i][0][1])	#year 1
									# example.append(orderedList[i+1][0][1])	#year 2
									# example.append(item)
									# example.append(ir)
									# example.append(mc_change)	#label 0 = worse than median change, 1 = better than median change
	#d = get_mcmfd(labels)
	#print examples




