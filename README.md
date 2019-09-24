# Downloading and parsing US Capitol Police arrest reports

Thanks to Mike Stucka for this great tutorial
[this great tutorial on scraping with pyquery](https://github.com/PalmBeachPost/nicar19scraping/blob/master/00-Scraping%20--%20full%20self-tutorial.ipynb) ... yeah, I switched to bs4 but this got me started.

### How to use it
* Clone this repository
* Install libraries with `pip3 install -r requirements.txt` from the cloned directory
* Run `python3 uscp_arrests.py` or `jupyter notebook uscp_arrests.ipynb from the terminal`
* Visit `http://127.0.0.1:8001/uscp_arrests`

### Things used:
* [requests](https://2.python-requests.org/en/master/)
* [pdfplumber](https://github.com/jsvine/pdfplumber)
* [pandas](https://pandas.pydata.org)
* [beautifulsoup](https://www.crummy.com/software/BeautifulSoup/bs4/doc/)
* [datasette](https://datasette.io)
* [csvs-to-sqlite](https://github.com/simonw/csvs-to-sqlite)
* Logger from [@ilanamarcus](https://github.com/ilanamarcus)

### Here's where the arrest reports [live](https://www.uscp.gov/media-center/weekly-arrest-summary).

### To do:
* ~~Refine datasette:~~
    * ~~SQLite apparently infers that number an int, should stay string in case of leading zeros. (This apparently might not be possible.) Fixed w/ --shape.~~
* ~~Functionify dir creation~~
* ~~Make a new csv each time the script runs~~
* ~~requirements.txt~~
* Implement emails w/ function
* YAML/cron
