# -*- coding: utf-8 -*-
import os
import requests
import requests_random_user_agent
import sys
import csv
import logging
import time
import sys
import time
import colorlog
from selenium import webdriver
from bs4 import BeautifulSoup
from msedge.selenium_tools import EdgeOptions
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager
import json
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import os

os.environ['WDM_LOCAL'] = '1'
def singleton(cls):
    instances = {}
    def get_instance():
        if cls not in instances:
            instances[cls] = cls()
        return instances[cls]
    return get_instance()

@singleton
class log():
    def __init__(self):
        self.logger = colorlog.getLogger()
        self.logger.setLevel(colorlog.colorlog.logging.INFO)
        handler = colorlog.StreamHandler()
        handler.setFormatter(colorlog.ColoredFormatter('%(log_color)s [%(asctime)s] [%(levelname)s] %(white)s%(message)s', datefmt='%H:%M:%S',
            reset=True,
            log_colors={
                'DEBUG':    'cyan',
                'INFO':     'green',
                'WARNING':  'yellow',
                'ERROR':    'red',
                'CRITICAL': 'bg_red',
            },
            secondary_log_colors={},
            style='%'))
        self.logger.addHandler(handler)

class URLChecker:
	def __init__(self):
		try:
			os.mkdir("outputs")
		except:
			pass
		if os.path.exists("backup.log"):
			with open("backup.log","r") as reader:
				self.backup =[i.strip("\n") for i in reader.readlines()]
		else:
			self.backup = []
		if not os.path.exists("result.csv"):
			with open('output.csv', 'w', newline='', encoding='utf-8') as f:
	    			writer = csv.writer(f)
	    			writer.writerow(["URL", "STATUS", "FILENAME"])  
	def driverdata(self):
		#capabilities = DesiredCapabilities.CHROME.copy()
		capabilities = DesiredCapabilities.EDGE.copy()
		capabilities['goog:loggingPrefs'] = {'performance': 'ALL'}
		capabilities['acceptSslCerts'] = True
		#options = webdriver.ChromeOptions()
		options = EdgeOptions()
		options.add_argument('--ignore-ssl-errors=yes')
		options.add_argument('--ignore-certificate-errors')
		options.add_argument(' --no-sandbox')
		#driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(),desired_capabilities=capabilities,options=options)
		driver = webdriver.Chrome(executable_path=EdgeChromiumDriverManager().install(),desired_capabilities=capabilities) 
		driver.set_page_load_timeout(7)
		return driver
	def get_result(self,url):
		headers = {
		'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:92.0) Gecko/20100101 Firefox/92.0',
		'Accept-Language': 'en-US,en;q=0.5',
		'platform': 'WEB',
		'Connection': 'keep-alive',
		'Referer': 'https://www.google.com/',
		'Cache-Control': 'no-cache',
		'TE': 'trailers'
		}
		try:
			response = requests.get(url,headers=headers, timeout = 8)
			return response
		except requests.exceptions.ConnectionError as e:
			print(e)
			return False
	def get_status(self,logs):
		for log in logs:
			if log['message']:
				d = json.loads(log['message'])
				try:
					#print(d['message']['params']['response']['status'])
					content_type = 'text/html' in d['message']['params']['response']['headers']['content-type']
					response_received = d['message']['method'] == 'Network.responseReceived'
					return d['message']['params']['response']['status']
				except Exception as e:
					#print(e)
					pass

	def GETURLS(self):
		if os.path.exists("urls.txt"):
			with open("urls.txt", "r") as reader:
				urls = [i.strip("\n") for i in reader.readlines() if i.strip("\n") not in self.backup and len(i.strip("\n"))>1]
				for j in urls:
					try:
						driver = self.driverdata()
					except Exception as e: #handle exception
						print(e)
						sys.exit()
						
					if "https" not in j.lower():
						log.logger.info("checking with http ")
						i = "https://{}".format(j)
					else:
						i = j
					log.logger.info(j)
					try:
						driver.get(i)
						log.logger.info("Waiting 10 secends to load page completely...........")
						time.sleep(10)
					except Exception as e:
						print(e)
						with open('output.csv', 'a', newline='', encoding='utf-8') as f:
							writer = csv.writer(f)
							writer.writerow([j, "blocked", "false"])  
							continue
					if "blocked" in driver.title.lower():
						status = ''
					else:
						current_url = driver.current_url
						js = '''
						let callback = arguments[0];
						let xhr = new XMLHttpRequest();
						xhr.open('GET', '{}', true);
						xhr.onload = function () {{
						    if (this.readyState === 4) {{
							callback(this.status);
						    }}
						}};
						xhr.onerror = function () {{
						    callback('error');
						}};
						xhr.send(null);
						'''.format(current_url)
						status= driver.execute_async_script(js)
					if status == 200 or status == '200':
						status = "working"
					else:
						status = "blocked"
					name = "_".join(j.split("/"))
					filename = "{}.txt".format(name)
					namereal = os.path.join("outputs",filename)
					html_source = driver.page_source
					soup = BeautifulSoup(html_source,"html.parser")
					textdata = soup.get_text(separator=' ')
					with open(namereal,"w", encoding='utf-8') as writer:
						writer.write(str(textdata))
					with open('output.csv', 'a', newline='', encoding='utf-8') as f:
						writer = csv.writer(f)
						writer.writerow([j, status, namereal])  	
					with open("backup.log","a") as writer:
						writer.write(j+"\n")	 
					driver.close()   
					#sys.exit()	
				
		else:
			log.logger.critical("Urls.txt file not found ")
			log.logger.info("creating url file ")
			urlfile = open("urls.txt","a")
			urlfile.close()
			log.logger.info("please add your urls in urls.txt file")
			log.logger.info("add then again run the script")
			sys.exit()
			
obj = URLChecker()
obj.GETURLS()
