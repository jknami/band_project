# 파일: src/utils.py
# 역할: 프로젝트 공통 유틸리티 함수 (경로 처리, 리소스 로드 등)

import os
import sys
import random
import glob
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.alert import Alert
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from config import URL_MODES, CHROME_PROFILE_DIRNAME, COOKIE_DIRNAME
from config import TXT_DIR, IMAGE_DIR
import time, datetime
import pygetwindow as gw
#(pip install pygetwindow pyobjc-core pyobjc-framework-Quartz )
import pyautogui
import logging
import os
from logging.handlers import RotatingFileHandler
from selenium.webdriver.remote.webelement import WebElement
from resources.xpath_dict import xpath_dict

def get_root_dir() -> str:
    """
    프로젝트의 최상위(root) 디렉터리 경로를 반환합니다.


    - 개발용(.py 파일 직접 실행): src/utils.py 기준으로 상위 2단계가 프로젝트 루트
    - Jupyter Notebook(.ipynb): 현재 작업 디렉터리를 루트로 간주 (필요시 cwd 기준)
    - PyInstaller 빌드 환경: sys._MEIPASS 경로
    """
    # 1. PyInstaller로 빌드된 exe 실행 환경에서 접속할 때
    if hasattr(sys, "_MEIPASS"):
        # sys._MEIPASS는 exe 내부 리소스 파일이 임시로 압축 해제되는 폴더
        # 빌드된 exe 배포 파일에서 리소스/데이터 로딩할 때 반드시 필요
        return sys._MEIPASS
    # 2. 일반(Python) 개발 환경 또는 Notebook 환경 구분
    try:
        # __file__ : 현재 실행 중인 .py 파일의 경로 (예: src/utils.py)
        # os.path.abspath(__file__) : 파일의 전체 경로 반환
        base = os.path.abspath(__file__)
        # 상위 2단계(../..): src/utils.py → src → [프로젝트 루트]
        return os.path.dirname(os.path.dirname(base))
    except NameError:
        # NameError (__file__ 미정의): Jupyter, IPython 등 셀 환경에서만 발생
        # 노트북 환경에서는 현재 작업 경로를 기본 루트로 반환
        base = os.getcwd()
        # 필요에 따라 한 단계만 상위로, 아니면 그대로 반환해도 무방 (대개 cwd가 루트)
        return base



def resource_path(relative_path: str) -> str:
    """
    프로젝트 루트 기준의 상대 경로를 절대 경로로 변환하여 반환합니다.
    - PyInstaller 빌드 및 개발 환경 모두에서 올바른 리소스 경로로 동작합니다.


    Args:
        relative_path (str): 프로젝트 루트 기준 상대 경로
            예: "resources/mozip.txt" , "accounts/01075381965/chrome_profile"


    Returns:
        str: 파일 혹은 폴더의 절대 경로 (OS별 슬래시 자동처리)
    """
    # 1) 프로젝트 루트 디렉토리 경로를 얻어옴
    #     get_root_dir() 함수는 실행 환경(Python 스크립트/노트북/.exe)에 따라 올바른 루트 경로를 반환함
    root = get_root_dir()   



    # 2) 루트와 상대 경로를 결합하여 OS별 절대경로 문자열 생성
    #     예: root가 "d:/coding/login", relative_path가 "resources/mozip.txt"면
    #         "d:/coding/login/resources/mozip.txt"로 반환됨
    return os.path.join(root, relative_path)




def get_random_file(resource_dir: str) -> str:
    """
    지정 폴더에서 txt, jpg, jpeg, png, gif 모든 파일 중 랜덤 추출
    """
    exts = ['*.txt', '*.jpg', '*.jpeg', '*.png', '*.gif']
    file_list = []
    for ext in exts:
        file_list.extend(glob.glob(os.path.join(resource_dir, '**', ext), recursive=True))
    if not file_list:
        raise FileNotFoundError("해당 폴더에 파일이 없습니다.")
    return resource_path(random.choice(file_list))


# 사용 예시
# resource_dir = "resources"  # images, txt 모두 포함
# random_file = get_random_file(IMAGE_dir)
# print(random_file)


def ensure_dir(path: str):
    """
    주어진 경로(path)가 디렉토리로 존재하지 않으면
    자동으로 새 디렉토리를 생성해 주는 함수입니다.
    
    Args:
        path (str): 생성할 디렉토리 경로 (절대경로 또는 프로젝트 루트 기준 상대경로)
    """
    # 1) 만약 입력 경로가 절대경로가 아니라면, resource_path로 절대경로로 변환
    #    예: "accounts/01075381965/chrome_profile" 등을 "D:/login/accounts/..." 형태로 변환
    abs_path = path if os.path.isabs(path) else resource_path(path)
    
    # 2) 해당 경로가 실제로 존재하지 않으면, 새로 생성 (이미 있으면 아무 동작 없음)
    os.makedirs(abs_path, exist_ok=True)


##############################
# lgo저장 관련
##############################

# 1. 로그 저장 폴더를 프로젝트 루트 기준으로 절대경로 변환
log_dir = resource_path("logs")

# 2. 로그 폴더가 없으면 반드시 새로 생성 (파일 저장 시도 시 에러 방지)
os.makedirs(log_dir, exist_ok=True)

# 3. 모듈 전역에서 사용할 logger 객체 생성 및 기본 로그 레벨 설정
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)  # INFO 이상 로그만 기록

# 4. 파일 핸들러 생성
#    크기는 10MB, 최대 5개의 이전 로그파일을 순환 저장하도록 설정
file_handler = RotatingFileHandler(
    filename=os.path.join(log_dir, "app.log"),  # 로그파일 이름과 경로 지정
    maxBytes=10 * 1024 * 1024,  # 10MB
    backupCount=5               # 최대 백업 파일 수
)
file_handler.setLevel(logging.INFO)  # 파일에 기록할 최소 로그 레벨 설정

# 5. 로그 출력 포맷 지정 (시간, 로그레벨, 메시지 포함)
formatter = logging.Formatter(
    '[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
file_handler.setFormatter(formatter)

# 6. 생성한 파일 핸들러를 logger에 추가해 파일로 로그 기록 가능
logger.addHandler(file_handler)

# 7. 콘솔에도 로그를 출력하려면 콘솔 핸들러 생성 및 연결
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)  # 콘솔에 출력할 로그 레벨 설정
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
# 이후부터는 기존과 동일하게
# logger.info("메시지"), logger.warning("경고"), logger.error("오류") 등 사용


##############################
# 계정별 크롬 프로필/쿠키 경로 지원 함수
##############################
def get_profile_path(mobile_num: str) -> str:
    """
    전화번호에 따른 개별 크롬 프로필 경로를 반환합니다.
    Args:
        mobile_num (str): 전화번호 (예: '01075381965')
    Returns:
        str: 해당 전화번호의 크롬 프로필 절대 경로
    """
    profile_path = resource_path(f"accounts/{mobile_num}/{CHROME_PROFILE_DIRNAME}")
    ensure_dir(profile_path)  # 경로가 없으면 자동 생성
    logger.info(f'get_profile_paht()->profile_dir의 경로는 {profile_path}')
    return profile_path


def get_cookie_path(mobile_num: str) -> str:
    """
    전화번호에 따른 개별 쿠키 저장 경로를 반환합니다.
    Args:
        mobile_num (str): 전화번호 (예: '01075381965')
    Returns:
        str: 해당 전화번호의 쿠키 저장 절대 경로
    """
    cookie_path = resource_path(f"accounts/{mobile_num}/{COOKIE_DIRNAME}")
    ensure_dir(cookie_path)  # 경로가 없으면 자동 생성
    return cookie_path


# 기본 디렉토리 생성
ensure_dir("resources")
ensure_dir("accounts")
ensure_dir("dist")



##############################
# Human-like Delays and Mouse Movements
##############################
def random_sleep(min_sec=0.5, max_sec=1.5):
    """
    동작 사이 클록 간격을 임의로 랜덤 설정하는 함수


    Args:
        min_sec (float): 최소 딜레이 시간(초)
        max_sec (float): 최대 딜레이 시간(초)
    """
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def human_delay(stage="default"):
    """
    사람 같은 행동지연을 단계별(stage별)로 다르게 적용.
    Args:
        stage (str): 행동 단계 구분 (click, typing, upload, thinking 등)
    """
    delays = {
        "click": (0.5, 1.3),         # 클릭 등 빠른 행동
        "typing": (1.2, 3.6),        # 타이핑은 더딤
        "upload": (2.0, 4.5),        # 파일찾기/탐색 흉내
        "thinking": (1.5, 5.0),      # 고민 후 클릭
        "scroll": (0.3, 1.0),        # 약간 짧음
        "default": (1.0, 2.5)
    }
    min_d, max_d = delays.get(stage, delays["default"])
    t = random.uniform(min_d, max_d)
    logger.info(f"[DELAY] {stage} 단계: {t:.2f}초 대기")
    time.sleep(t)


# 마우스 자연이동
def move_mouse_naturally(target_x=None, target_y=None):
    """
    마우스를 자연스럽게 임의 혹은 지정 좌표로 이동


    Args:
        target_x (int, optional): 목표 X좌표, 없으면 랜덤 지정
        target_y (int, optional): 목표 Y좌표, 없으면 랜덤 지정
    """
    if target_x is None:
        target_x = random.randint(300, 900)
    if target_y is None:
        target_y = random.randint(200, 600)
    duration = random.uniform(0.4, 1.5)
    pyautogui.moveTo(target_x, target_y, duration=duration)
    # logger.info(f"[INFO] 마우스 자연 이동: ({target_x}, {target_y}), duration: {duration:.2f}s")


def focus_window(title_substring):
    """
    윈도우 운영체제용: 창 제목에 특정 문자열 포함된 창을 찾아 포커스 이동 및 최대화
    (pygetwindow 필요, Windows 전용)


    Args:
        title_substring (str): 창 제목(url) 일부를 넣으면 됨
    """
    windows = gw.getWindowsWithTitle(title_substring)
    if windows:
        win = windows[0]
        if not win.isActive:
            win.activate()
            time.sleep(0.5)
        if not win.isMaximized:
            win.maximize()
        # logger.info(f"[INFO] 창 포커스 및 최대화: {win.title}")
    else:
        logger.warning(f"[WARN] 창 '{title_substring}' 찾지 못함")



# ===================
# Typing Simulation
# ===================
# 인접 키보드 배열. 오타가 날 때 인접한 키 중 하나를 입력
adjacent_keys = {
    "a": "qsxz", "b": "vhn", "c": "xdfv", "d": "serfcx", "e": "wsdr", "f": "drtgvc",
    "g": "ftyhbv", "h": "gyujnb", "i": "ujko", "j": "huikmn", "k": "jiolm", "l": "kop",
    "m": "njk", "n": "bhjm", "o": "iklp", "p": "ol", "q": "wa", "r": "edft", "s": "awedxz",
    "t": "rfgy", "u": "yhji", "v": "cfgb", "w": "qase", "x": "zsdc", "y": "tghu", "z": "asx"
}


def get_typo_char(c):
    # 입력할 문자의 소문자 인접 키를 랜덤 선택
    c = c.lower()
    return random.choice(adjacent_keys.get(c, "abcdefghijklmnopqrstuvwxyz"))



def realistic_typing(element: WebElement, text: str, typo_prob=0.016):
    """
    실제 사람처럼 타이핑하는 함수.
    - 평균 타자 속도를 정규분포로 흉내냄 (빠르게 조정)
    - 오타는 영어/한글 등 문자에서만 발생, 숫자는 오타 불가
    - 오타 즉시 백스페이스로 삭제하고 수정 문자 입력
    - 문장 부호나 공백 뒤에는 자연스러운 휴식(딜레이) 추가

    Args:
        element: Selenium WebElement (글 입력란 요소)
        text: 실제 입력할 문자열
        typo_prob: 오타 발생 확률 (0~1 사이, 기본 1.6%)
    """
    i = 0
    n = len(text)
    while i < n:
        c = text[i]

        # 타자 속도: 평균 0.07초, 표준편차 0.02초인 가우스 분포로 딜레이 생성
        delay = max(0.005, random.gauss(0.07, 0.02))  # 너무 빨라도 최소 0.005초
        time.sleep(delay)  # 각 문자 입력 사이 자연스러운 지연

        element.send_keys(c)  # 문자 입력

        # 오타 발생 조건:
        # - 영어/한글 등 문자만 오타 낼 수 있도록 isalpha()로 필터링
        # - 숫자(0~9)는 오타 내지 않음
        # - 텍스트 중 초반 3글자와 마지막 3글자는 오타 제외 (안정성 위해)
        if c.isalpha() and random.random() < typo_prob and 3 < i < n - 3:
            # 오타 문자 얻기 (인접 키 기반)
            typo_char = get_typo_char(c)
            
            # 오타 문자 입력
            element.send_keys(typo_char)
            time.sleep(random.uniform(0.05, 0.12))  # 오타-수정 간 자연스러운 시간

            # 백스페이스 입력으로 오타 삭제
            element.send_keys('\b')
            time.sleep(random.uniform(0.04, 0.10))  # 삭제 후 잠깐 대기

            # 원래 문자 다시 입력 (수정 반영)
            element.send_keys(c)
            time.sleep(random.uniform(0.04, 0.10))  # 수정 후 대기

        # 문장부호에 따른 자연스러운 휴식
        if c in ".!?":
            # 마침표/물음표/느낌표 뒤에는 더 긴 휴식
            time.sleep(random.uniform(0.12, 0.45))
        elif c in ",;:":
            # 쉼표, 세미콜론, 콜론 뒤에는 중간 휴식
            time.sleep(random.uniform(0.05, 0.18))

        # 가끔씩 띄어쓰기 후 매우 긴 휴식도 추가 (사람 집중하는 순간 모사)
        if c == " " and random.random() < 0.001:
            time.sleep(random.uniform(0.8, 2.0))

        i += 1




# ===================
# Selenium Utility Functions
# ==================
def save_error_screenshot(driver, filename_prefix="error"):
    """
    Selenium WebDriver 스크린샷을 'logs/screenshots' 폴더에 저장
    파일명에 타임스탬프 추가해 중복 방지 및 관리 편의 제공


    Args:
        driver: Selenium WebDriver 객체
        filename_prefix (str): 파일명 접두어 (예: "write_click_error")
    """
    save_dir = resource_path("logs/screenshots")
    ensure_dir(save_dir)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename_prefix}_{timestamp}.png"
    filepath = os.path.join(save_dir, filename)

    driver.save_screenshot(filepath)
    logger.info(f"[INFO] 에러 스크린샷 저장: {filepath}")

def go_home(driver, xpath_dict, wait_time=10):
    """
    xpath_dict 내 '홈' 키의 XPath를 활용해 네이버 밴드 홈 화면으로 강제 복귀하는 함수
    
    Args:
        driver: Selenium WebDriver 객체
        xpath_dict: XPath가 정의된 딕셔너리 (resources/xpath_dict.py)
        wait_time: 엘리먼트 대기 시간 (초)
    
    동작:
        - '홈' 버튼이 클릭 가능할 때까지 기다림
        - 클릭 후 약간 대기
        - 예외 발생 시 에러 로깅
    """
    try:
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.element_to_be_clickable((By.XPATH, xpath_dict['홈'])))
        home_button = driver.find_element(By.XPATH, xpath_dict['홈'])
        home_button.click()
        logger.info("[복구] 홈 버튼 클릭하여 강제 복귀 성공")
        time.sleep(2)  # 페이지 로딩 대기
    except Exception as e:
        logger.error(f"[복구 실패] 홈 버튼 클릭 실패: {e}")
        # 추가 복구 로직을 여기에 작성 가능


def x_path_click(driver, xpath: str, wait_time=10):
    """
    지정한 xpath를 클릭하는 함수.
    클릭 전후 랜덤 딜레이와 실패 시 스크린샷/사람 행동 패턴 흉내 추가.


    Args:
        driver: Selenium WebDriver 객체
        xpath: 클릭 대상 xpath 문자열
        wait_time: 요소 대기 시간(초)
    """
    try:
        human_delay('click')  # 클릭 전 랜덤 딜레이
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
        element = driver.find_element(By.XPATH, xpath)
        driver.execute_script("arguments[0].click();", element)
        random_sleep(0.2, 0.8)  # 클릭 후 랜덤 딜레이

    except (TimeoutException, NoSuchElementException) as e:
        logger.warning(f"[WARN] XPATH 클릭 실패: {xpath}\n에러: {e}")

        # 스크린샷 저장 (utils.py에 구현한 save_error_screenshot 함수 사용)
        save_error_screenshot(driver, "xpath_click_fail")

        # 사람 행동 패턴 흉내: 마우스 자연 이동 + 딜레이 후 재시도 시도
        move_mouse_naturally()
        human_delay('thinking')

        # 재시도 시도 (1회만)
        try:
            human_delay('click')
            wait.until(EC.element_to_be_clickable((By.XPATH, xpath)))
            element = driver.find_element(By.XPATH, xpath)
            driver.execute_script("arguments[0].click();", element)
            random_sleep(0.3, 0.9)
        except Exception:
            raise  # 재시도 실패 시 예외 다시 발생

    except Exception as e:
        logger.error(f"[ERROR] 알 수 없는 예외: {e}")
        save_error_screenshot(driver, "xpath_click_unknown_error")
        # 홈 복귀는 상위에서 처리하도록 분리
        raise


def x_path_human_click(driver, xpath: str, wait_time=10):
    """
    인간 행동 패턴+강제 enable+JS click을 모두 적용한 '글쓰기' 클릭 최적화
    Args:
        driver: Selenium WebDriver 객체
        xpath: 클릭 대상 xpath
        wait_time: 요소 대기 시간(초)
    """
    try:
        human_delay("click")  # 클릭 전 자연스러운 대기

        # 1. 15초 내 표시+활성화될 때까지 polling
        for _ in range(int(wait_time * 2)):
            try:
                element = driver.find_element(By.XPATH, xpath)
                if element.is_displayed() and element.is_enabled():
                    break
                # 네이버 밴드 탐지/숨김/overlay 회피: JS로 스타일 강제화
                driver.execute_script("""
                    arguments[0].style.display = 'block';
                    arguments[0].style.visibility = 'visible';
                    arguments[0].style.opacity = 1;
                    arguments[0].style.zIndex = 99999;
                """, element)
            except Exception:
                pass
            time.sleep(0.5)
        else:
            save_error_screenshot(driver, "write_button_fail")
            logger.warning(f"[WARN] XPATH 클릭 미활성(표시x): {xpath}")
            raise TimeoutException("글쓰기 버튼 활성화 실패")

        # 2. pyautogui 등 보조도 가능하지만 우선 JS click + 추가 delay
        driver.execute_script("arguments[0].scrollIntoView(true);", element)
        human_delay("click")
        driver.execute_script("arguments[0].click();", element)
        logger.info("[INFO] 글쓰기 버튼 강제 클릭 성공")

        human_delay("default")  # 클릭 후 더 자연스러운 행동 흉내

    except (TimeoutException, NoSuchElementException) as e:
        logger.warning(f"[WARN] XPATH 클릭 실패: {xpath}\n에러: {e}")
        raise
    except Exception as e:
        save_error_screenshot(driver, "write_click_error")
        logger.error(f"[ERROR] 알 수 없는 예외: {e}")
        raise


def safe_xpath_click(driver, xpath: str, wait_time=10):
    try:
        x_path_click(driver, xpath, wait_time)
    except Exception as e:
        logger.warning(f"[WARN] 기본 클릭 실패({e}), 인간 패턴 클릭으로 전환 중...")
        try:
            x_path_human_click(driver, xpath, wait_time)
        except Exception as e2:
            logger.error(f"[ERROR] 보조 클릭도 실패({e2})")
            save_error_screenshot(driver, "final_click_fail")
            raise


def x_path_send_keys(driver, xpath: str, send: str, wait_time=10):
    """
    지정한 xpath 요소에 문자열 입력.
    입력 전후 랜덤 딜레이, 실패 시 스크린샷 저장 및 재시도 포함.

    Args:
        driver: Selenium WebDriver 객체
        xpath: 입력 대상 xpath 문자열
        send: 입력할 문자열
        wait_time: 요소 대기 시간(초)
    """
    try:
        random_sleep(0.3, 1.0)  # 입력 전 랜덤 딜레이
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        element = driver.find_element(By.XPATH, xpath)
        element.send_keys(send)
        random_sleep(0.2, 0.6)  # 입력 후 랜덤 딜레이

    except (TimeoutException, NoSuchElementException) as e:
        logger.warning(f"[WARN] XPATH send_keys 실패: {xpath}\n에러: {e}")

        # 스크린샷 저장
        save_error_screenshot(driver, "xpath_send_keys_fail")

        # 사람 행동 패턴 흉내: 마우스 자연 이동 + 딜레이 후 재시도 시도
        move_mouse_naturally()
        human_delay('thinking')

        # 재시도 (1회만)
        try:
            random_sleep(0.3, 0.8)
            wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
            element = driver.find_element(By.XPATH, xpath)
            element.send_keys(send)
            random_sleep(0.3, 0.7)
        except Exception:
            raise  # 재시도 실패 시 예외 재발생

    except Exception as e:
        logger.error(f"[ERROR] 알 수 없는 예외: {e}")
        save_error_screenshot(driver, "xpath_send_keys_unknown_error")
        raise
