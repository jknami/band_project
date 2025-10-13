# 파일: config.py
# 역할: 전역 설정 및 상수 관리 (mobile_num별 크롬 프로필 지원)

# 로그인 페이지 URL
NAVERBAND_URL = "https://www.band.us/home"
NAVERBAND_LOGIN_URL = "https://auth.band.us/phone_login?keep_login=false"

# 크롬 프로필 및 쿠키 디렉토리 이름
CHROME_PROFILE_DIRNAME = "chrome_profile"
COOKIE_DIRNAME = "cookies"

# 밴드 XPath 리스트를 for문으로 생성
BAND_LIST = [
    f'//*[@id="content"]/section/div[2]/div/ul/li[{i}]/div/div/a/div[1]/div'
    for i in range(2, 11)
]
#활용예시
# import random

# 원본(BAND_LIST)은 그대로 두고,
# copy_list = BAND_LIST.copy()     # 복사본 생성
# random.shuffle(copy_list)        # 복사본만 랜덤 순서로 섞어줌
# choice = random.choice(BAND_LIST)
# print(choice)
# print("원본:", BAND_LIST)
# print("섞인 복사본:", copy_list)


# 자원(게시글 텍스트, 이미지) 경로
TXT_DIR= "resources/txt"
IMAGE_DIR = "resources/images"

DEFAULT_HOME_URL = "https://band.us/home"
LOGIN_URL = "https://band.us/login"
BOARD_URL = "https://band.us/board"

URL_MODES = {
    "home": DEFAULT_HOME_URL,
    "login": LOGIN_URL,
    "board": BOARD_URL,
}


# 다중 계정 루트 폴더
# ACCOUNT_ROOT_DIR = resource_path("accounts") #예) d:\coding\login\accounts

# 셀레니움 브라우저 옵션 기본 리스트
DEFAULT_CHROME_OPTIONS = [
    "--disable-blink-features=AutomationControlled",
    "--disable-infobars",
    "--disable-extensions",
    "--no-sandbox", 
    "--disable-dev-shm-usage",
    "--ignore-certificate-errors",
    "--disable-popup-blocking",
    "--start-maximized",
]

# 사용자 에이전트
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/115.0.0.0 Safari/537.36"
)

