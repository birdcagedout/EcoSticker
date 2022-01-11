import re
import time
import sys
import base64
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

DEFAULT_WORKING_PATH = r"C:\EcoSticker"
SESSION_INFO_PATH = DEFAULT_WORKING_PATH + r"session_info"
CHROMEDRIVER_PATH = DEFAULT_WORKING_PATH + r"\chromedriver.exe"
AUTH_FILE_PATH = DEFAULT_WORKING_PATH + r"\Auth.dat"

URL_ADMIN = "https://www.ev.or.kr/lcvms-mncpt/login.do"				# 관리자용 저공해차 발급 사이트
#URL_GUEST = "https://www.ev.or.kr/lcvms-portal/EP020401000SF01.do"	# 일반인용 저공해차 확인 사이트

AUTHENTICATION_SUCCESS = False
AUTH_DEFAULT_KEY = "EcoSticker2021 by Kim Jae Hyoung"		# 길이는 반드시 32byte : base64.urlsafe_b64decode(key)=32
ADMIN_ID = "su0672"
ADMIN_PW = "su0672"

# 로그아웃 버튼 XPATH : '//*[@id="wrap"]/div[2]/div/div/div/ul/li[2]/a'

## 테스트 차대번호 : 일반적으로 17자리 (끝자리 6자리 = 반드시 숫자)
# 1종 : KNAC381AFNA002915 KMHJ8816FNU018004
# 2종 : KNAPV81GBNK000521 KNARF81GBNA068551
# 3종 : KPBXH3AT1NP370787 KMHL341DBNA179522
# *** 독일차 차대번호 : WBA7L7106M7J56681 (끝자리 5개 숫자)
# *** 예외적 차대번호 : 끝자리 4자리만 숫자도 존재함
# *** 발급된 적 없는 차대번호 : KMHE341DBNA616046 (택시)

class EcoSticker:
	#########################################################
	# 생성자(초기화)
	def __init__(self, root):
		# Tk윈도 생성
		self.root = root
		self.root.iconbitmap(r"res\car_icon.ico")
		self.root.title("저공해차량 스티커 자동발급 시스템 ver.0.2")
		self.root.geometry(f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}+{WIN_POS_X}+{WIN_POS_Y}")
		self.root.resizable(False, False)
		self.root.wm_attributes("-topmost", True)

		# 배경 이미지 + 버튼 이미지 : (경로설정은 r string : file=r"res\bg_nature.png")
		self.img_bg0 = PhotoImage(file=r"res\bg_nature.png")		# 기본 배경(자연) : current_img=0
		self.img_e1 = PhotoImage(file=r"res\e1_half_cover.png")		# 1종 스티커 : current_img='z'
		self.img_e2 = PhotoImage(file=r"res\e2_half_cover.png")		# 2종 스티커 : current_img='a'
		self.img_e3 = PhotoImage(file=r"res\e3_half_cover.png")		# 3종 스티커 : current_img='b'
		self.img_btn = PhotoImage(file=r"res\issue_button.png")		# 발급 버튼 : 230x147
		self.img_canvas_wait = PhotoImage(file=r"res\wait.png")			# 대기 화면
		self.img_loader_frames = [PhotoImage(file='res/loader/frame-{}.png'.format(i)) for i in range(1, 35+1)]		# 파일:1~35, frame:0~34

		# 기본캔버스 생성 + 기본이미지 붙임
		self.canvas = Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white', bd=0, highlightthickness=0)
		self.canvas_img_id = self.canvas.create_image(0, 0, image=self.img_bg0, anchor="nw")	# id = 1
		self.canvas_img_now = 0
		self.canvas.pack(fill="both", expand=True)

		# 기본캔버스 + 발급 버튼 
		# borderwidth=3, relief="flat" / "groove"
		self.btn = Button(self.root, image=self.img_btn, borderwidth=1)
		self.btn.bind("<ButtonRelease-1>", self.on_btn_click)
		self.btn.configure(width=230, height=147, activebackground="#FFFFFF")
		self.btn_ID = self.canvas.create_window(127, 50, anchor="nw", window=self.btn)
		self.btn["state"] = DISABLED

		# 로딩캔버스 + 라벨
		#self.canvas_wait = Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white', bd=0, highlightthickness=0)
		#self.canvas_wait.create_image(0, 0, image=self.img_canvas_wait, anchor="nw")
		#self.canvas_wait.pack(fill="both", expand=True)
		
		self.label_loader = Label(self.root, bg="#84C3EF")
		self.canvas.create_window(CANVAS_WIDTH/2, CANVAS_HEIGHT/2, anchor="c", window=self.label_loader)

		# 기본캔버스 + 텍스트
		self.canvas_text_issuenum_id = self.canvas.create_text(X_POS_ISSUENUM, Y_POS_ISSUENUM, font=("Malgun Gothic", 20, "bold"), anchor="nw", text="")
		self.canvas_text_regnum_id = self.canvas.create_text(X_POS_REGNUM, Y_POS_REGNUM, font=("Malgun Gothic", 20, "bold"), anchor="nw", text="")
		self.canvas_text_count_id = self.canvas.create_text(X_POS_REGNUM + 150, Y_POS_REGNUM + 65, font=("Malgun Gothic", 12), fill="yellow", anchor="nw", text="")

		# 클립보드 저장용 변수 초기화
		self.vin_pattern = re.compile("[0-9A-Z]{13}[0-9]{4}")  # 17자리 차대번호(13자리 영문자/숫자 + 4자리 숫자)
		self.last_clipboard = ""
		self.current_clipboard = ""

		# 사이트 접속용 Headless Chrome 생성
		self.options = webdriver.ChromeOptions()
		#self.options.add_argument("--headless")		#self.options.headless = True
		self.options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko")
		self.options.add_argument("log-level=2")
		self.options.add_argument("lang=ko_KR")
		self.options.add_experimental_option("excludeSwitches", ["enable-logging"])		# 세션정보 유지
		self.options.add_argument("--user-data-dir=" + SESSION_INFO_PATH)				# 세션정보 저장
		#self.browser = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=self.options)

		# 저공해 차량인 경우 저공해 정보
		self.eco_class = ""
		self.car_name = ""
		self.fuel_type = ""
		self.owner_name = ""
		self.reg_num = ""
		self.issue_count = ""
		self.issue_num = ""
		
		# 쓰레드를 위한 flag
		self.check_eco_success = False		# 쓰레드가 저공해 차량인지 확인한 결과
		self.issue_sticker_success = False	# 쓰레드가 저공해 스티커 발급한 결과

		# 발급성공 flag
		self.issue_success = False

		# 캔버스에 왼쪽버튼 클릭시 이벤트핸들러 = canvas_onLclick()
		#self.canvas.bind("<Button-1>", self.canvas_onLclick)

	#########################################################
	# 발급/발급취소 단계 후 초기화 함수
	def reset_all(self):

		# 캔버스 초기화
		self.canvas.itemconfig(self.canvas_img_id, image=self.img_bg0)
		self.canvas_img_now = 0

		self.canvas.itemconfig(self.canvas_text_issuenum_id, text="")
		self.canvas.itemconfig(self.canvas_text_regnum_id, text="")
		self.canvas.itemconfig(self.canvas_text_count_id, text="")

		# 버튼 초기화
		self.btn.lift()
		self.btn["state"] = DISABLED

		# 대기 loader 초기화
		self.label_loader.configure(image=None)
		self.label_loader.lower()

		# 클립보드 변수 초기화
		self.last_clipboard = self.current_clipboard
		self.current_clipboard = ""
		if self.issue_success == True:
			self.root.clipboard_clear()
			self.root.clipboard_append(" ")

		# 저공해 차량인 경우 저공해 정보
		self.eco_class = ""
		self.car_name = ""
		self.fuel_type = ""
		self.owner_name = ""
		self.reg_num = ""
		self.issue_count = ""
		self.issue_num = ""
		
		# 쓰레드를 위한 flag
		self.check_eco_success = False		# 쓰레드가 저공해 차량인지 확인한 결과
		self.issue_sticker_success = False	# 쓰레드가 저공해 스티커 발급한 결과

		# 발급성공 flag
		self.issue_success = False

		# 항상 맨 위
		self.root.wm_attributes("-topmost", True)
		self.root.update()

	#########################################################
	# 소멸자(자원해제)
	def __del__(self):

		# 이미지 삭제
		self.img_bg0.__del__()
		self.img_e1.__del__()
		self.img_e2.__del__()
		self.img_e3.__del__()
		self.img_btn.__del__()

		# 버튼 삭제
		self.btn.destroy()

		# 라벨 삭제
		self.label_loader.destroy()

		# 기본 캔버스(텍스트 포함) 삭제
		self.canvas.delete(self.canvas_text_issuenum_id)
		self.canvas.delete(self.canvas_text_regnum_id)
		self.canvas.delete(self.canvas_text_count_id)
		self.canvas.destroy()

		# 대기 캔버스(텍스트 포함) 삭제
		#self.canvas_wait.destroy()

		# 크롬 삭제
		#self.browser.quit()

	#########################################################
	# 윈도 좌우로 흔들기
	def win_shake(self):
		times = 40
		nth = times
		original_pos_x = self.root.winfo_x()
		original_pos_y = self.root.winfo_y()

		while nth > 0:
			self.root.geometry("+{}+{}".format(original_pos_x + int(10*cos((-0.5*pi*nth/times) + 0.5*pi)), original_pos_y))
			self.root.update()
			
			self.root.geometry("+{}+{}".format(original_pos_x - int(20*cos((-0.5*pi*nth/times) + 0.5*pi)), original_pos_y))
			self.root.update()

			self.root.geometry("+{}+{}".format(original_pos_x + int(10*cos((-0.5*pi*nth/times) + 0.5*pi)), original_pos_y))
			self.root.update()

			nth -= 1

		self.root.geometry("+{}+{}".format(original_pos_x, original_pos_y))
		self.root.update()

	#########################################################
	# 클립보드를 확인하는 함수 : 새로운 차대번호 맞으면 return True
	def vin_copied(self):
		try:
			self.current_clipboard = self.root.clipboard_get().strip()
			match_result = self.vin_pattern.match(self.current_clipboard)
			if (len(self.current_clipboard) == 17) and (match_result is not None):		# 차대번호가 맞고
				if self.current_clipboard != self.last_clipboard:						# 이전값과 다르면
					print("[클립보드 감시] 새로운 차대번호를 발견하였습니다.")
					return True
				else:
					print("[클립보드 감시] 이전 차대번호가 유지되고 있습니다.")
			else:
				print("[클립보드 감시] 차대번호 형식이 아닙니다.")
		except TclError:
			self.current_clipboard = ""
			self.root.clipboard_clear()
			self.root.clipboard_append(" ")		# 텅빈 클립보드에서 읽어오면 TclError 발생
			#print("[클립보드 감시] TclError가 발생하여 클립보드를 초기화합니다.")
		
		return False

	#########################################################
	# 저공해 차량 확인 + 발급 : 저공해 차량이면 return True
	def check_if_eco(self):

		self.check_thread = Thread(target=self._check_eco_by_thread_)
		self.check_thread.start()
		print("쓰레드 시작")

		# 발급대기 시작 ==> 기본 캔버스 버튼 숨김
		self.btn.lower()

		# 대기 캔버스 + loader 라벨 시작
		self.canvas.itemconfig(self.canvas_img_id, image=self.img_canvas_wait)
		self.label_loader.lift()
		self.root.update()
		print("대기 캔버스 올림")

		# loader 돌림 : 5번
		# 루프 1회 : 0.03초 * 35프레임 = 1.05초
		loop_count = 5
		while loop_count > 0:
			for current_frame in self.img_loader_frames:
				self.label_loader.configure(image=current_frame)
				self.root.update()
				loop_count -= 1
				time.sleep(0.03)
		
		self.check_thread.join()
		print("쓰레드 join 끝")

		# loader 라벨 초기화
		self.label_loader.configure(image=None)
		self.label_loader.lower()

		# 성공 여부를 return
		return self.check_eco_success


	def _check_eco_by_thread_(main_thread):

		# Headless Chrome 생성
		browser = webdriver.Chrome(executable_path=CHROMEDRIVER_PATH, options=main_thread.options)

		total_retry = 2
		retry_count = total_retry
		while retry_count > 0:

			# 저공해차 확인 사이트 접속
			print("저공해 발급사이트 {}/{}번째 접속합니다...".format(3-retry_count, total_retry))
			try:
				browser.get(URL_ADMIN)
				#browser.implicitly_wait(5)		# 페이지 완전히 로딩될 때까지 최대 5초 기다린다.
			except NewConnectionError as nce:
				print("[로그인 확인] 대상 컴퓨터와 연결되지 못했습니다.(연결거부 or 서버장애)")

				main_thread.check_eco_success = False
				retry_count = -1
				#return

			# 세션 정보 살아있으면 ==> 로그인 과정 불필요
			try:
				# 로그인(id/pw)
				browser.find_element_by_id("userId").send_keys(ADMIN_ID)		# ID
				browser.find_element_by_id("userPw").send_keys(ADMIN_PW)		# PW
				browser.find_element_by_class_name("btn_login.mt20").click()	# 버튼
			except NoSuchElementException:
				print("[저공해 확인] 로그인 생략합니다...")
				pass
			
			# 발급페이지 웹엘리먼트에 차대입력
			browser.find_element_by_xpath('//*[@id="vinNm"]').send_keys(main_thread.current_clipboard)	# 차대번호 입력
			browser.find_element_by_id('btnSearch').click()												# 확인(검색)버튼 클릭
			print("[저공해 확인] 차대입력 후 확인 버튼 클릭!")

			# Case1. 오류 팝업 나오는 경우 ==> 기다렸다가 오류 팝업의 "확인" 버튼 클릭
			try:
				# 오류 팝업의 "확인" 버튼 XPATH : '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a'
				# <저공해 차량이 아닌 경우>
				# 팝업1 : "요청하신 차량은 조회결과가 없습니다. 제원번호 입력 후 확인해주세요."
				# 팝업2 : "차대번호 또는 차량등록번호를 입력해주세요."
				# 팝업3 : "요청하신 차량은 저공해차 차량이 아닙니다.(제원번호미존재)"
				# <저공해 차량인데 기등록된 경우>
				# 팝업1 : "차량등록번호를 입력해주세요."
				alert_button = WebDriverWait(browser, 6).until(EC.presence_of_element_located((By.XPATH, '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a')))
				#alert_message = main_thread.browser.find_element_by_xpath('//*[@id="messageLayerPop"]/div/div[2]/div').text
				#print(alert_message)
				alert_message = browser.find_element_by_xpath('//*[@id="layerPop2"]/div/div[2]/div/div[1]').text
				print(alert_message, len(alert_message))		# 메시지와 메시지의 길이
				browser.execute_script("arguments[0].click();", alert_button)
				print("[저공해 확인] 오류 팝업 발생")
				
				main_thread.check_eco_success = False
				retry_count = -1
				#return False

			# Case2. 저공해 차량 맞는 경우 : 사이트의 저공해 정보 추출
			except TimeoutException:
				# 등급 		: '//*[@id="ECO_NO"]'			# 1종
				# 차모델	: '//*[@id="CAR_NM"]'			# EV6	깨진문자 #40; = (	깨진문자 #41; = )
				# 사용연료	: '//*[@id="USEFUELNM"]'		# 전기
				# 소유자 	: '//*[@id="OWNER_NM"]'			# 김OO
				# 등록번호 	: '//*[@id="CAR_REGIST_NO"]'	# 55루2327
				# 발급횟수	: '//*[@id="ISSU_CNT"]'			# 0 1 ...
				# 발급번호 	: '//*[@id="CVISU_NO"]'			# 20210902-1068577
				main_thread.eco_class = browser.find_element_by_xpath('//*[@id="ECO_NO"]').text.strip()
				main_thread.car_name = browser.find_element_by_xpath('//*[@id="CAR_NM"]').text.strip()
				main_thread.fuel_type = browser.find_element_by_xpath('//*[@id="USEFUELNM"]').text.strip()
				main_thread.owner_name = browser.find_element_by_xpath('//*[@id="OWNER_NM"]').text.strip()
				main_thread.reg_num = browser.find_element_by_xpath('//*[@id="CAR_REGIST_NO"]').text.strip()
				main_thread.issue_count = browser.find_element_by_xpath('//*[@id="ISSU_CNT"]').text.strip()

				# 발급사이트 오류 : 저공해차가 맞는데 저공해 등급 안뜨는 경우 가끔 발생 ==> 1번만 더 재시도
				if main_thread.eco_class not in ["1종", "2종", "3종"]:
					retry_count -= 1
					
					# 1번째 시도인 경우 ==> 한번 더 확인
					if retry_count == 1:
						print(f"[저공해 확인 실패] {retry_count}번 더 확인 시도합니다.")
					
					# 2번째 시도인 경우 ==> 최종 실패
					else:
						main_thread.check_eco_success = False
						retry_count = -1
						#return
				
				# 저공해 정보 뜬 경우 ==> 정상적인 저공해차 ==> return True
				else:
					print("[저공해 확인] 저공해 정보 확인되었습니다.")
					main_thread.check_eco_success = True
					retry_count = 0
					#return

		main_thread.check_eco_success = False
		return False 		# 2번 모두 실패한 경우 ==> 저공해차 아님


	#########################################################
	# 발급 함수
	def issue_sticker(self):
		
		# 발급버튼 누르기
		# 표지발급 / 재발급	: '//*[@id="btnCvisu"]'
		# 한참 후에 눌러서 세션 종료된 경우 ==> 재시도 없이 return False
		try:
			self.browser.find_element_by_xpath('//*[@id="btnCvisu"]').click()
		except NoSuchElementException:
			print("[발급사이트 오류] 발급버튼이 없습니다.")
			return False

		# Case1. 정상적으로 "표지발급이 완료되었습니다." 팝업창 기다림 ==> 닫기
		# 팝업창 확인 버튼	: '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a'
		try:
			alert_button = WebDriverWait(self.browser, 3).until(EC.presence_of_element_located((By.XPATH, '//*[@id="layerPop2"]/div/div[2]/div/div[2]/a')))
			self.browser.execute_script("arguments[0].click();", alert_button)
			print("표지가 정상적으로 발급되었습니다.")

		# Case2. 비정상적으로 표지발급 안 된 경우(발급시간 초과)
		except TimeoutException:
			#response = messagebox.askretrycancel("발급사이트 오류", "표지발급 시간이 초과하였습니다.")
			#if response == 1:	# 재시도 선택시
			#	self.retry_issue_sticker = True
			#else:				# 취소 선택시
			#	self.retry_issue_sticker = False
			print("[발급사이트 오류] 표지발급 시간이 초과하였습니다.")
			return False

		# 정상적으로 발급된 경우 : 발급번호 나옴
		self.issue_num = self.browser.find_element_by_xpath('//*[@id="CVISU_NO"]').text.strip()
		return True

	#########################################################
	# 발급결과 출력 함수
	def display_result(self, countdown):
		#issue_num = "20210830-1063069"
		#car_num = "123고6789"

		self.canvas.itemconfig(self.canvas_text_issuenum_id, text=self.issue_num)
		self.canvas.itemconfig(self.canvas_text_regnum_id, text=self.reg_num)
		self.canvas.itemconfig(self.canvas_text_count_id, text=f"{countdown}초 후 닫습니다")
		self.canvas.update()


	#########################################################
	# 클립보드 차대 확인/저공해 확인/발급/결과표시 등 총괄 callback함수
	def automate(self):

		# 새로운 차대번호 복사되었다면
		if self.vin_copied() == True:
			# 발급 버튼 활성화
			self.btn["state"] = NORMAL
		
		# 새로운 차대번호가 복사되지 않은 경우
		else:
			# 발급 버튼 비활성화
			self.btn["state"] = DISABLED
			#self.win_shake()

		# 항상 맨 위
		self.root.wm_attributes("-topmost", True)
		self.root.update()

		# 1초 후 timer event로 callback
		self.root.after(1000, self.automate)


	#########################################################
	# 발급버튼 클릭 이벤트 처리 함수
	def on_btn_click(self, event):

		# 버튼 비활성화 상태는 무시
		if self.btn["state"] == DISABLED:
			print("버튼 비활성화 상태입니다.")
		
		# 버튼이 "normal" 또는 "active"
		else:
			# 저공해 차량 확인 ==> 저공해 차량인 경우
			#self.issue_ready_pending = True
			if self.check_if_eco() == True:

				# 스티커 발급 ==> 성공
				if self.issue_sticker() == True:			# 스티커 발급 성공시

					# 발급 성공시 버튼윈도우/버튼 초기화
					#self.canvas.delete(self.btn_ID)		# 버튼 윈도우 삭제
					self.btn.lower()						# 버튼 감추기

					# 저공해 종별에 따라 캔버스 이미지 변신
					if self.eco_class == "1종":
						self.canvas.itemconfig(self.canvas_img_id, image=self.img_e1)
						self.canvas_img_now = 'z'
					elif self.eco_class == "2종":
						self.canvas.itemconfig(self.canvas_img_id, image=self.img_e2)
						self.canvas_img_now = 'a'
					elif self.eco_class == "3종":
						self.canvas.itemconfig(self.canvas_img_id, image=self.img_e3)
						self.canvas_img_now = 'b'

					# 발급번호 / 차량등록번호 출력 + 발급성공 flag
					#self.display_result()
					self.issue_success = True

				# 스티커 발급 실패
				else:
					print("[저공해 발급] 발급시 오류 발생")
					self.issue_success = False

			# 저공해 차량 아닌 경우
			else:
				response = messagebox.showinfo("확인 오류", "저공해 차량이 아닙니다.\n시스템을 초기화합니다.")
				if response == "ok":
					print("메시지박스 OK ==> 초기화")

			#self.issue_ready_pending = False
		
			# 발급 성공시 = 50초 잠자기
			show_countdown = 50
			if self.issue_success == True:
				while show_countdown > 0:
					self.display_result(show_countdown)
					time.sleep(1)
					show_countdown -= 1

			# 전체 초기화
			self.reset_all()



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
			self.win_shake()
	
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

	def win_shake(self):
		times = 40
		nth = times
		original_pos_x = self.root.winfo_x()
		original_pos_y = self.root.winfo_y()

		while nth > 0:
			self.root.geometry("+{}+{}".format(original_pos_x + int(10*cos((-0.5*pi*nth/times) + 0.5*pi)), original_pos_y))
			self.root.update()
			
			self.root.geometry("+{}+{}".format(original_pos_x - int(20*cos((-0.5*pi*nth/times) + 0.5*pi)), original_pos_y))
			self.root.update()

			self.root.geometry("+{}+{}".format(original_pos_x + int(10*cos((-0.5*pi*nth/times) + 0.5*pi)), original_pos_y))
			self.root.update()

			nth -= 1

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

		root = Tk()
		ecoSticker = EcoSticker(root)
		
		# 저공해스티커 발급 총괄 callback 함수
		ecoSticker.automate()
		root.mainloop()
	else:
		sys.exit(0)		# 정상 종료
