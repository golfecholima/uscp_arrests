#!/usr/bin/env python
# coding: utf-8

# <a href="https://colab.research.google.com/github/golfecholima/uscp_arrests/blob/master/uscp_arrests.ipynb" target="_parent"><img src="https://colab.research.google.com/assets/colab-badge.svg" alt="Open In Colab"/></a>

# # Downloading and parsing US Capitol Police arrest reports
# 
# Thanks to Mike Stucka for this great tutorial
# [this great tutorial on scraping with pyquery](https://github.com/PalmBeachPost/nicar19scraping/blob/master/00-Scraping%20--%20full%20self-tutorial.ipynb) ... yeah, I switched to bs4 but this got me started.
# 
# ### Things used:
# * [requests](https://2.python-requests.org/en/master/)
# * [pdfplumber](https://github.com/jsvine/pdfplumber)
# * [pandas](https://pandas.pydata.org)
# * [beautifulsoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
# * [datasette/csvs-to-sqlite](https://datasette.io)
# * Logger from [@ilanamarcus](https://github.com/ilanamarcus)
# 
# ### Here's where the arrest reports [live](https://www.uscp.gov/media-center/weekly-arrest-summary).
# 
# ### To do:
# * ~~Refine datasette:~~
#     * ~~SQLite apparently infers that number an int, should stay string in case of leading zeros. (This apparently might not be possible.) Fixed w/ --shape.~~
# * ~~Functionify dir creation~~
# * ~~Make a new csv each time the script runs~~
# * Implement emails w/ function
# * YAML/cron

# In[1]:


# Install dependencies
get_ipython().system('pip3 install pdfplumber pandas requests csvs-to-sqlite datasette beautifulsoup4')


# In[2]:


# External dependencies
import requests
import pdfplumber
import pandas as pd
from bs4 import BeautifulSoup
from Logger import Log

# Built-in dependencies
import csv
import re
import os
import glob
import datetime
import subprocess
import urllib
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError

# Set up logging
log = Log().getLogger()


# In[3]:


base_url = 'https://www.uscp.gov'
url = base_url + '/media-center/weekly-arrest-summary'
dt = str(datetime.datetime.now().strftime('%Y%m%d_%H%M%S'))
wd = os.getcwd()

# Making directories
def mkdir(d):
    log.debug(f'Creating the directory {d} ...')
    
    if os.path.isdir(d):
        log.debug(f'Directory already exists.')
    else:
        try:
            os.mkdir(d)
        except OSError as e:
            log.error(e)
            log.debug(f'Failed.')
        else:
            log.debug(f'Success.')


# In[4]:


# Get the HTML and download the PDFs 
def download(site):
    
    reports = wd + '/reports'
    
    mkdir(reports)
    
    try:
        log.debug(f'Getting {site}.')
        html = urlopen(site)
    except HTTPError as e:
        log.error(e)
        log.debug('Failed.')
        # Send a message somewhere
    except URLError as e:
        log.error(e)
        log.debug('Failed.')
        # Send a message somewhere
    else:
        log.debug('Done.')
    
    bs = BeautifulSoup(html.read(), 'html.parser')
    links = bs.find_all('a', text= re.compile('Arrest Summary .+'))
    
    if not links:
        log.debug('No links found. Hmmm, maybe the URL changed ...')
        # This because bad URL slug ending still returned a page, just not the right one
        # Send a message somewhere
    else:
        for link in links:
            try:
                href = link.attrs['href']
            except AttributeError as e:
                log.error(e)
                log.debug('Failed.')
                # Send a message somewhere
            else:
                filename = '/' + href.rsplit('/', 1)[1].lower().replace('%20', '_')
                log.debug('Downloading ' + filename)
                urllib.request.urlretrieve(base_url + href, reports + filename)
    
    pdfs = glob.glob(reports + '/*')
    return pdfs


# In[5]:


# Parse the downloaded PDFs
def parse_pdf(pdfs):
    log.debug('Parsing the PDFs ...')
    
    rows = []
    
    for pdf in pdfs:
        plumb = pdfplumber.open(pdf)
        pages = plumb.pages # A list of PDF page objects
        pages_text = ''

        for page in pages:
            text = page.extract_text()
            pages_text += text

        pages_text = re.sub(r'(^\d\s*(\n|$))', '\n', pages_text, flags=re.M) # Get rid of the page numbers

        # Regex to find each arrest report chunk https://regex101.com/r/kWkaLi/7
        regex = (
                r'((?:(?:.+\n)(?=(?:(?:\d{1,2}\/\d{1,2}\/\d{2,4})(?:\s+)(?:\d{1,2}:\d{1,2})(?:\s+)(?:\d{5,12}))))'
                r'(?:(?:\d{1,2}\/\d{1,2}\/\d{2,4})(?:\s+)(?:\d{1,2}:\d{1,2})(?:\s+)(?:\d{5,12}))'
                r'(?:(?:[\s\S]+?(?=(?:\Z)|(?:(?:(?:.+\n)(?=(?:(?:\d{1,2}\/\d{1,2}\/\d{2,4})(?:\s+)(?:\d{1,2}:\d{1,2})(?:\s+)(?:\d{5,12})))))))))'
        )

        chunks = re.findall(regex, pages_text, flags=re.M)

        for chunk in chunks:
            rows.append(chunk)
    
    log.debug('Done.')
    return rows


# In[6]:


# Parse each chunk/row to cols then dataframe
def parse_row(rows):
    log.debug('Parsing each row into columns ...')
    title = []
    date = []
    time = []
    number = []
    narrative = []
    d = {
    'title': title,
    'date': date,
    'time': time,
    'number': number,
    'narrative': narrative
    }
    
    for row in rows:
        row = row.strip() # Remove leading and trailing whitespace

        # Regex to slice up the different data points of each 'chunk'
        regex = r'(^.+\n)(?:(\d{1,2}\/\d{1,2}\/\d{2,4})(?:\s+)(\d{1,2}:\d{1,2})(?:\s+)(\d{5,12}))([\s\S]+)'

        titles = re.search(regex, row).group(1).strip()
        dates = re.search(regex, row).group(2).strip()
        times = re.search(regex, row).group(3).strip()
        numbers = re.search(regex, row).group(4).strip()
        narratives = re.sub('\n', '',(re.search(regex, row).group(5).strip()))

        title.append(titles)
        date.append(dates)
        time.append(times)
        number.append(numbers)
        narrative.append(narratives)
    
    log.debug('... putting into dataframe ...')
    
    df = pd.DataFrame(data = d)
    
    df['datetime'] = df['date'].map(str) + ' ' + df['time'] # Merge the date and time columns
    df['datetime'] = pd.to_datetime(df['datetime'], infer_datetime_format = True) # Make that new column a datetime type
    df['date'] = df['datetime'].dt.date # Split off date
    df['time'] = df['datetime'].dt.time # Split off time
    
    log.debug('Done.')
    return df


# In[7]:


# Make a CSV with datetime label that goes in the csv dir
def mkcsv(df):
    log.debug('Converting dataframe to csv ...')
    csvs = wd + '/csv'
    csv = csvs + '/uscp_arrests_' + dt + '.csv'
    
    mkdir(csvs)

    df.to_csv(csv, encoding='utf-8', index=False)
    log.debug(f'Saved the file {csv}.')
    
    return csv


# In[8]:


# Put it all in a datasette and 'publish'
def ds(csv):
    log.debug(f'Converting {csv} to .db ...')
    dbs = wd + '/db'
    db = dbs + '/uscp_arrests.db'
    
    mkdir(dbs)
    
    # Running terminal commands from python
    subprocess.check_call([
        'csvs-to-sqlite',
        '--replace-tables',
        '--shape',
        'title:title,date:date(TEXT),time:time(TEXT),number:number(TEXT),narrative:narrative,datetime:datetime(TEXT)',
        csv,
        db]) 
    # ^^ Trixy ^^ any time you would have a space in the command line
    # you need to comma separate and have a news string in the brackets.

    log.debug('Starting datasette at http://127.0.0.1:8001/ ...')
    subprocess.check_call(['datasette', db])
    
    return db


# In[ ]:


# Do the things

pdfs = download(url)
rows = parse_pdf(pdfs)
df = parse_row(rows)
csv = mkcsv(df)
ds(csv)

