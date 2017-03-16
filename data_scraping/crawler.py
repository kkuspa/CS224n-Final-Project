# This script will download all the 10-K, 10-Q and 8-K 
# provided that of company symbol and its cik code.

from bs4 import BeautifulSoup
import re
import requests
import os
import time


class SecCrawler():

    REQUEST_SLEEP_TIME = 600
    HTTP_OKAY = 200
    ERROR_FILENAME = 'error_log.txt'

    def __init__(self):
        self.hello = "Welcome to Sec Cralwer!"

    def repeatRequest(self, target_url):
        r = requests.get(target_url)
        acceptable_errors = [404]
        while r.status_code != self.HTTP_OKAY:
            if r.status_code in acceptable_errors:
                print r.status_code, " received for request: ", target_url, ".  Moving on."
                return Nones
            print r.status_code, " received for request: ", target_url, ".  Sleeping for ", self.REQUEST_SLEEP_TIME, "..."
            time.sleep(self.REQUEST_SLEEP_TIME)
            r = requests.get(target_url)
        print r.status_code, " received for request: ", target_url, ".  Onwards!"    
        return r

    def make_directory(self, companyCode, cik, priorto, filingType):
        # Making the directory to save comapny filings
        if not os.path.exists("SEC-Edgar-data/"):
            os.makedirs("SEC-Edgar-data/")
        if not os.path.exists("SEC-Edgar-data/"+str(companyCode)):
            os.makedirs("SEC-Edgar-data/"+str(companyCode))
        if not os.path.exists("SEC-Edgar-data/"+str(companyCode)+"/"+str(filingType)):
            os.makedirs("SEC-Edgar-data/"+str(companyCode)+"/"+str(filingType))

    def parseData(self, soup):
        decomposeList = ["table", "a"]
        for toDecompose in soup.findAll(decomposeList):
            toDecompose.decompose()
            toDecompose.extract()
        return soup

    #Takes in an array of strings from BS4 and identifies the sentence with the market cap
    def findMarketCapText(self, strings):
        MAX_DOT_LOOKAHEAD = 5

        for line in strings:
            line = line.lower()
            if "aggregate" in line and "market" in line and "value" in line:
                idx = line.find('aggregate')
                if idx != -1:
                    line = line[idx:]
                    lineArray = line.split('.')
                    line = '.'.join(lineArray[:min(MAX_DOT_LOOKAHEAD, len(lineArray) - 1)])
                snippets = self.findPotentialMarketCapSentences(line)
                if len(snippets) > 0:
                    # print line
                    return snippets[0]
        for line in strings:
            line = line.lower()
            if "common stock" in line and "$" in line:
                idx = line.find("common stock")
                if idx != -1:
                    line = line[idx:]
                    lineArray = line.split('.')
                    line = '.'.join(lineArray[:min(MAX_DOT_LOOKAHEAD, len(lineArray) - 1)])
                snippets = self.findPotentialMarketCapSentences(line)
                if len(snippets) > 0:
                    # print line
                    return snippets[0]
        return None

    def convertTextToAmount(self, text):
        # print "TEXT IS: "
        if isinstance(text, tuple):
            text = text[0]
        amount = re.findall('[\d\,*\.*]+', text)
        if len(amount) == 0:
            return -1
        amount = amount[0].strip().replace(',','')
        amount = amount.strip('.')
        # print 'Amount: ', amount
        multiplier = 1
        if 'billion' in text:
            multiplier = 1000000000
        if 'million' in text:
            multiplier = 1000000
        return float(amount)*multiplier

    def findPotentialMarketCapSentences(self, sentence):
        potentialMarketCaps = re.findall(r'was\s*\$?((\d{1,3}(,\d{3})*(\.\d+)?) *[mb]illion(?i))', sentence)
        if len(potentialMarketCaps) is 0:
            print 1
            potentialMarketCaps = re.findall(r'was\s*\$ *((\d{1,3}(,\d{3})*(\.\d+)?))', sentence)
        if len(potentialMarketCaps) is 0:
            print 2
            potentialMarketCaps = re.findall(r'was\s*\$? *((\d{1,3}(,\d{3})*(\.\d+)?))', sentence)
        if len(potentialMarketCaps) is 0:
            print 3
            potentialMarketCaps = re.findall(r'approximately\s*\$? *((\d{1,3}(,\d{3})*(\.\d+)?) *[mb]illion(?i))', sentence)
        if len(potentialMarketCaps) is 0:
            print 4
            potentialMarketCaps = re.findall(r'approximately\s*\$ *((\d{1,3}(,\d{3})*(\.\d+)?))', sentence)
        if len(potentialMarketCaps) is 0:
            print 5
            potentialMarketCaps = re.findall(r'approximately\s*\$? ((\d{1,3}(,\d{3})*(\.\d+)?))', sentence)
        if len(potentialMarketCaps) is 0:
            print 6
            potentialMarketCaps = re.findall(r'\$? *((\d{1,3}(,\d{3})*(\.\d+)?) *[mb]illion(?i))', sentence)
        if len(potentialMarketCaps) is 0:
            print 7
            potentialMarketCaps = re.findall(r'\$ *((\d{1,3}(,\d{3})*(\.\d+)?))', sentence)
        if len(potentialMarketCaps) is 0:
            print 8
            potentialMarketCaps = re.findall(r'\$? ((\d{1,3}(,\d{3})*(\.\d+)?))', sentence)
        print potentialMarketCaps
        return potentialMarketCaps
            
    def marketCapFromText(self, marketCapText):
        marketCap = self.convertTextToAmount(marketCapText)
        return marketCap

    def getCombinedLineArray(self, lines):
        curLine = ""
        outArray= []
        for line in lines:
            found = re.findall('\.\s*$', line)
            curLine += line.strip() + " "
            if len(found) != 0:                
                curLine = curLine.replace("?", " ")
                curLine = re.sub(r'\s\s+', ' ', curLine)
                curLine = curLine.replace("\n", " ")
                outArray.append(curLine)
                curLine = ""
        return outArray

    def truncateDocumentData(self, data):
        strings = data.split('\n')
        endIdx = len(strings)
        for i in xrange(len(strings)):
            s = strings[i]
            if '</DOCUMENT>' in s:
                endIdx = i
                break
        strings = strings[:endIdx]
        newData = '\n'.join(strings)

        return newData

    def save_in_directory(self, companyCode, cik, priorto, filingURLList, docNameList, indexURLList, filingType):
        # Save every text document into its respective folder
        for i in range(len(filingURLList)):
            path = "SEC-Edgar-data/"+str(companyCode)+"/"+str(filingType)+"/"+str(docNameList[i])

            #Don't overwrite existing, non-text root files
            # if os.path.isfile(path):
            #     #Fixing weird .txt downloads
            #     f = open(path, 'r')
            #     original_filetype = f.readline().split('.')[-1]
            #     f.close()
            #     ##TODO: Remove the following after we actually fix things
            #     print 'Original filetype:', original_filetype
            #     if 'txt' not in original_filetype:
            #         print "ALREADY EXISTS: ", path, ', moving on...'
            #         continue

            t1 = time.time()
            target_url = filingURLList[i]
            index_url = indexURLList[i]
            print "Saving ", target_url, "..."

            r = self.repeatRequest(target_url)
            if r is None:
                errorFile = open(self.ERROR_FILENAME, 'a+')
                errorFile.write(target_url + '\n')
                errorFile.close()
                continue
            data = r.text
            strings = None

            #Attempt normal parsing.  If this fails, try truncating and parsing again
            #If this fails AGAIN, just ignore it completely.
            try:
                soup = BeautifulSoup(data, "lxml")
                soup = BeautifulSoup(soup.prettify(), "lxml")
                soup = self.parseData(soup)
                if '.txt' in target_url:
                    strings = [s.encode('ascii', 'replace') for s in soup.get_text().split('\n') if s.strip() != '']
                else:
                    strings = [s.encode('ascii', 'replace') for s in soup.strings if s.strip() != '']
                print 'finished initial souping'
            except:
                print 'Initial soup load failed'
                try:
                    data = self.truncateDocumentData(data)
                    soup = BeautifulSoup(data, "lxml")
                    soup = BeautifulSoup(soup.prettify(), "lxml")
                    soup = self.parseData(soup)
                    if '.txt' in target_url:
                        strings = [s.encode('ascii', 'replace') for s in soup.get_text().split('\n') if s.strip() != '']
                    else:
                        strings = [s.encode('ascii', 'replace') for s in soup.strings if s.strip() != '']
                except:
                    print 'Soup conversion failed.  Running as text.'
                    errorFile = open(self.ERROR_FILENAME, 'a+')
                    errorFile.write('SOUP CONVERSION FAILED: ' + target_url + '\n')
                    errorFile.close()
                    continue

            print "Num strings:", len(strings)
            outArray = self.getCombinedLineArray(strings)

            header = outArray[0:50]
           
            marketCapText = self.findMarketCapText(header)
            print marketCapText
            marketCap = -1
            if marketCapText is not None:
                marketCap = self.marketCapFromText(marketCapText)
            print marketCap

            outString = '\n'.join(outArray)
            outString = re.sub(r'(?<!\n)\n', '\n', outString)

            filename = open(path,"w+")
            filename.write(target_url + '\n')
            filename.write(index_url + '\n')
            filename.write(str(float(marketCap)) + '\n')
            infoArray = docNameList[i].strip(".txt").split('_')
            for info in infoArray:
                print info
                filename.write(info + '\n')
            filename.write(str(docNameList[i]) + '\n\n')
            filename.write(outString)
            filename.close()
            t2 = time.time()
            print "Downloaded " + companyCode + "'s " + filingType + "s: " + str(i) + "/" + str(len(filingURLList)) + ". Time: " + str(t2-t1) + "\n"


    #filingType must be "10-K", "10-Q", "8-K", "13F"

    def getFiling(self, companyCode, cik, priorto, count, filingType):
        try:
            self.make_directory(companyCode,cik, priorto, filingType)
        except:
            print "Not able to create directory"
        
        #generate the url to crawl 
        base_url = "http://www.sec.gov"
        target_url = base_url + "/cgi-bin/browse-edgar?action=getcompany&CIK="+str(companyCode)+"&type="+filingType+"&dateb="+str(priorto)+"&owner=exclude&output=xml&count="+str(count)    
        print "Now trying to download "+ filingType + " forms for " + str(companyCode) + ' from target url:\n' + target_url
        r = self.repeatRequest(target_url)
        data = r.text
        soup = BeautifulSoup(data, "lxml") # Initializing to crawl again
        linkList=[] # List of all links from the CIK page

        # If the link is .htm convert it to .html
        print "Printing all seen URLs\n\n"
        for link in soup.find_all('filinghref'):
            URL = link.string
            # print URL
            extension = link.string.split(".")[len(link.string.split("."))-1]
            if extension == "htm":
                URL+="l"
                linkList.append(URL)
                print URL
            if extension == "html":
                linkList.append(URL)
        linkListFinal = linkList
        
        numFiles = min(len(linkListFinal), count)
        print "Number of files to download: ", numFiles
        print "Starting download...."

        indexURLList = [] # List of index URLs used.
        filingURLList = [] # List of URLs scraped from index.
        docNameList = [] # List of document names

        for link in linkListFinal:
            r = self.repeatRequest(link)
            data = r.text
            newSoup = BeautifulSoup(data, "lxml") # Initializing to crawl again
            linkList=[] # List of all links from the CIK page

            # Finds the filing date for this set of documents
            grouping = newSoup.findAll('div', {'class': 'formGrouping'})[1]
            filingDate = grouping.find('div', {'class': 'info'}).string
            docName = companyCode + "_" + filingDate + "_" + filingType + ".txt"
            docNameList.append(docName)

            # Finds filingType documents from the index page using link checking
            def isFiling(filingType, URL):
                # print URL
                URL = URL.lower()
                filingType = filingType.lower()
                filingTypeFillerRegex = filingType.replace('-', '.')
                filingTypeNoHyphenRegex = filingType.replace('-', '')
                # print 'TESTING URL:', URL
                if '/archives/' in URL:
                    if re.search(filingTypeFillerRegex + '\.htm', URL) != None:
                        return True
                    if re.search(filingTypeNoHyphenRegex + '\.htm', URL) != None:
                        return True
                    if re.search(filingTypeFillerRegex + '\.txt', URL) != None:
                        return True
                    if re.search(filingTypeNoHyphenRegex + '\.txt', URL) != None:
                        return True
                return False

                # if '/archives/' in URL:
                #     if re.search(filingTypeFillerRegex + '\.htm', URL) != None
                #         return True
                #     if (filingType.replace('-', '') + '.htm') in URL:
                #         return True
                #     results = re.search(r'\.', URL)
                #     if (filingType + '.txt') in URL:
                #         return True
                #     if (filingType.replace('-', '') + '.txt') in URL:
                #         return True
                # return False

            foundFiling = False
            #Use the table search method to locate table rows with '10k'
            trs = soup.findAll('tr')
            for tr in trs:
                if not foundFiling:
                    tds = tr.findAll('td')
                    for td in tds:
                        s = str(td.string).lower().strip()


                        #Ignore 10k-ish filings
                        if '10-k' in s and '10-k/a' not in s and '10-k405' not in s:
                            URL = str(tr.find('a').string)
                            filingURLList.append(base_url + URL)
                            foundFiling = True
                            print 'FOUND FILING: ', URL
                            break

            #If we can't identify, use naive link checking method
            if not foundFiling:
                for linkedDoc in newSoup.find_all('a'):
                    URL = linkedDoc['href']
                    # print URL
                    if isFiling(filingType, URL):
                        filingURLList.append(base_url + URL)
                        print 'FOUND FILING: ', URL
                        foundFiling = True
                        break

            ''' If no filings found, THEN go look for complete submission .txt file'''
            if not foundFiling:
                linkID = link.split('/')[-1].strip('-index.html')
                for linkedDoc in newSoup.find_all('a'):
                    URL = linkedDoc['href']
                    if linkID in URL.lower() and '.txt' in URL.lower():
                        filingURLList.append(base_url + URL)
                        foundFiling = True
                        print 'FOUND FILING: ', URL
                        break

            if foundFiling:
                indexURLList.append(link)


        # try:
        self.save_in_directory(companyCode, cik, priorto, filingURLList, docNameList, indexURLList, filingType)
        # except:
            # print "Not able to save " + filingType + " files for " + companyCode