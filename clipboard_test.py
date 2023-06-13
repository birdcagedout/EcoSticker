import re
import time
import pyperclip
from math import *
from enum import Enum
from tkinter import *
from threading import *		# Timer

class ClipboardState(Enum):
	EMPTY = "EMPTY"
	REGNUM = "REGNUM"
	FULL = "FULL"


class MyApp():
	def __init__(self):

		# 클립보드용 변수
		self.prev_regnum = ""
		self.old_content = ""
		self.regnum = ""
		self.vinnum = ""
		self.clipboard_state = ClipboardState.EMPTY
		self.clipboard_timer = None

		self.regnum_pattern = re.compile("([가-힣]{2})?[0-9]{2,3}[가-힣][0-9]{4}")
		self.vin_pattern = re.compile("[0-9A-Z]{17}")

		# tkinter 윈도
		self.root = Tk()
		self.root.geometry("400x300+1400+500")

		self.label_ID.grid(row=0, column=0, sticky=W, padx=2, pady=4)
		self.entry_state = Entry(self.root)
		self.entry_old = Entry(self.root)
		self.entry_new = Entry(self.root)
		self.entry_regnum = Entry(self.root)
		self.entry_vinnum = Entry(self.root)
		self.entry_state.pack()
		self.entry_old.pack()
		self.entry_new.pack()
		self.entry_regnum.pack()
		self.entry_vinnum.pack()
		self.root.update()


		# 클립보드 총괄함수
		self.clipboard_automate()
		self.root.mainloop()


	def __del__(self):
		if self.clipboard_timer.is_alive():
			self.clipboard_timer.cancel()
			self.clipboard_timer.join()



	# 타이머 timeout 핸들러
	def clipboard_timeout(self, clipboard_state):
		if clipboard_state == ClipboardState.REGNUM:
			self.regnum = ""
			# self.old_content = ""								# 같은 차량번호 다시 Ctrl+C 했을 때 반응하도록
			self.clipboard_state = ClipboardState.EMPTY
			self.win_shake(horizontal=True)
			print("차대번호 기다리다 timeout되었습니다.")

		elif clipboard_state == ClipboardState.FULL:
			self.regnum = ""
			self.vinnum = ""
			self.clipboard_state = ClipboardState.EMPTY
			self.win_shake(horizontal=True)
			print("발급버튼 눌러주기 기다리다 timeout되었습니다.")
			# 이 부분에서 발급버튼을 disable 시켜야 한다.
			# btn["STATE"] = DISABLED
	
	
	def clipboard_automate(self):

		new_content = pyperclip.paste().strip()

		# 클립보드 내용이 안 바뀐 경우 ==> 무시
		if new_content == self.old_content:
			pass

		# 클립보드 내용이 바뀐 경우

		# 현재 입력상태가 "아무것도 입력되지 않은 상태"라면
		elif self.clipboard_state == ClipboardState.EMPTY:

			# 클립보드 확인(차량번호인지)
			match_result = self.regnum_pattern.match(new_content)
			if (match_result is not None) and (new_content == match_result.group()):
				self.win_shake(horizontal=False)
				self.regnum = new_content
				self.clipboard_state = ClipboardState.REGNUM

				self.clipboard_timer = Timer(5, self.clipboard_timeout, [self.clipboard_state])
				self.clipboard_timer.start()

				self.entry_state.insert(0, str(self.clipboard_state))
			self.old_content = new_content

		# 현재 입력상태가 "차량번호 입력된 상태"라면
		elif self.clipboard_state == ClipboardState.REGNUM:

			# 클립보드 확인1(차대번호인지)
			match_result = self.vin_pattern.match(new_content)
			if (match_result is not None) and (new_content == match_result.group()):
				self.win_shake(horizontal=False)
				self.vinnum = new_content
				self.clipboard_state = ClipboardState.FULL

				self.clipboard_timer = Timer(5, self.clipboard_timeout, [self.clipboard_state])
				self.clipboard_timer.start()

				self.entry_state.insert(0, str(self.clipboard_state))
			else:
				self.win_shake(horizontal=True)
				self.regnum = ""
				self.clipboard_state = ClipboardState.EMPTY
			self.old_content = new_content


		self.root.after(100, self.clipboard_automate)


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






if __name__ == '__main__':
	my_app = MyApp()