import re
import os
import sys
import time
import base64
import pyperclip
from math import *
from threading import *
from cryptography.fernet import Fernet, InvalidToken 		# 암호화 패키지
from tkinter import *
from tkinter import messagebox

import chromedriver_autoinstaller
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service				# 0.81 추가
from selenium.webdriver.chrome.options import Options				# 0.81 추가
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib3.exceptions import NewConnectionError
from selenium.common.exceptions import TimeoutException, NoSuchElementException, ElementNotInteractableException, JavascriptException

CANVAS_WIDTH = 500
CANVAS_HEIGHT = 540

WIN_POS_X = 1400
WIN_POS_Y = 100

X_POS_ISSUENUM = int(CANVAS_WIDTH * 0.32)
Y_POS_ISSUENUM = int(CANVAS_HEIGHT * 0.685)
X_POS_REGNUM = X_POS_ISSUENUM
Y_POS_REGNUM = int(CANVAS_HEIGHT * 0.785)

# 윈도의 X위치 : root.winfo_x()      # 1233
# 윈도의 Y위치 : root.winfo_y()      # 258

# 윈도의 X크기 : root.winfo_width()         # 500
# 윈도의 Y크기 : root.winfo_height()        # 540

# 현재화면 X해상도 : root.winfo_screenwidth()   # 1920
# 현재화면 Y해상도 : root.winfo_screenheight()  # 1080

HOME_PATH = r"C:/EcoSticker"
SESSION_INFO_PATH = HOME_PATH + r"/session_info"
AUTH_FILE = HOME_PATH + r"/Auth.dat"

# chromedriver_autoinstaller로 현재 크롬 버전에 맞는 드라이버 자동 다운로드
chrome_ver = chromedriver_autoinstaller.get_chrome_version().split('.')[0]			# 103
CHROME_DRIVER = HOME_PATH + f"/{chrome_ver}/chromedriver.exe"						# C:/EcoSticker/103/chromedriver.exe
if os.path.exists(CHROME_DRIVER):
    print(f"chrome driver is insatlled: {CHROME_DRIVER}")
else:
    print(f"install the chrome driver(ver: {chrome_ver})")
    chromedriver_autoinstaller.install(path=HOME_PATH)								# path="C:/EcoSticker"로 주면 'C:/EcoSticker/103/chromedriver.exe' 생성



URL_ADMIN = "https://www.ev.or.kr/lcvms-mncpt/login.do"				# 관리자용 저공해차 발급 사이트
#URL_GUEST = "https://www.ev.or.kr/lcvms-portal/EP020401000SF01.do"	# 일반인용 저공해차 확인 사이트

AUTHENTICATION_SUCCESS = False
AUTH_DEFAULT_KEY = "EcoSticker2021 by Kim Jae Hyoung"				# 길이=32byte : base64.urlsafe_b64decode(key)=32
ADMIN_ID = ""
ADMIN_PW = ""


VER = "0.95"														# 0.6 ==> 0.7(크롬드라이버 자동설치 + 크롬드라이버 중복실행 제거 browser.close + browser.quit)
																	# 0.82 : Selenium4에 맞게 함수 고침, 0.83: 'useAutomationExtension'=False
																	# 0.9 : send_key(Keys.Enter)로 안눌리는 버튼 누르기 성공
																	# 0.91 : Javascript Injection
																	# 0.93 : 사이트 팝업 메시지를 재시도창에 띄움 (0.94에서 당일등록차량 추가)

# 자동차 등록번호 정규식 	: '[0-9]{2,3}[가-힣][0-9]{4}'
# 영업용 등록번호 정규식 	: '서울[0-9]{2}[가-힣][0-9]{4}'
# ==> 2개 통합한 정규식 	: '(서울)?[0-9]{2,3}[가-힣][0-9]{4}'

## 테스트 차대번호 : 일반적으로 17자리 (끝자리 6자리 = 반드시 숫자)
# 1종 : KNAC381AFNA002915 KMHJ8816FNU018004
# 2종 : KNAPV81GBNK000521 KNARF81GBNA068551
# 3종 : KPBXH3AT1NP370787 KMHL341DBNA179522
# *** 독일차 차대번호 : WBA7L7106M7J56681 (끝자리 5개 숫자)
# *** 예외적 차대번호 : 끝자리 3/4자리만 숫자도 존재함
# *** 발급된 적 없는 차대번호 : KMHE341DBNA616046 (택시)



# 브라우저 접속용 쓰레드 함수 : login + check + issue 통합
class WebAgentThread(Thread):
	# 초기화
	def __init__(self, login_test=False, testID="", testPW=""):
		super(WebAgentThread, self).__init__(daemon=True)

		# 내부 변수 초기화
		self.reg_num = ""
		self.vin_num = ""
		self.issue_num = ""

		self.eco_class = ""
		self.car_name = ""
		self.fuel_type = ""
		self.owner_name = ""
		self.issue_count = ""
		self.auth_num = ""

		# 로그인 테스용일 때만 사용되는 변수 4개
		self.login_test = login_test
		self.login_test_success = None
		self.testID = testID
		self.testPW = testPW

		# 브라우저 변수
		self.options = None
		self.browser = None

		# 저공해차 표지 발급 과정 변수
		self.eco_process_done = False 		# 발급과정 끝났음
		self.eco_process_success = False	# 발급 성공/실패
		self.eco_process_message = ""		# 발급 절차 팝업창 메시지
		
		self.getReady()

	# 사이트 접속용 Headless Chrome 생성
	def getReady(self):
		self.options = Options()
		#self.options.add_argument("--headless")
		#self.options.add_argument("--incognito")
		#self.options.add_argument("--no-sandbox")
		#self.options.add_argument("--disable-gpu")
		self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36 Edg/110.0.1587.46")
		self.options.add_argument("log-level=2")
		self.options.add_argument("lang=ko_KR")
		self.options.add_argument("start-maximized")
		self.options.add_argument("--enable-javascript")
		self.options.add_argument('--disable-blink-features=AutomationControlled')		# 웹드라이버 사용 은폐하기 (콘솔에서 navigator.webdriver = false)
		self.options.add_experimental_option('excludeSwitches', ['enable-logging'])		# 불필요한 로그 메시지 없애기
		self.options.add_experimental_option("excludeSwitches", ["enable-automation"])
		self.options.add_experimental_option('useAutomationExtension', False)
		#self.options.add_argument("--user-data-dir=" + SESSION_INFO_PATH)				# 세션정보 저장
		self.service = Service(executable_path=CHROME_DRIVER)
		self.browser = webdriver.Chrome(service=self.service, options=self.options)

	
	# 등록번호 / 차대번호 입력
	def setCarInfo(self, reg_num, vin_num):
		self.vin_num = vin_num
		self.reg_num = reg_num


	# 쓰레드 실행함수
	def run(self):
		
		# 1. 저공해차 확인 사이트 접속
		print("[저공해 확인] 저공해 발급사이트 접속합니다...")
		try:
			self.browser.get(URL_ADMIN)
			self.browser.implicitly_wait(2)		# 페이지 완전히 로딩될 때까지 최대 2초 기다린다.
		except NewConnectionError as nce:
			print("[로그인 확인] 발급사이트와 연결되지 못했습니다.(연결거부 or 서버장애)")
			self.eco_process_success = False
			self.browser.close()
			self.browser.quit()
			self.eco_process_done = True
			return
		
		# 2-1. ID/PW 조정(test모드냐 아니냐에 따라 ID/PW 다름)
		if self.login_test == True:
			ID = self.testID
			PW = self.testPW
		else:
			ID = ADMIN_ID
			PW = ADMIN_PW
		
		# 2-2. 로그인(ID/PW)
		try:
			#id_field = self.browser.find_element(By.ID, "userId")		# ID
			#id_field.clear()
			#for char in ID:
			#	id_field.send_keys(char)
			#	time.sleep(0.15)
			self.browser.find_element(By.ID, "userId").send_keys(ID)		# ID
			#pw_field = self.browser.find_element(By.ID, "userPw")		# PW
			#pw_field.clear()
			#for char in PW:
			#	pw_field.send_keys(char)
			#	time.sleep(0.15)
			self.browser.find_element(By.ID, "userPw").send_keys(PW)
			
			#login_btn = self.browser.find_element(By.CLASS_NAME, "btn_login.mt20")		# 로그인버튼 
			#self.browser.execute_script("arguments[0].click();", login_btn)
			self.browser.execute_script("""getForm = function (form) { var formObj = null; if(typeof(form) == "object") { formObj = form; } else { var $formByName = $("form[name=" + form + "]"); var $formById = $("form").find("#" + form); if($formByName.length > 0) { formObj = $formByName[0]; } else if($formById.length > 0) { formObj = $formById[0]; }} return formObj; };""")
			#time.sleep(0.1)
			self.browser.execute_script("""checkPki = function () { var result = false; $.ajax({ type: "post", cache: false, url: CONTEXT_PATH + "/common/check/pki_check.jsp", async: false, dataType: "json", data: {}, complete: function(data, status) { var resultJson = JSON.parse(data.responseText); result = resultJson.result; } }); return result;};""")
			#time.sleep(0.1)
			self.browser.execute_script("""formSubmit = function (form, isBizSkip, _target, certOptions, ppcOptions) { var formObj = getForm(form); if(certOptions && certOptions["isCert"] === true) { PkiUtils.cert.setCertVidData(formObj, certOptions["certVid"], certOptions["certType"]); if(checkPkiCert()) { if(!PkiUtils.cert.setCertData(formObj, certOptions["certVid"], certOptions["certType"])) { return; } }} if(ppcOptions && ppcOptions["isPpc"] === true) { PpcUtil.setData(formObj, ppcOptions); } if(isSubmit) { return; } if(currentFocusElement) { $(currentFocusElement).blur(); } var $formObj = $(formObj); $formObj.find("input[name=isProcess]").remove(); $formObj.append('<input type="hidden" name="isProcess" value="' + ((isBizSkip) ? "false" : "true") + '" />'); $formObj.attr("method", "post"); if (_target != null && _target != "") { $formObj.attr("target", _target); } isSubmit = true; if(checkPki()) { PkiUtils.setEncryptData(formObj, PkiUtils.getEncryptData(formObj)); } if(formObj != null) formObj.submit(); else $formObj.submit(); };""")
			#time.sleep(0.1)
			self.browser.execute_script("""(function () { var $loginForm = $(getForm("_loginForm")); $loginForm.attr("action", CONTEXT_PATH + "/j_spring_security_check"); formSubmit($loginForm[0]); })()""")

		except Exception as e:
			print("[저공해 확인] 로그인 중 예상 못한 오류 발생")
			print(f"Exception Type: {type(e)}, Exception: {e}")
			#print(sys.exc_info()[1])
			self.login_test_success = False
			self.browser.close()
			self.browser.quit()
			self.eco_process_done = True
			return
		
		# 2-2. 로그인 : 로그인 테스트 모드이면 ==> 성공/실패 저장 + 로그아웃
		if self.login_test == True:
			# 로그아웃 버튼 XPATH : '//*[@id="wrap"]/div[2]/div/div/div/ul/li[2]/a'
			try:
				logout_btn = WebDriverWait(self.browser, 2).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="wrap"]/div[2]/div/div/div/ul/li[2]/a')))
				logout_btn.click()
				print("[로그인 확인] 로그인 / 로그아웃 둘 다 성공")
				self.login_test_success = True
			except:
				print("[로그인 확인] ID/PW가 올바르지 않습니다.")
				self.login_test_success = False

			self.browser.close()
			self.browser.quit()
			return
		

		#############################################################
		# 공지사항 "당일 등록차량에 대하여 표지발급이 아닌 임의표지발급으로만 처리되던 사항은 수정하였습니다."
		# "닫기" 버튼 XPATH : '//*[@id="reqBtnClose1"]'
		# 뜨면 닫고, 안 뜨면 말고 ==> NoSuchElementException, ElementNotInteractableException
		try:
			notice_close_btn = WebDriverWait(self.browser, 1).until(EC.presence_of_element_located((By.XPATH, '//*[@id="reqBtnClose1"]')))
			notice_close_btn.click()
		except (NoSuchElementException, ElementNotInteractableException, TimeoutException): 
			pass

		# 3. 발급페이지 웹엘리먼트에 차량등록번호 / 입력
		self.browser.find_element(By.XPATH, '//*[@id="vinNm"]').send_keys(self.vin_num)			# 차대번호 입력
		self.browser.find_element(By.XPATH, '//*[@id="carRegistNo"]').send_keys(self.reg_num)	# 등록번호 입력
		self.browser.find_element(By.XPATH, '//*[@id="btnSearch"]').click()						# 확인(검색)버튼 클릭
		print("[저공해 확인] 차대입력 후 확인 버튼 클릭!")

		# Case1. 오류팝업/긴급공지 나오는 경우 ==> 기다렸다가 팝업의 "확인" 버튼 클릭
		try:
			# 오류 팝업의 "확인" 버튼 XPATH : '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a'
			# 오류 팝업의 "내용" XPATH 		: '//*[@id="layerPop2"]/div/div[2]/div/div[1]'

			# <당일 등록한 경우> ==> 저공해차일수도, 아닐수도 있음
			#   팝업1 : "요청 차량은 당일등록차량입니다. *표지발급은 필요시 저공해차관련 서류를 확인 후 진행하시기 바랍니다."	==> "당일등록차량입니다"

			# <저공해 차량이 아닌 경우>
			# 	팝업1 : "요청하신 차량은 조회결과가 없습니다. 제원번호 입력 후 확인해주세요."									==> "조회결과가 없습니다"
			# 	팝업2 : "요청하신 차량은 저공해차 차량이 아닙니다.(제원번호미존재)"												==> "저공해차 차량이 아닙니다"
			#   팝업3 : "2020년 4월 3일 부터 법개정으로 인하여 경유를 연료로 하는 자동차는 저공해차에서 제외되었습니다."		==> "저공해차에서 제외되었습니다"
			#   팝업4: "요청하신 차량의 저공해차 제원정보가 없습니다. 제조사에 문의해주시기 바랍니다."							==> "저공해차 제원정보가 없습니다"
			# 	팝업5 : "차대번호 또는 차량등록번호를 입력해주세요."
			# <저공해 차량인데 1개만 넣은 경우>
			# 	팝업1 : "차량등록번호를 입력해주세요."
			# 	팝업2 : "차대번호를 입력해주세요."
			# <사이트 내부 오류인 경우>
			#   팝업1 : "표지발급정보 조회 중 오류가 발생하였습니다. ~~오류내용~~"												==> "오류가 발생하였습니다"
			#""" 예를 들면
			#표지발급정보 조회 중 오류가 발생하였습니다.
			#SqlMapClient operation; SQL [];
			#--- The error occurred in sqlmap/lcvi/I010001000EV.xml.
			#--- The error occurred while applying a parameter map.
			#--- Check the lcvi.01.00.010.ev.getFuelcd-InlineParameterMap.
			#--- Check the statement (query failed).
			#--- Cause: java.sql.SQLRecoverableException: 소켓에서 읽을 데이터가 없습니다; nested exception is com.ibatis.common.jdbc.exception.NestedSQLException:
			#--- The error occurred in sqlmap/lcvi/I010001000EV.xml.
			#--- The error occurred while applying a parameter map.
			#--- Check the lcvi.01.00.010.ev.getFuelcd-InlineParameterMap.
			#--- Check the statement (query failed).
			#--- Cause: java.sql.SQLRecoverableException: 소켓에서 읽을 데이터가 없습니다
			#"""

			#############################################################
			# [팝업창 처리] 
			# 긴급공지 : "당일등록차량이거나 저공해차대상이 아닙니다." ==> 당일등록 차량에 대해 무조건 팝업 나옴 ==> 무시
			# "내용" : '//*[@id="layerPop2"]/div/div[2]/div/div[1]'
			# "확인" : '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a'
			# 0.8버전 : 원래 0.7까지는 6초 기다림 ==> 8초 걸린다면 팝업 뜨기 전에 인증번호(=self.auth_num)를 찾으므로 self.auth_num == ""
			#           ==> 저공해차 아님으로 판별됨 ==> 0.8버전에서 10초로 더 길게 기다림
			alert_button = WebDriverWait(self.browser, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a')))
			alert_message = self.browser.find_element(By.XPATH, '//*[@id="layerPop2"]/div/div[2]/div/div[1]').text
			print(f"[저공해 확인] 오류 팝업 메시지: {alert_message} \t 길이: {len(alert_message)}")		# 메시지와 메시지의 길이
			alert_button.click()
			time.sleep(1)

		# Case2. 10초 timeout 결과 안 나온 경우
		except TimeoutException as err:
			print(err)
			self.eco_process_message = "저공해차 확인 중 제한시간(10초)이 초과되었습니다\n"
			self.browser.close()
			self.browser.quit()
			self.eco_process_done = True
			self.eco_process_success = False
			return

		#except (NoSuchElementException, ElementNotInteractableException) as err:
		except Exception as err:
			#print(sys.exc_info()[1])																		# 디버깅용1
			#import traceback
			#traceback.print_exception(etype=sys.last_type,value=sys.last_value,tb=sys.last_traceback)		# 디버깅용2
			print(err)																						# 디버깅용3
			self.eco_process_message = f"저공해차 확인 중 Timeout 외의 오류({err})가 발생하였습니다\n"
			self.browser.close()
			self.browser.quit()
			self.eco_process_done = True
			self.eco_process_success = False
			return

		# 당일등록 차량입니다 ==> 저공해차 정보가 나오면 에러메시지 내보낼 필요 없음 / 저공해차 정보가 안 나오면 에러메시지에 "당일등록차량 + 제원정보 없음"
		if "당일등록차량입니다" in alert_message:
			#self.eco_process_message += "당일등록차량의 저공해차 정보가 없습니다"
			self.eco_process_message += "당일등록차량입니다\n"
		# 저공해차 아닌 경우
		if "저공해차 제원정보가 없습니다" in alert_message:
			self.eco_process_message += "저공해차 제원정보가 없습니다\n"
		if ("조회결과가 없습니다" in alert_message):
			self.eco_process_message += "저공해 차량 조회결과가 없습니다\n"
		if ("저공해차 차량이 아닙니다" in alert_message):
			self.eco_process_message += "저공해 차량이 아닙니다\n"
		if ("저공해차에서 제외되었습니다" in alert_message):
			self.eco_process_message += "경유차는 저공해차에서 제외되었습니다\n"
		# 사이트 내부 오류 발생한 경우
		if ("오류가 발생하였습니다" in alert_message):
			self.eco_process_message += "사이트 내부 오류가 발생하였습니다\n"
		

		
		# 조회결과 : 저공해 차량은 "인증번호" 나옴 / 저공해 차량이 아닌 경우 self.auth_num = ""
		self.auth_num = self.browser.find_element(By.XPATH, '//*[@id="CRTF_NO"]').text.strip()		# 인증번호
		self.eco_class = self.browser.find_element(By.XPATH, '//*[@id="ECO_NO"]').text.strip()		# O종
		

		# 인증번호 확인 ==> 저공해차량 아닌 경우
		#if (self.auth_num == "") or (self.eco_class not in ["1종", "2종", "3종"]):
		if self.auth_num == "":
			print("저공해차량의 인증번호가 확인되지 않습니다.")
			self.eco_process_message += "+ 저공해차량의 인증번호가 확인되지 않습니다"
			# 실패 + 로그아웃 버튼 클릭
			#logout_btn = WebDriverWait(self.browser, 1).until(EC.presence_of_element_located((By.XPATH, '//*[@id="wrap"]/div[2]/div/div/div/ul/li[2]/a')))
			logout_btn = self.browser.find_element(By.XPATH, '//*[@id="wrap"]/div[2]/div/div/div/ul/li[2]/a')
			logout_btn.click()
			self.browser.close()
			self.browser.quit()
			self.eco_process_done = True
			self.eco_process_success = False
			return
		
		# 저공해 정보 뜬 경우 ==> "발급" 버튼 클릭
		# 표지발급 / 재발급 버튼 XPATH	: '//*[@id="btnCvisu"]'
		print("[저공해 확인] 저공해 정보 확인되었습니다.")
		self.browser.find_element(By.XPATH, '//*[@id="btnCvisu"]').click()


		# Case1. 정상적으로 "표지발급이 완료되었습니다." 팝업창 기다림 ==> 닫기
		# 팝업창 확인 버튼	: '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a'
		try:
			alert_button = WebDriverWait(self.browser, 2).until(EC.presence_of_element_located((By.XPATH, '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a')))
			self.browser.execute_script("arguments[0].click();", alert_button)
			print("[스티커 발급 성공] 표지가 정상적으로 발급되었습니다.")

		# Case2. 비정상적으로 팝업창이 안 뜬 경우(발급시간 초과)
		# 팝업창이 안 떴다 하더라도 발급은 되었을 수 있다. ==> 발급번호 길이 확인
		except :
			pass
		
		# 등급 		: '//*[@id="ECO_NO"]'			# 1종
		# 차모델	: '//*[@id="CAR_NM"]'			# EV6	깨진문자 #40; = (	깨진문자 #41; = )
		# 사용연료	: '//*[@id="USEFUELNM"]'		# 전기
		# 소유자 	: '//*[@id="OWNER_NM"]'			# 김OO
		# 등록번호 	: '//*[@id="CAR_REGIST_NO"]'	# 55루2327
		# 발급횟수	: '//*[@id="ISSU_CNT"]'			# 0 1 ...
		# 발급번호 	: '//*[@id="CVISU_NO"]'			# 20210902-1068577
		# 인증번호	: '//*[@id="CRTF_NO"]'			# MMY-KM-13-05	==> 저공해차량 조건 : string[8] in [1,2,3]
		self.eco_class = self.browser.find_element(By.XPATH, '//*[@id="ECO_NO"]').text.strip()
		self.car_name = self.browser.find_element(By.XPATH, '//*[@id="CAR_NM"]').text.strip()
		self.fuel_type = self.browser.find_element(By.XPATH, '//*[@id="USEFUELNM"]').text.strip()
		self.owner_name = self.browser.find_element(By.XPATH, '//*[@id="OWNER_NM"]').text.strip()
		self.reg_num = self.browser.find_element(By.XPATH, '//*[@id="CAR_REGIST_NO"]').text.strip()
		self.issue_count = self.browser.find_element(By.XPATH, '//*[@id="ISSU_CNT"]').text.strip()
		self.issue_num = self.browser.find_element(By.XPATH, '//*[@id="CVISU_NO"]').text.strip()		# 저공해차 ==> 발급번호 나옴

		# 발급 성공
		if len(self.issue_num) == 16:
			self.eco_process_success = True
		# 발급 실패
		else:
			self.eco_process_success = False
		
		logout_btn = self.browser.find_element(By.XPATH, '//*[@id="wrap"]/div[2]/div/div/div/ul/li[2]/a')
		logout_btn.click()
		self.browser.close()
		self.browser.quit()
		self.eco_process_done = True
		return


################################################################################
## class EcoSticker : 저공해 스티커 발급 메인루틴 클래스
## 		- reset_all()		: (발급 성공/실패 후) 재초기화
##		- automate()		: 발급 전체 과정 총괄
##	 		- get_car_info()	: 자동차 등록번호/차대번호 입력 총괄
##				- regnum_copied()	: 등록번호 입력 확인
##				- vin_copied()		: 차대번호 입력 확인
##			- get_eco_info()	: 쓰레드로부터 발급사이트의 저공해 정보 얻어옴
##			- display_result()	: 발급결과 화면
##		- on_btn_click()	: 발급 버튼 event handler
##		- win_shake()		: 창 흔들기
################################################################################
class EcoSticker:
	#########################################################
	# 생성자(초기화)
	def __init__(self):
		# Tk윈도 생성
		self.root = Tk()
		self.root.iconbitmap(r"res\car_icon.ico")
		self.root.title(f"저공해차량 스티커 자동발급 시스템 Ver.{VER} (90초 Edition)")	# 공지/팝업이 뜨거나 말거나 오류 안 나게 수정(0.53) 차대끝2숫자(0.54)
		self.root.geometry(f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}+{WIN_POS_X}+{WIN_POS_Y}")
		self.root.resizable(False, False)
		self.root.wm_attributes("-topmost", True)
		self.root.wm_attributes("-topmost", False)

		# 배경 이미지 + 버튼 이미지 : (경로설정은 r string : file=r"res\bg_nature.png")
		#self.img_bg0 = PhotoImage(file=r"res\bg_field_sky.png")		# 기본 배경(자연)
		self.img_bg0 = PhotoImage(file=r"res/bg_field_sky.png")		# 기본 배경(자연)
		self.img_e1 = PhotoImage(file=r"res/e1_half_cover.png")		# 1종 스티커
		self.img_e2 = PhotoImage(file=r"res/e2_half_cover.png")		# 2종 스티커
		self.img_e3 = PhotoImage(file=r"res/e3_half_cover.png")		# 3종 스티커
		self.img_btn = PhotoImage(file=r"res/text_button.png")		# 발급 버튼 : 178x84
		self.img_bg_wait = PhotoImage(file=r"res/wait.png")			# 대기 화면
		self.img_loader_frames = [PhotoImage(file=f"res/loader/frame-{i}.png") for i in range(1, 35+1)]		# 파일:1~35, frame:0~34

		# 기본캔버스 생성 + 기본이미지 붙임
		self.canvas = Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white', bd=0, highlightthickness=0)
		self.canvas_img_id = self.canvas.create_image(0, 0, image=self.img_bg0, anchor="nw")	# id = 1
		self.canvas.pack(fill="both", expand=True)

		# 기본캔버스 + 발급 버튼 
		# borderwidth=3, relief="flat" / "groove"
		self.btn = Button(self.root, image=self.img_btn, borderwidth=1)
		self.btn.bind("<ButtonRelease-1>", self.on_btn_click)		# 누를 때는 "<Button-1>"
		self.btn.configure(width=178, height=84, activebackground="#FFFFFF")
		self.btn_ID = self.canvas.create_window(250, 90, anchor="c", window=self.btn)
		self.btn["state"] = DISABLED

		# 처리중입니다.		
		self.label_loader = Label(self.root, bg="#84C3EF")
		self.canvas.create_window(CANVAS_WIDTH/2, CANVAS_HEIGHT/2 + 20, anchor="c", window=self.label_loader)
		self.label_loader.lower()

		# 기본캔버스 + 텍스트
		self.canvas_text_issuenum_id = self.canvas.create_text(X_POS_ISSUENUM, Y_POS_ISSUENUM, font=("Malgun Gothic", 20, "bold"), anchor="nw", text="")
		self.canvas_text_regnum_id = self.canvas.create_text(X_POS_REGNUM, Y_POS_REGNUM, font=("Malgun Gothic", 20, "bold"), anchor="nw", text="")
		self.canvas_text_count_id = self.canvas.create_text(X_POS_REGNUM + 150, Y_POS_REGNUM + 65, font=("Malgun Gothic", 12), fill="yellow", anchor="nw", text="")

		#self.canvas_text_processing_id = self.canvas.create_text(255, 70, fill="#1c0d9f", font=("Malgun Gothic", 28, "bold"), anchor="c", text="")		# 처리중입니다.
		#self.canvas_text_plzwait_id = self.canvas.create_text(250, 320, fill="#626288", font=("Malgun Gothic", 15, "bold"), anchor="c", text="")		# 잠시만 기다려주세요.

		# 클립보드 저장용 변수 초기화
		self.regnum_pattern = re.compile("(서울)?[0-9]{2,3}[가-힣][0-9]{4}")	# 차량등록번호(자가용+영업용)
		self.vin_pattern = re.compile("[0-9A-Z]{17}")  					# 17자리 차대번호(15자리 영문자/숫자 + 2자리 숫자)
		
		self.vin_entered = ""
		self.regnum_entered = ""

		# 상태변수
		self.new_regnum = False
		self.car_info_entered = False
		self.thread_working = False

		# 저공해 차량인 경우 저공해 정보
		self.eco_class = ""
		self.car_name = ""
		self.fuel_type = ""
		self.owner_name = ""
		self.reg_num = ""
		self.issue_count = ""
		self.issue_num = ""

		# 쓰레드 생성
		self.web_agent = WebAgentThread()

		# 총괄함수
		self.automate()

		# Tk 윈도 메인루프
		self.root.mainloop()

	#########################################################
	# 발급/발급취소 단계 후 초기화 함수
	def reset_all(self):

		# 캔버스 초기화
		self.canvas.itemconfig(self.canvas_img_id, image=self.img_bg0)

		self.canvas.itemconfig(self.canvas_text_issuenum_id, text="")	# 발급번호 초기화
		self.canvas.itemconfig(self.canvas_text_regnum_id, text="")		# 등록번호 초기화
		self.canvas.itemconfig(self.canvas_text_count_id, text="")		# 몇초남았음 초기화

		#self.canvas.itemconfig(self.canvas_text_processing_id, text="")	# 처리중입니다 초기화
		#self.canvas.itemconfig(self.canvas_text_plzwait_id, text="")	# 잠시만 기다려주세요 초기화

		# 버튼 초기화
		self.btn.lift()
		self.btn["state"] = DISABLED

		# 대기 loader 초기화
		self.label_loader.configure(image=None)
		self.label_loader.lower()

		# 클립보드 변수 초기화
		self.regnum_entered = ""
		self.vin_entered = ""

		# 상태변수
		self.new_regnum = False
		self.car_info_entered = False
		self.thread_working = False

		# 저공해 차량인 경우 저공해 정보
		self.eco_class = ""
		self.car_name = ""
		self.fuel_type = ""
		self.owner_name = ""
		self.reg_num = ""
		self.issue_count = ""
		self.issue_num = ""

		# 쓰레드 객체 삭제 후 생성
		self.web_agent.join()
		del self.web_agent
		self.web_agent = WebAgentThread()

		# 항상 맨 위
		self.root.wm_attributes("-topmost", True)
		self.root.wm_attributes("-topmost", False)
		self.root.update()

	#########################################################
	# 소멸자(자원해제)
	def __del__(self):
		if self.web_agent.is_alive() == True:
			self.web_agent.join()

	#########################################################
	# 클립보드를 확인하는 함수 : 등록번호 + 차대번호
	def get_car_info(self):
		
		if self.regnum_copied() == True:			# 차량등록번호 확인
			if self.new_regnum == True:
				self.win_shake(horizontal=False)	# 고개 상하 끄덕끄덕
			
			if self.vin_copied() == True:			# 차대번호 확인
				#self.win_shake(horizontal=False)	# 고개 상하 끄덕끄덕
				self.car_info_entered = True
				return True
		
		self.car_info_entered = False
		return False

	#########################################################
	# 차량등록번호 확인 함수
	def regnum_copied(self):
		# 이미 차량등록번호가 입력되었다면 ==> return True
		if self.regnum_entered != "":
			self.new_regnum = False
			return True

		current_clipboard = pyperclip.paste().strip()
		match_result = self.regnum_pattern.match(current_clipboard)

		if (match_result is not None) and (len(current_clipboard) == len(match_result.group())):	# 차량등록번호가 맞으면
			print("[클립보드 감시] 차량등록번호를 발견하였습니다.")
			self.regnum_entered = current_clipboard
			self.new_regnum = True
			
			self.root.wm_attributes("-topmost", True)
			self.root.wm_attributes("-topmost", False)
			self.root.update()

			return True
		else:
			print("[클립보드 감시] 차량등록번호 형식이 아닙니다.")
		
		return False


	#########################################################
	# 차대번호 확인 함수
	def vin_copied(self):
		# 차대번호 입력에 5초 ==> 초과하면 차량등록번호까지 초기화
		try:
			current_clipboard = pyperclip.waitForNewPaste(5).strip()
		except pyperclip.PyperclipTimeoutException:
			print("[차대번호 입력시간 초과] 입력을 모두 초기화합니다.")
			self.regnum_entered = ""
			pyperclip.copy("")
			self.win_shake(horizontal=True)		# 고개 좌우 흔들기
			return False

		match_result = self.vin_pattern.match(current_clipboard)

		if (match_result is not None) and (len(current_clipboard) == len(match_result.group())):	# 차대번호가 맞으면
			print("[클립보드 감시] 차대번호를 발견하였습니다.")
			self.vin_entered = current_clipboard

			self.root.wm_attributes("-topmost", True)
			self.root.wm_attributes("-topmost", False)
			self.root.lift()
			self.root.update()

			return True
		else:
			print("[클립보드 감시] 차대번호 형식이 아닙니다.")
		
		return False


	#########################################################
	# 발급결과 출력 함수
	def display_result(self, countdown):
		# 로더 내리고
		self.label_loader.lower()

		# 글자 내리고
		#self.canvas.itemconfig(self.canvas_text_processing_id, text="")
		#self.canvas.itemconfig(self.canvas_text_plzwait_id, text="")
		#self.root.update()

		# 저공해 종별에 따라 캔버스 배경이미지 변신
		if self.eco_class == "1종":
			self.canvas.itemconfig(self.canvas_img_id, image=self.img_e1)

		elif self.eco_class == "2종":
			self.canvas.itemconfig(self.canvas_img_id, image=self.img_e2)

		elif self.eco_class == "3종":
			self.canvas.itemconfig(self.canvas_img_id, image=self.img_e3)
		self.root.update()

		# countdown(초) 동안 화면 계속 출력
		while countdown > 0:
			self.canvas.itemconfig(self.canvas_text_issuenum_id, text=self.issue_num)
			self.canvas.itemconfig(self.canvas_text_regnum_id, text=self.reg_num)
			self.canvas.itemconfig(self.canvas_text_count_id, text=f"{countdown}초 후 닫습니다")
			self.canvas.update()
			time.sleep(1)
			countdown -= 1

	#########################################################
	# 쓰레드에서 저공해 정보 가져오는 함수
	def get_eco_info(self):
		self.reg_num = self.web_agent.reg_num
		self.issue_num = self.web_agent.issue_num
		
		self.eco_class = self.web_agent.eco_class
		self.car_name = self.web_agent.car_name
		self.fuel_type = self.web_agent.fuel_type
		self.owner_name = self.web_agent.owner_name
		self.issue_count = self.web_agent.issue_count
		self.issue_num = self.web_agent.issue_num

	#########################################################
	# 총괄 callback함수
	def automate(self):
		retry = False	# 한번 더 조회
		
		if self.car_info_entered == False:
			# 새로운 등록번호/차대번호 복사되었다면
			if self.get_car_info() == True:
				self.btn["state"] = NORMAL		# 발급 버튼 활성화
			
			# 새로운 차대번호가 복사되지 않은 경우
			else:
				self.btn["state"] = DISABLED	# 발급 버튼 비활성화
		
		# 쓰레드 시작(발급버튼 눌림)
		if self.thread_working == True:

			while self.web_agent.eco_process_done == False:
				# 대기 캔버스
				self.canvas.itemconfig(self.canvas_img_id, image=self.img_bg_wait)
				#self.canvas.itemconfig(self.canvas_text_processing_id, text="처리중입니다...")
				#self.canvas.itemconfig(self.canvas_text_plzwait_id, text="잠시만 기다려주세요")
				self.label_loader.lift()
				self.root.update()
				print("[쓰레드 실행중] 대기화면 캔버스 상태")

				# 로딩화면 보여주기
				for current_frame in self.img_loader_frames:
					if self.web_agent.eco_process_done == True:
						break
					self.label_loader.configure(image=current_frame)
					self.root.update()
					time.sleep(0.03)
					print(self.web_agent.eco_process_done)		# 디버그용

			# 쓰레드에서 발급 성공
			if self.web_agent.eco_process_success == True:
				self.get_eco_info()					# 쓰레드에서 저공해 정보 얻어옴
				self.display_result(countdown=90)	# 50초간 발급 결과 화면 보여주기

			# 쓰레드에서 발급 실패
			else:
				self.root.wm_attributes("-topmost", True)
				self.root.update()
				print("[저공해 발급] 오류 발생")
				response = messagebox.askretrycancel("발급 실패", "발급 실패 사유:\n" + self.web_agent.eco_process_message + "\n한번 더 확인하시려면 '다시 시도' 클릭\n처음으로 돌아가시려면 '취소' 클릭")
				self.root.wm_attributes("-topmost", False)
				if response == True:
					# 재시도 = True
					retry = True

					# 쓰레드 죽이고 + 다시 생성 + 쓰레드 시작
					self.web_agent.join()
					del self.web_agent
					self.web_agent = WebAgentThread()
					self.web_agent.setCarInfo(reg_num=self.regnum_entered, vin_num=self.vin_entered)
					self.web_agent.start()

			# 발급 성공이든 실패든 초기화 
			# But 재시도 ==> reset 안함
			if retry == False:
				self.reset_all()
		
		# 0.5초 후 timer event로 callback
		self.root.after(500, self.automate)


	#########################################################
	# 발급버튼 클릭 이벤트 처리 함수
	def on_btn_click(self, event):

		# 버튼 비활성화 상태는 무시
		if self.btn["state"] == DISABLED:
			print("버튼 비활성화 상태입니다.")
		
		# 버튼이 "normal" 또는 "active"
		else:
			# 버튼 활성화 ==> 비활성화
			self.btn["state"] = DISABLED
			self.root.update()
			time.sleep(0.5)
			self.btn.lower()

			# 쓰레드에 차량등록번호/차대번호 입력
			self.web_agent.setCarInfo(reg_num=self.regnum_entered, vin_num=self.vin_entered)

			# 쓰레드 시작
			self.thread_working = True
			self.web_agent.start()
		
	#########################################################
	# 윈도 흔들기 : horizontal=True이면 좌우방향, False이면 상하방향
	def win_shake(self, horizontal=True):

		# 윈도 창 맨 앞 활성화
		self.root.wm_attributes("-topmost", True)
		self.root.wm_attributes("-topmost", False)

		# 창이 최소화 상태라면 원래대로 restore
		if self.root.state() == "iconic":
			self.root.deiconify()
			time.sleep(0.5)

		# 흔드는 횟수
		total_times = 30
		this_time = total_times

		##################################################
		# 창 위치 조정 : 함수 호출 최소화하기 위한 변수
		pos_x = self.root.winfo_x()
		pos_y = self.root.winfo_y()
		width = self.root.winfo_width()
		height = self.root.winfo_height()
		screen_width = self.root.winfo_screenwidth()
		screen_height = self.root.winfo_screenheight()

		# 화면을 벗어난 경우 ==> 화면 안쪽으로 이동
		if pos_x <= 0:								# 왼쪽 바깥
			pos_x = 20
		if (pos_x + width + 10) >= screen_width:	# 오른쪽 바깥
			pos_x = screen_width - width - 20
		if pos_y <= 0:								# 위쪽 바깥
			pos_y = 20
		if (pos_y + height + 80) >= screen_height:	# 아래쪽 바깥(작업표시줄 감안)
			pos_y = screen_height - height - 80
		self.root.geometry(f"+{pos_x}+{pos_y}")
		self.root.update()
		##################################################

		# 진폭 한계
		amp_max_x = min(min(screen_width - pos_x - width, pos_x), 10)
		amp_max_y = min(min(screen_height - pos_y - height, pos_y), 10)

		# 흔들기
		while this_time > 0:
			# 방향에 따라 delta값 설정
			if horizontal == True:
				delta_x = round(amp_max_x*sin(0.5*pi*this_time/total_times))
				delta_y = 0
			else:
				delta_x = 0
				delta_y = round(amp_max_y*sin(0.5*pi*this_time/total_times))

			# + delta만큼 이동
			self.root.geometry(f"+{pos_x + delta_x}+{pos_y + delta_y}")
			self.root.update()
			time.sleep(0.001)

			# - 2*delta만큼 이동
			self.root.geometry(f"+{pos_x - 2*delta_x}+{pos_y - 2*delta_y}")
			self.root.update()
			time.sleep(0.001)

			# 다시 +delta만큼 이동
			self.root.geometry(f"+{pos_x + delta_x}+{pos_y + delta_y}")
			self.root.update()
			time.sleep(0.001)

			this_time -= 1

		self.root.geometry(f"{width}x{height}+{pos_x}+{pos_y}")
		self.root.update()


################################################################################
## class LoginAgent : 메시지 윈도에서 인증정보(ID/PW) 입력받기
## 		- check_login()	: 입력된 ID/PW로 로그인 검증하는 버튼(핸들러)
##		- login_test()	: 쓰레드로 실제 로그인 수행하는 함수
################################################################################
class LoginAgent:
	def __init__(self):

		# 접속 성공 flag
		self.login_success = False
		self.autologin = True

		# Tk 윈도 생성
		self.root = Tk()
		self.root.iconbitmap(r'res\car_icon.ico')
		self.root.geometry(f"292x90+{int((self.root.winfo_screenwidth()-self.root.winfo_width())/2-100)}+{int((self.root.winfo_screenheight()-self.root.winfo_height())/2-100)}")
		self.root.title("관리자 로그인")
		self.root.resizable(False, False)
		self.root.wm_attributes("-topmost", True)
		self.root.wm_attributes("-topmost", False)
	
		# 아이디 / 비밀번호 텍스트 라벨
		self.label_ID = Label(self.root, text=" 아이디 ")
		self.label_ID.grid(row=0, column=0, sticky=W, padx=2, pady=4)
		self.label_PW = Label(self.root, text=" 비밀번호 ")
		self.label_PW.grid(row=1, column=0, sticky=W, padx=2, pady=4)

		# 아이디 / 비밀번호 입력칸
		self.entry_ID = Entry(self.root)
		self.entry_ID.grid(row=0, column=1, pady=0)
		self.entry_PW = Entry(self.root)
		self.entry_PW.grid(row=1, column=1, pady=0)
		self.entry_PW.bind("<Return>", self.check_login)	# PW입력칸에서 ENTER 눌러도 버튼 누른 효과

		# 로그인 버튼(이미지)
		self.img_btn = PhotoImage(file=r"res\login_button.png")
		self.btn_login = Button(self.root, image=self.img_btn, borderwidth=1, relief=RAISED)
		self.btn_login.bind("<Button-1>" , self.check_login)
		self.btn_login.grid(row=0, column=2, columnspan=2, rowspan=2, padx=4, pady=4)

		# "자동 로그인" 체크버튼
		self.VarCheckBtn = IntVar()
		self.checkbtn_login = Checkbutton(self.root, text = " 자동 로그인", variable=self.VarCheckBtn, onvalue=True, offvalue=False, state=DISABLED)
		self.checkbtn_login.grid(row=2, column=0, sticky="s", rowspan=2, columnspan=2, padx=4, pady=2)
		self.VarCheckBtn.set(True)

		# ID부분에 포커스
		self.entry_ID.focus()

		# TK윈도 무한루프
		self.root.mainloop()

	def check_login(self, event):
		# 버튼 비활성화 상태는 무시
		if self.btn_login["state"] == DISABLED:
			print("버튼 비활성화 상태입니다.")
		
		# 버튼이 "normal" 또는 "active"
		else:
			self.entry_ID["state"] = DISABLED
			self.entry_PW["state"] = DISABLED
			
			self.btn_login.config(relief=SUNKEN)
			self.btn_login.update()
			time.sleep(0.25)
			self.btn_login.config(relief=RAISED)
			self.btn_login.update()
			time.sleep(0.1)
			self.btn_login["state"] = DISABLED
			self.btn_login.update()
			
			# 브라우저가 login 성공시
			if self.login_test() == True:
				self.login_success = True
				
				global AUTHENTICATION_SUCCESS
				AUTHENTICATION_SUCCESS = True
				
				global ADMIN_ID
				ADMIN_ID = self.entry_ID.get().strip()
				global ADMIN_PW
				ADMIN_PW = self.entry_PW.get().strip()

				self.root.destroy()

			else:
				self.login_success = False
				self.win_shake(horizontal=True)
				
				self.entry_ID["state"] = NORMAL
				self.entry_PW["state"] = NORMAL
				self.btn_login["state"] = NORMAL
				self.btn_login.config(relief=RAISED)
				self.root.update()

				self.entry_ID.delete(0, END)
				self.entry_PW.delete(0, END)
				
				self.root.lift()
				self.root.update()
				self.entry_ID.focus()

	
	def login_test(self):
		# 쓰레드 생성
		login_thread = WebAgentThread(login_test=True, testID=self.entry_ID.get().strip(), testPW=self.entry_PW.get().strip())
		login_thread.start()

		while login_thread.login_test_success == None:
			time.sleep(0.1)

		#login_thread.join()
		return login_thread.login_test_success


	#########################################################
	# 윈도 흔들기 : horizontal=True이면 좌우방향, False이면 상하방향
	def win_shake(self, horizontal=True):
		total_times = 40
		this_time = total_times

		##################################################
		# 창 위치 조정 : 함수 호출 최소화하기 위한 변수
		pos_x = self.root.winfo_x()
		pos_y = self.root.winfo_y()
		width = self.root.winfo_width()
		height = self.root.winfo_height()
		screen_width = self.root.winfo_screenwidth()
		screen_height = self.root.winfo_screenheight()

		# 화면을 벗어난 경우 ==> 화면 안쪽으로 이동
		if pos_x <= 0:								# 왼쪽 바깥
			pos_x = 20
		if (pos_x + width + 10) >= screen_width:	# 오른쪽 바깥
			pos_x = screen_width - width - 20
		if pos_y <= 0:								# 위쪽 바깥
			pos_y = 20
		if (pos_y + height + 80) >= screen_height:	# 아래쪽 바깥(작업표시줄 감안)
			pos_y = screen_height - height - 80
		self.root.geometry(f"+{pos_x}+{pos_y}")
		self.root.update()
		##################################################

		# 진폭 한계
		amp_max_x = min(min(screen_width - pos_x - width, pos_x), 10)
		amp_max_y = min(min(screen_height - pos_y - height, pos_y), 10)

		# 흔들기
		while this_time > 0:
			# 방향에 따라 delta값 설정
			if horizontal == True:
				delta_x = round(amp_max_x*sin(0.5*pi*this_time/total_times))
				delta_y = 0
			else:
				delta_x = 0
				delta_y = round(amp_max_y*sin(0.5*pi*this_time/total_times))

			# + delta만큼 이동
			self.root.geometry(f"+{pos_x + delta_x}+{pos_y + delta_y}")
			self.root.update()
			# - 2*delta만큼 이동
			self.root.geometry(f"+{pos_x - 2*delta_x}+{pos_y - 2*delta_y}")
			self.root.update()
			# 다시 +delta만큼 이동
			self.root.geometry(f"+{pos_x + delta_x}+{pos_y + delta_y}")
			self.root.update()

			this_time -= 1

		self.root.geometry(f"+{pos_x}+{pos_y}")
		self.root.update()


################################################################################
## class LoadAuthInfo : 파일에서 인증정보(ID/PW) 추출
## 		- get_auth_from_file()	: 파일에서 인증정보 가져오기
##		- save_auth_to_file()	: 검증된 인증정보를 파일로 저장
################################################################################
class LoadAuthInfo:
	# 초기화
	def __init__(self):
		self.key = base64.urlsafe_b64encode((AUTH_DEFAULT_KEY.encode("utf-8")))		# encode 결과 = b'EcoSticker2021 by Kim Jae Hyoung'
		self.fernet = Fernet(self.key)

		self.ID = ""
		self.PW = ""
		self.file_exists = False
		self.load_auth_success = False

		self.get_auth_from_file()

	# 인증정보 파일로부터 ID, PW 추출 (이미 자동로그인으로 저장된 정보)
	def get_auth_from_file(self):
		try:
			with open(AUTH_FILE, "rb") as file:
				file_contents = file.read()
				self.file_exists = True

				self.ID = self.fernet.decrypt(file_contents[:100]).decode("utf-8")		# ID 추출 (100byte)
				self.PW = self.fernet.decrypt(file_contents[100:]).decode("utf-8")		# PW 추출 (100byte)

		except (FileNotFoundError, OSError) as e:
			print("[인증파일 읽기] 경로나 파일이 없거나 읽을 수 없습니다.")
			self.file_exists = False
			return

		except (TypeError, InvalidToken, UnicodeDecodeError) :
			print("[인증파일 손상] 파일의 인증정보를 복호화 할 수 없어 파일을 삭제합니다.")
			os.remove(AUTH_FILE)
			self.file_exists = False
			return
		
		# 파일 읽고/decrypt/decode하는 동안 오류가 발생하지 않았다면 ==> 로그인 테스트
		login_thread = WebAgentThread(login_test=True, testID=self.ID, testPW=self.PW)
		login_thread.start()

		while login_thread.login_test_success == None:
			time.sleep(0.5)

		# 쓰레드가 login에 성공한 경우
		if login_thread.login_test_success == True:
			self.load_auth_success = True

			# 전역변수에 ID/PW 저장
			global ADMIN_ID
			ADMIN_ID = self.ID
			global ADMIN_PW
			ADMIN_PW = self.PW

			# 전역변수에 인증 성공 저장
			global AUTHENTICATION_SUCCESS
			AUTHENTICATION_SUCCESS = True

		# 쓰레드가 login에 실패한 경우
		else:
			print("파일의 인증정보로 로그인에 실패하여 파일을 삭제합니다.")
			os.remove(AUTH_FILE)
			self.file_exists = False

			self.load_auth_success = False
		
		return

	# ID, PW 인증정보를 파일에 저장 (자동로그인 체크하여 처음 로그인한 경우)
	def save_auth_to_file(self, id, pw):
		id_encrypted = self.fernet.encrypt(id.encode("utf-8"))	# id 암호화 (길이=100byte)
		pw_encrypted = self.fernet.encrypt(pw.encode("utf-8"))	# pw 암호화 (길이=100byte)

		try:
			with open(AUTH_FILE, "wb") as file:	# 이미 파일이 존재하는 경우 ==> 파일 지움(에러 없음)
				file.write(id_encrypted)
				file.write(pw_encrypted)

		except OSError as e:
			print("[인증파일 저장] 인증정보를 파일에 저장 중 에러가 발생하였습니다.")
			return False

		return True		# 성공


################################################################################
## 메인 함수
## 		- auth	: 파일에서 인증정보 가져오기
##		- login	: 파일에서 인증정보 추출 실패한 경우 ID/PW 입력창
## 			- 브라우저로 로그인 성공시 ==> 파일에 인증정보 저장
##		- ecoSticker : 항상 떠 있는 실질적인 핵심로직 윈도
################################################################################
if __name__ == '__main__':

	# 파일로부터 인증정보 확인
	auth = LoadAuthInfo()

	# 인증정보 확인 안된 경우 ==> 로그인 메시지박스로 ID/PW 입력
	if auth.load_auth_success == False:
		login = LoginAgent()

	# 파일이든 입력이든 인증 성공시 ==> 저공해차량 스티커 발급모드
	if AUTHENTICATION_SUCCESS == True:
		
		# 인증파일 없었거나/손상되었거나/로그인 실패한 경우 ==> 인증정보 파일로 저장
		if auth.file_exists == False:
			auth.save_auth_to_file(ADMIN_ID, ADMIN_PW)

		ecoSticker = EcoSticker()
	else:
		sys.exit(0)		# 정상 종료
