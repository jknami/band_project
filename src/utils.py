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



'''
get_root_dir()는 PyInstaller로 exe 파일을 만들 때도 정상적으로 리소스 및 경로를 찾기 위해 만들어진 유틸 함수입니다.

요약 설명
일반 파이썬 개발/실행 환경

.py 파일 실행 시 프로젝트 루트(상위 경로)를 동적으로 반환합니다.

PyInstaller 배포(.exe) 환경

PyInstaller로 패키징된 실행파일(exe)에서는 내부적으로 리소스(텍스트, 이미지 등)를 임시 폴더(sys._MEIPASS)에 풀어주기 때문에,

이 경로(sys._MEIPASS)를 반환하여 exe에서도 리소스 경로가 깨지지 않고 동작하도록 해줍니다.

즉, 개발 중이든, exe로 만든 후든 코드와 리소스를 구분하지 않고 안정적으로 접근할 수 있게 하는 역할입니다.
'''
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
    print(f'profile_dir의 경로는 {profile_path}')
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
# Selenium XPATH 핸들링 유틸리티
##############################

def x_path_click(driver, xpath: str, wait_time=10):
    """
    지정한 xpath를 클릭합니다.
    예외 발생 시 홈 복구 없이 에러만 출력하고 raise로 상위에서 처리하도록 함.
    """
    try:
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        element = driver.find_element(By.XPATH, xpath)
        driver.execute_script("arguments[0].click();", element)
    except (TimeoutException, NoSuchElementException) as e:
        print(f"[WARN] XPATH 클릭 실패: {xpath}\n에러: {e}")
        raise   # 예외를 상위로 올림
    except Exception as e:
        print(f"[ERROR] 알 수 없는 예외: {e}")
        raise

def x_path_send_keys(driver, xpath: str, send: str, wait_time=10):
    """
    해당 xpath에 send_keys 입력 (예외처리/복구 URL 이동 삭제, 예외를 raise)
    """
    try:
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        element = driver.find_element(By.XPATH, xpath)
        element.send_keys(send)
    except (TimeoutException, NoSuchElementException) as e:
        print(f"[WARN] XPATH send_keys 실패: {xpath}\n에러: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] 알 수 없는 예외: {e}")
        raise