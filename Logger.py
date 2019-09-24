import os
import logging
from logging import handlers

# Usage:
# log = Log().getLogger() in every script that uses it 
# log.debug(msg) writes to console and local debug folder, will collect all log statements
# log.error(msg) writes to console and local error folder, will only collect level 'error' and above
# learn about logging levels: https://docs.python.org/2/library/logging.html

class Log:
    def __init__(self):        
        folder = '/debug'
        print(f'Creating the directory {folder} ...')
    
        if os.path.isdir(os.getcwd() + folder):
            print('Directory exists.')
        else:
            try:
                os.mkdir(os.getcwd() + folder)
            except OSError as e:
                print(e)
                print('Failed.')
            else:
                print('Success.')

        self.logger = logging.getLogger(__name__)
        if not len(self.logger.handlers):
            c_handler = logging.StreamHandler()
            f_handler = logging.handlers.RotatingFileHandler("debug/debug.log", maxBytes=20000, backupCount=10)
            e_handler = logging.handlers.RotatingFileHandler("debug/error.log", maxBytes=20000, backupCount=10)
            e_handler.setLevel(logging.ERROR)
            
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            
            c_handler.setFormatter(formatter)
            f_handler.setFormatter(formatter)
            e_handler.setFormatter(formatter)
            
            self.logger.addHandler(c_handler)
            self.logger.addHandler(f_handler)
            self.logger.addHandler(e_handler)
            
            self.logger.setLevel(logging.DEBUG)

    def getLogger(self):
        return self.logger