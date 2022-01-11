from threading import Thread
from selenium import webdriver
from NScreenPlayer4 import *


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
		self.reg_num = reg_num
		self.vin_num = vin_num


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
		self.browser.find_element_by_xpath('//*[@id="carRegistNo"]').send_keys(self.reg_num)	# 등록번호 입력
		self.browser.find_element_by_xpath('//*[@id="vinNm"]').send_keys(self.vin_num)			# 차대번호 입력
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


a = WebAgentThread()
a.setCarInfo("123가1234", "12345678901234567")
start = time.time()
a.start()
print("[맨처음] is_alive() 호출결과: {}".format(a.is_alive()))

# Tk 윈도 부분
root = Tk()

img_canvas_wait = PhotoImage(file=r"res\wait.png")		# 대기 화면
img_loader_frames = [PhotoImage(file='res/loader/frame-{}.png'.format(i)) for i in range(1, 35+1)]		# 파일:1~35, frame:0~34

# 기본캔버스 생성 + 기본이미지 붙임
canvas = Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white', bd=0, highlightthickness=0)
canvas_img_id = canvas.create_image(0, 0, image=img_canvas_wait, anchor="nw")	# id = 1
canvas.pack(fill="both", expand=True)

label_loader = Label(root, bg="#84C3EF")
canvas.create_window(CANVAS_WIDTH/2, CANVAS_HEIGHT/2, anchor="c", window=label_loader)

# loader 돌림
while a.is_alive() == True:
	for current_frame in img_loader_frames:
		label_loader.configure(image=current_frame)
		root.update()
		time.sleep(0.03)
		print("[루프내부] is_alive() 호출결과: ", a.is_alive())		# 쓰레드 객체가 run() 실행을 끝내면 종료된다.(False)

end = time.time()
print("실행시간: {}초".format(end-start))

print("[맨마지막] is_alive() 호출결과: ", a.is_alive())		# 쓰레드 객체가 run() 실행을 끝내면 종료된다.(False)

if a.eco_process_success == True:							# 하지만 쓰레드는 종료되어도, 쓰레드 객체는 살아있어 내부변수 접근 가능
	print("[발급결과] 발급번호: {} \t 등록번호: {}".format(a.issue_num, a.reg_num))	

# 쓰레드 객체 죽임
del a
#print("[쓰레드 del 후] 발급번호: {} \t 등록번호: {}".format(a.issue_num, a.reg_num))	# 오류 발생

# 쓰레드 객체 다시 생성
a = WebAgentThread()
print("[쓰레드 del 후] 발급번호: {} \t 등록번호: {}".format(a.issue_num, a.reg_num))	# 오류 발생 X

root.mainloop()
