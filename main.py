#!/usr/bin/python

from optparse import OptionParser
import os
import re
import sys
import datetime
import string

report = {}
wordscore = {}
filescore = {}
filelist = list()
skipped = 0
opened = 0
datasize = 0
progresstext = "" 

def sortscore(score, reverse=False):
	sortedscore = sorted(score.items(), key=lambda score: score[1], reverse=reverse)
	returnscore = []
	for s in sortedscore:
		if s[1] > 0:
			returnscore.append(s)
	
	return returnscore

def printscore(report):
	for i in report:
		print i[0] + ':' + str(i[1])

def scorewords(report):
	for file in report.keys():
		for word in report[file].keys():
			if not word in wordscore:
				wordscore[word] = 0
			if not file in filescore:
				filescore[file] = 0
			wordscore[word] += report[file][word]
	return wordscore

def scorefile(report):
	for file in report.keys():
		for word in report[file].keys():
			if not word in wordscore:
				wordscore[word] = 0
			if not file in filescore:
				filescore[file] = 0
			filescore[file] += report[file][word]
	return filescore

def summary(report):
	filescore = scorefile(report)
	text = ""
	for file in sortscore(filescore):
		text += file[0] + '(' + str(file[1]) + '):'
		for word in report[file[0]].keys():
			if report[file[0]][word] > 0:
				text += word + '(' + str(report[file[0]][word]) + ');' 
		text += '\n'
	return text

def wholeword(word, string):
	re.purge()
	matches = []
	
	if word.isdigit():
		int(word)
		regexNum = r'([^0-9]|\b)(' + word + r')([^0-9]|\b)'
		mN = re.search(regexNum, string)
		if "groups" in dir(mN):
			matches.append(mN.groups())
	
	else:
		regexU = r'([A-Z]|[^a-zA-Z]|\b)(' + word.lower() + r')([A-Z]|[^a-zA-Z]|\b)'
		regexL = r'([a-z]|[^a-zA-Z]|\b)(' + word.upper() + r')([a-z]|[^a-zA-Z]|\b)'
		mU = re.search(regexU, string)
		if "groups" in dir(mU):
			matches.append(mU.groups())
		re.purge()
		mL = re.search(regexL, string)
		if "groups" in dir(mL):
			matches.append(mL.groups())
	return matches

def skipfile(filename,skippedexts):
	if not isinstance(skippedexts, list):
		return False
	for skip in skippedexts:
		if filename.endswith(skip):
			return True
	return False

def scoretext(wordlist, text, maxwholewordlen = -1):
	score = {}
	for word in wordlist:
		wordreg = word.replace('-', ' ')
		wordreg = wordreg.replace(' ', '['+string.punctuation+' ]*')
		if int(len(word)) > int(maxwholewordlen):
			matches = [] 
			m = re.search(wordreg.lower(),text.lower())
			if "groups" in dir(m):
				matches.append(m.groups())
			score[word] = len(matches)			
		else:
			score[word] = len(wholeword(wordreg,text))
	return score

usage = "%prog [options] DIRECTORY ... DIRECTORYN"
epilog = "example: ./main.py ../git.lf/janitor -s .ppt -s .docx -s .pdf -s .xls -s .xlsx -s .gif -s .png -s .jpg -s .css -r fw -w cryptology.txt -c -p -l 3"
parser = OptionParser(usage = usage, epilog = epilog)
parser.add_option("-f", "--file", dest="suspiciousfilename", help="specify file to scan", action="append")
parser.add_option("-w", "--wordlist", dest="wordlistfilename", help="file containing all of the words to look for")
parser.add_option("-s", "--skip", dest="skipfileextensions", help="file extensions to skip", action="append")
parser.add_option("-v", "--verbose", dest="verbose", help="print verberose information", default=False, action="store_true")
parser.add_option("-r", "--report", dest="printreport", default="wf", help="print score")
parser.add_option("--show-wordlist", dest="show_wordlist", default=False, help="print list of words to detect", action="store_true")
parser.add_option("-c", "--display-counts", dest="display_counts", default=False, help="Show the num ber of files processed", action="store_true")
parser.add_option("-p", "--display_progress", dest="display_progress", default=False, help="show percentage complete", action="store_true")
parser.add_option("-l", "--max-wholeword-length", dest="maxwholewordlength", type="int", default=-1, help="maximun length of a word allowed to only find matches on whole word")
parser.add_option("-o", "--summary-file", dest="summaryfile", help="name of the file to store the summary in")
parser.add_option("-x", "--display-summary", dest="displaysummary", default=False, help="Display a summary from the summary file", action="store_true")
parser.add_option("-X", "--dont-display-summary", dest="dontdisplaysummary", default=False, help="Dont Display a summary after running a scan", action="store_true")

(options, args) = parser.parse_args()

if options.wordlistfilename:
	wordlist = list(set(open(options.wordlistfilename).read().lower().strip().split('\n')))
			
if options.show_wordlist: print wordlist; exit()

if options.displaysummary and options.summaryfile:
	report = dict()
	try:
		summaryfile = open(options.summaryfile)
	except:
		print "no summary file: " + options.summaryfile
		exit()
	#sample input
	#../bzr.lf/lsb/devel/build_env/headers/x86-64/4.1/glib-2.0/gio/gmenuexporter.h.defs(1): export(1);
	for line in summaryfile:
		#find the file name which is before the matching parathsis before the last colon on the line
		filename = line[:line[:line.rfind(':')].rfind('(')]
		#find the total number of words found by locating the end of the filename and taking the number in parathesis right before the :
		totalfilecount = line[line[:line.rfind(':')].rfind('(')+1:line[:line.rfind(':')].rfind(')')]
		#find the list of words following the :, and split them by the ;, and then drop the last item on the list which is always a \n
		foundwords = line[line.rfind(':')+1:].split(';')[:-1]
		report[filename] = dict()		
		for w in foundwords:
			w = w.strip()
			word = w[:w.find('(')]
			wcount = w[w.find('(')+1:w.find(')')]		
			report[filename][word] = int(wcount)

	if options.printreport:
		if options.printreport == "f":
			printscore(sortscore(scorefile(report)))
		elif options.printreport == "w":
			printscore(sortscore(scorewords(report)))
		elif options.printreport == "wf" or options.printreport == "fw":
			print summary(report)			
	else:
		print summary(report)
	exit()


for a in args:
	#filelist.append(a)
	for (path, dirs, files) in os.walk(a):
		if 'CVS' in dirs:
			dirs.remove('CVS')
		if '.git' in dirs:
			dirs.remove('.git')
		if '.bzr' in dirs:
			dirs.remove('.bzr')
		if '.hg' in dirs:
			dirs.remove('.hg')
		if '.svn' in dirs:
			dirs.remove('.svn')
	
		for file in files:
			filelist.append(path + '/' + file)
	
if options.suspiciousfilename:
	filelist += options.suspiciousfilename

start = datetime.datetime.now()
for file in filelist:
	if skipfile(file, options.skipfileextensions):
		skipped += 1
		continue
	try:
		f = open(file)
	except:
		print "failed to open: " + file
		continue
	opened +=1
	now = datetime.datetime.now()
	estimate = (((now - start) / (opened + skipped)) * len(filelist)) 
	if options.display_progress: 
		print '\r' + " " * len(progresstext) + '\r',
		progresstext = str(((opened + skipped)*1.0/len(filelist))*100)[:5] + '% '+ " time left:" + str(estimate).split('.')[0] + ' ' + file + '\r'
		print progresstext,
	sys.stdout.flush()
	filecontents = f.read()
	datasize += len(filecontents)		
	filenamescore = scoretext(wordlist, file, options.maxwholewordlength)
	filecontentsscore = scoretext(wordlist, filecontents, options.maxwholewordlength)
	report[file] = {}
	for k in filecontentsscore.keys():
		report[file][k] = filenamescore[k] + filecontentsscore[k]

if options.display_progress: 
	print '\r' + " " * len(progresstext) + '\r',

if options.printreport and not options.dontdisplaysummary:
	if options.printreport == "f":
		printscore(sortscore(scorefile(report)))
	elif options.printreport == "wf" or options.printreport == "fw":
		print summary(report)
	else:
		printscore(sortscore(scorewords(report)))

if options.display_counts:
	print "total files:" + str(len(filelist)) ,
	print "suspicious files:" + str(len(sortscore(scorefile(report)))) ,
	print "skipped files:" + str(skipped) ,
	print "searched:" + str(datasize) + 'B', 
	print "time:" + str(datetime.datetime.now() - start).split('.')[0]

if options.summaryfile and len(filelist) > 0 and not options.displaysummary:
	summaryfilename = options.summaryfile	
	counter = 0
	while os.path.isfile(summaryfilename):
		counter +=1
		summaryfilename = options.summaryfile + '.' + str(counter)
	try:
		if counter > 1: print "saving as " + summaryfilename + "...."	
		summaryfile = open(summaryfilename, 'w+')
		summaryfile.write(summary(report))
		summaryfile.close()		
	except:
		print report
		print "error saving summary as " + summaryfilename


def test():
	print wholeword("22", "port22")
	print wholeword("22", "22")
	print wholeword("22", ":22'")
	print wholeword("22", "223")	
	print wholeword("22", "open('22')")
	print wholeword("ear","bearth")
	print wholeword("ear","BearTH")
	print wholeword("ear","bEARth")
	print wholeword("ear","ear_")
	print wholeword("ear","ear()")
	print wholeword("ear","ear.")
	print wholeword("ear","ear:")
	print wholeword("ear","ear\n\r")
	print wholeword("ear","myEAR() MYear: myEAR()")

#test()
