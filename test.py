#from selenium.webdriver.chrome.service import Service
#from selenium.webdriver.edge.service import Service

#from selenium.webdriver.firefox.options import Options
#from selenium.webdriver.firefox.service import Service
#from selenium.webdriver import Firefox


#service = Service(executable_path="C:\\EcoSticker\\msedgedriver.exe")
#driver = webdriver.Chrome(service=service)

#service = Service(executable_path="C:\\EcoSticker\\geckodriver.exe")
#driver = webdriver.Edge(service=service)

from selenium                           import webdriver
from webdriver_manager.firefox          import GeckoDriverManager
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service

op = Options()
#options.add_argument('-headless')
op.binary_location = r'C:\Program Files\Mozilla Firefox\firefox.exe'
sv = Service(executable_path="C:\\EcoSticker\\geckodriver.exe")
driver = webdriver.Firefox(service=sv, options=op)

driver.get("http://google.com/")
while True:
    pass