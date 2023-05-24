import time
import random
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service				# 0.81 추가
from selenium.webdriver.chrome.options import Options				# 0.81 추가
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib3.exceptions import NewConnectionError
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, JavascriptException


CHROME_DRIVER = 'C:/EcoSticker/113/chromedriver.exe'
URL_ADMIN = "https://www.ev.or.kr/lcvms-mncpt/login.do"		

URL_ADMIN = "https://www.ev.or.kr/lcvms-mncpt/login.do"				# 관리자용 저공해차 발급 사이트


options = Options()
#options.add_argument("--headless")
#options.add_argument("--incognito")
#options.add_argument("--no-sandbox")
#options.add_argument("--disable-gpu")
options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.46")
options.add_argument("log-level=2")
options.add_argument("lang=ko_KR")
options.add_argument("start-maximized")
options.add_argument("--enable-javascript")
options.add_argument('--disable-blink-features=AutomationControlled')		# 웹드라이버 사용 은폐하기 (콘솔에서 navigator.webdriver = false)
options.add_experimental_option('excludeSwitches', ['enable-logging'])		# 불필요한 로그 메시지 없애기
options.add_experimental_option("excludeSwitches", ["enable-automation"])
options.add_experimental_option('useAutomationExtension', False)
#options.add_argument("--user-data-dir=" + SESSION_INFO_PATH)				# 세션정보 저장
service = Service(executable_path=CHROME_DRIVER)
browser = webdriver.Chrome(service=service, options=options)

# 사이트 접속
browser.get(URL_ADMIN)

# 로그인
browser.find_element(By.ID, "userId").send_keys('su0672')
browser.find_element(By.ID, "userPw").send_keys('su0672')
login_btn = browser.find_element(By.CLASS_NAME, "btn_login.mt20")
browser.execute_script("arguments[0].click();", login_btn)

keep_session = True
timeout_low = 10 * 60		# 10분
timeout_high = 19 * 60		# 19분 (20분=timeout)

#timeout = random.randint(timeout_low, timeout_high)
timeout = timeout_high
print(f"====[{timeout}초 후 refresh]=================================")

while keep_session == True:

	if timeout == 0:
		print("refresh합니다.")
		browser.refresh()

		# 페이지 정상인지 확인
		try:
			# 로그아웃 버튼
			logout_btn = browser.find_element(By.XPATH, '//*[@id="wrap"]/div[2]/div/div/div/ul/li[2]/a')
			print(f"[정상 접속] 로그아웃 버튼 찾음")
		except NewConnectionError as connection_error:
			print("[에러] 접속장애가 발생하였습니다")
			keep_session = False
		except (NoSuchElementException, ElementNotInteractableException) as no_element_error:
			print("[에러] 로그아웃 버튼이 안 보입니다")
			keep_session = False
		except Exception as etc_error:
			print(f"[에러] 기타 에러({etc_error})가 발생하였습니다")
			keep_session = False

		timeout = random.randint(timeout_low, timeout_high)
		print(f"====[{timeout}초 후 refresh]=================================")
	
	else:
		if timeout % 10 == 0:
			print(f"다음 refresh까지 {timeout}초 남았습니다")
		time.sleep(1)
		timeout -= 1
            

