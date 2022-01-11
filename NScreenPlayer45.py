import re
import time
import sys
import base64
import pyperclip
from math import *
from threading import *
from cryptography.fernet import Fernet 		# 암호화 패키지
from tkinter import *
from tkinter import messagebox

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from urllib3.exceptions import NewConnectionError
from selenium.common.exceptions import TimeoutException, NoSuchElementException

CANVAS_WIDTH = 500
CANVAS_HEIGHT = 540

WIN_POS_X = 1350
WIN_POS_Y = 150

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

HOME_PATH = r"C:\EcoSticker"
SESSION_INFO_PATH = HOME_PATH + r"\session_info"
CHROMEDRIVER_PATH = HOME_PATH + r"\chromedriver.exe"
AUTH_FILE_PATH = HOME_PATH + r"\Auth.dat"

URL_ADMIN = "https://www.ev.or.kr/lcvms-mncpt/login.do"				# 관리자용 저공해차 발급 사이트
#URL_GUEST = "https://www.ev.or.kr/lcvms-portal/EP020401000SF01.do"	# 일반인용 저공해차 확인 사이트

AUTHENTICATION_SUCCESS = False
AUTH_DEFAULT_KEY = "EcoSticker2021 by Kim Jae Hyoung"		# 길이는 반드시 32byte : base64.urlsafe_b64decode(key)=32
ADMIN_ID = "su0672"
ADMIN_PW = "su0672"

# 자동차 등록번호 정규식 	: '[0-9]{2,3}[가-힣][0-9]{4}'
# 영업용 등록번호 정규식 	: '서울[0-9]{2}[가-힣][0-9]{4}'
# ==> 2개 통합한 정규식 	: '(서울)?[0-9]{2,3}[가-힣][0-9]{4}'


# 로그아웃 버튼 XPATH : '//*[@id="wrap"]/div[2]/div/div/div/ul/li[2]/a'
## 테스트 차대번호 : 일반적으로 17자리 (끝자리 6자리 = 반드시 숫자)
# 1종 : KNAC381AFNA002915 KMHJ8816FNU018004
# 2종 : KNAPV81GBNK000521 KNARF81GBNA068551
# 3종 : KPBXH3AT1NP370787 KMHL341DBNA179522
# *** 독일차 차대번호 : WBA7L7106M7J56681 (끝자리 5개 숫자)
# *** 예외적 차대번호 : 끝자리 4자리만 숫자도 존재함
# *** 발급된 적 없는 차대번호 : KMHE341DBNA616046 (택시)



# 스티커 발급용 쓰레드 함수 : check + issue 통합
class WebAgentThread(Thread):
	# 초기화
	def __init__(self):
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

		self.options = None
		self.browser = None

		self.eco_process_success = False	# 발급 성공/실패
		
		self.getReady()

	# 사이트 접속용 Headless Chrome 생성
	def getReady(self):
		self.options = webdriver.ChromeOptions()
		self.options.add_argument("--headless")		# options.headless = True
		self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko")	# IE인 것처럼
		self.options.add_argument("log-level=2")
		self.options.add_argument("lang=ko_KR")
		self.options.add_experimental_option("excludeSwitches", ["enable-logging"])		# 세션정보 유지
		self.options.add_argument("--user-data-dir=" + SESSION_INFO_PATH)				# 세션정보 저장
		self.browser = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=self.options)

	
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
			#self.browser.implicitly_wait(5)		# 페이지 완전히 로딩될 때까지 최대 5초 기다린다.
		except NewConnectionError as nce:
			print("[로그인 확인] 발급사이트와 연결되지 못했습니다.(연결거부 or 서버장애)")
			self.eco_process_success = False
			return
		
		# 2. 세션 정보 살아있으면 ==> 로그인 과정 불필요
		try:
			# 로그인(id/pw)
			self.browser.find_element_by_id("userId").send_keys(ADMIN_ID)		# ID
			self.browser.find_element_by_id("userPw").send_keys(ADMIN_PW)		# PW
			self.browser.find_element_by_class_name("btn_login.mt20").click()	# 버튼
		except NoSuchElementException:
			print("[저공해 확인] 로그인 생략합니다...")
			pass

		# 3. 발급페이지 웹엘리먼트에 차량등록번호 / 차대번호 입력
		self.browser.find_element_by_xpath('//*[@id="vinNm"]').send_keys(self.vin_num)			# 차대번호 입력
		self.browser.find_element_by_xpath('//*[@id="carRegistNo"]').send_keys(self.reg_num)	# 등록번호 입력
		self.browser.find_element_by_id('btnSearch').click()									# 확인(검색)버튼 클릭
		print("[저공해 확인] 차대입력 후 확인 버튼 클릭!")

		# Case1. 오류 팝업 나오는 경우 ==> 기다렸다가 오류 팝업의 "확인" 버튼 클릭
		try:
			# 오류 팝업의 "확인" 버튼 XPATH : '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a'
			# 오류 팝업의 "내용" XPATH : '//*[@id="layerPop2"]/div/div[2]/div/div[1]'
			# <저공해 차량이 아닌 경우>
			# 	팝업1 : "요청하신 차량은 조회결과가 없습니다. 제원번호 입력 후 확인해주세요."
			# 	팝업2 : "차대번호 또는 차량등록번호를 입력해주세요."
			# 	팝업3 : "요청하신 차량은 저공해차 차량이 아닙니다.(제원번호미존재)"
			# <저공해 차량인데 1개만 넣은 경우>
			# 	팝업1 : "차량등록번호를 입력해주세요."
			# 	팝업2 : "차대번호를 입력해주세요."
			alert_button = WebDriverWait(self.browser, 6).until(EC.presence_of_element_located((By.XPATH, '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a')))
			alert_message = self.browser.find_element_by_xpath('//*[@id="layerPop2"]/div/div[2]/div/div[1]').text
			print("[저공해 확인] 오류 팝업 메시지: {} \t 길이: {}".format(alert_message, len(alert_message)))		# 메시지와 메시지의 길이
			self.browser.execute_script("arguments[0].click();", alert_button)
			
			self.eco_process_success = False
			return

		# Case2. 저공해 차량 맞는 경우 : 사이트의 저공해 정보 추출
		except TimeoutException:
			# 등급 		: '//*[@id="ECO_NO"]'			# 1종
			# 차모델	: '//*[@id="CAR_NM"]'			# EV6	깨진문자 #40; = (	깨진문자 #41; = )
			# 사용연료	: '//*[@id="USEFUELNM"]'		# 전기
			# 소유자 	: '//*[@id="OWNER_NM"]'			# 김OO
			# 등록번호 	: '//*[@id="CAR_REGIST_NO"]'	# 55루2327
			# 발급횟수	: '//*[@id="ISSU_CNT"]'			# 0 1 ...
			# 발급번호 	: '//*[@id="CVISU_NO"]'			# 20210902-1068577
			self.eco_class = self.browser.find_element_by_xpath('//*[@id="ECO_NO"]').text.strip()
			self.car_name = self.browser.find_element_by_xpath('//*[@id="CAR_NM"]').text.strip()
			self.fuel_type = self.browser.find_element_by_xpath('//*[@id="USEFUELNM"]').text.strip()
			self.owner_name = self.browser.find_element_by_xpath('//*[@id="OWNER_NM"]').text.strip()
			self.reg_num = self.browser.find_element_by_xpath('//*[@id="CAR_REGIST_NO"]').text.strip()
			self.issue_count = self.browser.find_element_by_xpath('//*[@id="ISSU_CNT"]').text.strip()

			# 예외적으로 등급 정보가 안 나올 경우 ==> 실패
			if self.eco_class not in ["1종", "2종", "3종"]:
				self.eco_process_success = False
				return
		
		# 저공해 정보 뜬 경우 ==> 정상적인 저공해차 ==> 성공
		print("[저공해 확인] 저공해 정보 확인되었습니다.")

		# 발급버튼 누르기
		# 표지발급 / 재발급 버튼 XPATH	: '//*[@id="btnCvisu"]'
		self.browser.find_element_by_xpath('//*[@id="btnCvisu"]').click()

		# Case1. 정상적으로 "표지발급이 완료되었습니다." 팝업창 기다림 ==> 닫기
		# 팝업창 확인 버튼	: '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a'
		try:
			alert_button = WebDriverWait(self.browser, 2).until(EC.presence_of_element_located((By.XPATH, '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a')))
			self.browser.execute_script("arguments[0].click();", alert_button)
			print("표지가 정상적으로 발급되었습니다.")

		# Case2. 비정상적으로 표지발급 안 된 경우(발급시간 초과)
		except TimeoutException:
			print("[발급사이트 오류] 표지발급 시간이 초과하였습니다.")
			self.eco_process_success = False
			return

		# 정상적으로 발급된 경우 : 발급번호 나옴
		self.issue_num = self.browser.find_element_by_xpath('//*[@id="CVISU_NO"]').text.strip()
		self.eco_process_success = True
		return



class EcoSticker:
	#########################################################
	# 생성자(초기화)
	def __init__(self):
		# Tk윈도 생성
		self.root = Tk()
		self.root.iconbitmap(r"res\car_icon.ico")
		self.root.title("저공해차량 스티커 자동발급 시스템 ver.0.45")
		self.root.geometry(f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}+{WIN_POS_X}+{WIN_POS_Y}")
		self.root.resizable(False, False)
		self.root.wm_attributes("-topmost", True)

		# 배경 이미지 + 버튼 이미지 : (경로설정은 r string : file=r"res\bg_nature.png")
		self.img_bg0 = PhotoImage(file=r"res\bg_field_sky.png")		# 기본 배경(자연)
		self.img_e1 = PhotoImage(file=r"res\e1_half_cover.png")		# 1종 스티커
		self.img_e2 = PhotoImage(file=r"res\e2_half_cover.png")		# 2종 스티커
		self.img_e3 = PhotoImage(file=r"res\e3_half_cover.png")		# 3종 스티커
		self.img_btn = PhotoImage(file=r"res\text_button.png")		# 발급 버튼 : 178x84
		self.img_bg_wait = PhotoImage(file=r"res\wait.png")			# 대기 화면
		self.img_loader_frames = [PhotoImage(file='res/loader/frame-{}.png'.format(i)) for i in range(1, 35+1)]		# 파일:1~35, frame:0~34

		# 기본캔버스 생성 + 기본이미지 붙임
		self.canvas = Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white', bd=0, highlightthickness=0)
		self.canvas_img_id = self.canvas.create_image(0, 0, image=self.img_bg0, anchor="nw")	# id = 1
		self.canvas.pack(fill="both", expand=True)

		# 기본캔버스 + 발급 버튼 
		# borderwidth=3, relief="flat" / "groove"
		self.btn = Button(self.root, image=self.img_btn, borderwidth=1)
		self.btn.bind("<ButtonRelease-1>", self.on_btn_click)
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
		self.regnum_pattern = re.compile('(서울)?[0-9]{2,3}[가-힣][0-9]{4}')	# 차량등록번호(자가용+영업용)
		self.vin_pattern = re.compile("[0-9A-Z]{13}[0-9]{4}")  					# 17자리 차대번호(13자리 영문자/숫자 + 4자리 숫자)
		
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
		del self.web_agent
		self.web_agent = WebAgentThread()

		# 항상 맨 위
		self.root.wm_attributes("-topmost", True)
		self.root.update()

	#########################################################
	# 소멸자(자원해제)
	def __del__(self):
		pass

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

			while self.web_agent.is_alive() == True:
				# 대기 캔버스
				self.canvas.itemconfig(self.canvas_img_id, image=self.img_bg_wait)
				#self.canvas.itemconfig(self.canvas_text_processing_id, text="처리중입니다...")
				#self.canvas.itemconfig(self.canvas_text_plzwait_id, text="잠시만 기다려주세요")
				self.label_loader.lift()
				self.root.update()
				print("[쓰레드 실행중] 대기화면 캔버스 올림")

				# 로딩화면 보여주기
				for current_frame in self.img_loader_frames:
					self.label_loader.configure(image=current_frame)
					self.root.update()
					time.sleep(0.03)

			# 쓰레드에서 발급 성공
			if self.web_agent.eco_process_success == True:
				self.get_eco_info()					# 쓰레드에서 저공해 정보 얻어옴
				self.display_result(countdown=50)	# 50초간 발급 결과 화면 보여주기

			# 쓰레드에서 발급 실패
			else:
				print("[저공해 발급] 오류 발생")
				response = messagebox.askretrycancel("조회 오류", "저공해 차량정보가 조회되지 않습니다.\n한번 더 확인하시려면 '다시 시도' 클릭\n처음으로 돌아가시려면 '취소' 클릭")
				if response == True:
					# 재시도 = True
					retry = True

					# 쓰레드 죽이고 + 다시 생성 + 쓰레드 시작
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
			self.root.geometry("+{}+{}".format(pos_x + delta_x, pos_y + delta_y))
			self.root.update()
			# - 2*delta만큼 이동
			self.root.geometry("+{}+{}".format(pos_x - 2*delta_x, pos_y - 2*delta_y))
			self.root.update()
			# 다시 +delta만큼 이동
			self.root.geometry("+{}+{}".format(pos_x + delta_x, pos_y + delta_y))
			self.root.update()

			this_time -= 1

		self.root.geometry(f"+{pos_x}+{pos_y}")
		self.root.update()


class LoginAgent:
	def __init__(self):

		# 접속 성공 flag
		self.login_success = False
		self.autologin = True

		# Tk 윈도 생성
		self.root = Tk()
		self.root.iconbitmap(r'res\car_icon.ico')
		self.root.geometry("292x90+{}+{}".format(int((self.root.winfo_screenwidth()-self.root.winfo_width())/2-150), int((self.root.winfo_screenheight()-self.root.winfo_height())/2-100)))
		self.root.title("관리자 로그인")
		self.root.resizable(False, False)
		self.root.wm_attributes("-topmost", True)
	
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
		self.entry_PW.bind("<Return>", self.check_login)

		# 로그인 버튼(이미지)
		self.img_btn = PhotoImage(file=r"res\login_button.png")
		self.btn_login = Button(self.root, image=self.img_btn, borderwidth=1, command=self.check_login)
		self.btn_login.grid(row=0, column=2, columnspan=2, rowspan=2, padx=4, pady=4)

		# "자동 로그인" 체크버튼
		self.VarCheckBtn = IntVar()
		self.btn_login = Checkbutton(self.root, text = " 자동 로그인", variable=self.VarCheckBtn, onvalue=True, offvalue=False, state=DISABLED)
		self.btn_login.grid(row=2, column=0, sticky="s", rowspan=2, columnspan=2, padx=4, pady=2)
		self.VarCheckBtn.set(True)

		# 사이트 접속용 Headless Chrome 생성
		self.options = webdriver.ChromeOptions()
		self.options.headless = True
		self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko")
		self.options.add_argument("log-level=2")
		self.options.add_argument("lang=ko_KR")
		self.options.add_experimental_option("excludeSwitches", ["enable-logging"])		# 세션정보 유지
		self.options.add_argument("--user-data-dir=" + SESSION_INFO_PATH)						# 세션정보 저장
		self.browser = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=self.options)

		# TK윈도 무한루프
		self.root.mainloop()

	def check_login(self):
		self.entry_ID["state"] = DISABLED
		self.entry_PW["state"] = DISABLED
		
		if self.login() == True:
			self.login_success = True
			
			global AUTHENTICATION_SUCCESS
			AUTHENTICATION_SUCCESS = True
			global ADMIN_ID
			ADMIN_ID = self.entry_ID.get()
			global ADMIN_PW
			ADMIN_PW = self.entry_PW.get()
			self.root.destroy()

		else:
			self.login_success = False
			self.entry_ID["state"] = NORMAL
			self.entry_PW["state"] = NORMAL
			self.entry_ID.delete(0, END)
			self.entry_PW.delete(0, END)
			self.win_shake(horizontal=True)
	
	def login(self):
		# 저공해차 확인 사이트 접속
		try:
			self.browser.get(URL_ADMIN)
			#self.browser.implicitly_wait(5)		# 페이지 완전히 로딩될 때까지 최대 5초 기다린다.
		except NewConnectionError as nce:
			print("[로그인 확인] 대상 컴퓨터와 연결되지 못했습니다.(연결거부 or 서버장애)")

		# 로그인(id/pw)
		try:
			self.browser.find_element_by_id("userId").send_keys(self.entry_ID.get())		# ID
			self.browser.find_element_by_id("userPw").send_keys(self.entry_PW.get())		# PW
			self.browser.find_element_by_class_name("btn_login.mt20").click()				# 로그인 버튼
			print("[로그인 확인] 로그인 버튼 누름")
		except NoSuchElementException:
			print("[로그인 확인] ID/PW 엘리먼트를 찾을 수 없습니다.")
			self.browser.quit()
			return False
		
		# 로그아웃 버튼 XPATH : '//*[@id="wrap"]/div[2]/div/div/div/ul/li[2]/a'
		try:
			logout_button = WebDriverWait(self.browser, 2).until(EC.presence_of_element_located((By.XPATH, '//*[@id="wrap"]/div[2]/div/div/div/ul/li[2]/a')))
			self.browser.execute_script("arguments[0].click();", logout_button)
			print("[로그인 확인] 로그인 / 로그아웃 둘 다 성공")
			self.browser.quit()
			return True

		except:
			print("[로그인 확인] ID/PW가 올바르지 않습니다.")
			self.browser.quit()
			return False

	#########################################################
	# 윈도 흔들기 : horizontal=True이면 좌우방향, False이면 상하방향
	def win_shake(self, horizontal=True):
		total_times = 40
		this_time = total_times
		original_pos_x = self.root.winfo_x()
		original_pos_y = self.root.winfo_y()

		while this_time > 0:
			# 방향에 따라 delta값 설정
			if horizontal == True:
				delta_x = int(10*cos((-0.5*pi*this_time/total_times) + 0.5*pi))
				delta_y = 0
			else:
				delta_x = 0
				delta_y = int(10*cos((-0.5*pi*this_time/total_times) + 0.5*pi))

			# + delta만큼 이동
			self.root.geometry("+{}+{}".format(original_pos_x + delta_x, original_pos_y + delta_y))
			self.root.update()
			# - 2*delta만큼 이동
			self.root.geometry("+{}+{}".format(original_pos_x - 2*delta_x, original_pos_y - 2*delta_y))
			self.root.update()
			# 다시 +delta만큼 이동
			self.root.geometry("+{}+{}".format(original_pos_x + delta_x, original_pos_y + delta_y))
			self.root.update()

			this_time -= 1

		self.root.geometry("+{}+{}".format(original_pos_x, original_pos_y))
		self.root.update()


class LoadAuthInfo:
	def __init__(self):
		self.key = base64.urlsafe_b64encode((AUTH_DEFAULT_KEY.encode("utf-8")))		# b'EcoSticker2021 by Kim Jae Hyoung'
		self.fernet = Fernet(self.key)

		self.ID = ""
		self.PW = ""
		self.LOAD_AUTH_SUCCESS = self.getAuthFromFile()

	# 인증정보 파일로부터 ID, PW 추출 (이미 자동로그인으로 저장된 정보)
	def getAuthFromFile(self):
		try:
			with open(AUTH_FILE_PATH, "rb") as file:
				file_contents = file.read()
				self.ID = self.fernet.decrypt(file_contents[:100]).decode("utf-8")		# ID 추출 (100byte)
				self.PW = self.fernet.decrypt(file_contents[100:]).decode("utf-8")		# PW 추출 (100byte)

		except (FileNotFoundError, OSError, IOError) as e:
			print("[인증파일 읽기] 경로/파일이 없거나 읽을 수 없습니다.")
			return False
		
		return True		# 성공

	# ID, PW 인증정보를 파일에 저장 (자동로그인 체크하여 처음 로그인한 경우)
	def saveAuthToFile(self, id, pw):
		id_encrypted = self.fernet.encrypt(id.encode("utf-8"))	# id 암호화 (길이=100byte)
		pw_encrypted = self.fernet.encrypt(pw.encode("utf-8"))	# pw 암호화 (길이=100byte)

		try:
			with open(AUTH_FILE_PATH, "wb") as file:	# 이미 파일이 존재하는 경우 파일 지움(에러 없음)
				file.write(id_encrypted)
				file.write(pw_encrypted)

		except (OSError, IOError) as e:
			print("[인증파일 저장] 인증정보를 파일에 저장 중 에러가 발생하였습니다.")
			return False

		return True		# 성공


	def LoadAuthSuccess(self):
		global AUTHENTICATION_SUCCESS
		AUTHENTICATION_SUCCESS = True
		return self.LOAD_AUTH_SUCCESS


if __name__ == '__main__':

	# 저장된 파일로부터 인증정보 확인
	auth = LoadAuthInfo()

	# 인증정보 확인 안된 경우 ==> 로그인 메시지박스
	if auth.LoadAuthSuccess() == False:
		login = LoginAgent()

	# 로그인 성공시에만 저공해차량 스티커 발급모드
	if AUTHENTICATION_SUCCESS == True:
		auth.saveAuthToFile(ADMIN_ID, ADMIN_PW)

		ecoSticker = EcoSticker()
	else:
		sys.exit(0)		# 정상 종료
