from NScreenPlayer import *
from cryptography.fernet import Fernet 		# 암호화 패키지


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


	def succeedAuth(self):
		return self.LOAD_AUTH_SUCCESS

