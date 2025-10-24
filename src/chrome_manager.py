# 파일: src/chrome_manager.py
# 역할: 전화번호별 크롬 프로필 관리 및 브라우저 생성 (로그인 페이지 자동 오픈 포함)

import os
import time
import pickle
import json

import pyautogui

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.alert import Alert

from webdriver_manager.chrome import ChromeDriverManager

from config import (
    USER_AGENT,
    DEFAULT_CHROME_OPTIONS,
    NAVERBAND_URL,
    NAVERBAND_LOGIN_URL
)

from src.utils import (
    get_profile_path,
    get_cookie_path,
    x_path_send_keys
)

from resources.xpath_dict import xpath_dict, id_dict
from src.utils import logger

def fix_chrome_profile_preferences(profile_path: str):
    """
    크롬 사용자 프로필 내 Preferences 파일을 열어
    정상 종료 상태로 강제로 수정하는 함수입니다.

    크롬은 비정상 종료되면 다음 실행 시 "브라우저가 비정상적으로 종료되었습니다" 라는 알림을 띄우거나
    세션 복원 팝업을 띄울 수 있습니다.
    
    이 팝업을 막아 자동화가 원활하게 진행되도록 하기 위해,
    프로필 내 설정 파일의 'exit_type'과 'exited_cleanly' 값을 정상 종료를 의미하도록 변경합니다.

    Args:
        profile_path (str): 크롬 프로필 폴더 경로 (예: accounts/01075381965/chrome_profile)
    """
    # 1) Preferences 파일 경로 만들기
    #    크롬 프로필 기본 저장 위치 내 'Default/Preferences' 경로
    prefs_file = os.path.join(profile_path, 'Default', 'Preferences')
    logger.info(f'fix_chrome_profile_preferences()->크롬 프로필 기본 저장 위치 : {prefs_file}')

    # 2) Preferences 파일이 존재하는지 확인
    if os.path.exists(prefs_file):
        # 3) 파일을 json 모드로 읽기
        with open(prefs_file, 'r', encoding='utf-8') as f:
            prefs = json.load(f)

        # 4) 'profile' 키에 exit 정보가 있다면 수정
        if 'profile' in prefs:
            # 5) exit_type 수정 → 정상 종료('Normal')로 설정
            prefs['profile']['exit_type'] = 'Normal'
            # 6) exited_cleanly 수정 → True로 설정하여 정상 종료 플래그 활성화
            prefs['profile']['exited_cleanly'] = True

            # 7) 수정된 JSON 데이터를 다시 Preferences 파일에 UTF-8로 저장
            with open(prefs_file, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, ensure_ascii=False, indent=2)

def close_restore_popup(driver):
    """
    크롬 브라우저에서 '페이지를 복원하시겠습니까?' 팝업이 떴을 때,
    ESC 키를 보내서 팝업을 강제로 닫아 자동화가 계속 진행되게 하는 함수.
    """
    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE)
        actions.perform()
        logger.info("[INFO] 복원 팝업 ESC 키 전송으로 닫음")
    except Exception as e:
        logger.error(f"[WARN] 복원 팝업 닫기 실패: {e}")



def handle_alert_and_home(driver, home_url):
    try:
        alert = Alert(driver)
        alert.accept()  # "확인" 버튼 누름
        logger.info("[INFO] 경고/확인 팝업 자동 확인 완료")
        driver.get(home_url)
        logger.info(f"[INFO] 홈으로 이동: {home_url}")
    except Exception as e:
        logger.error(f"[WARN] 팝업 제어 or 홈 이동 실패: {e}")


def select_mobile_and_get_driver():
    """
    pyautogui로 전화번호를 선택하고, 해당 번호의 크롬 프로필을 적용한 드라이버를 생성,
    네이버밴드 로그인 페이지로 자동 이동하여 반환합니다.
    Returns:
        tuple: (selected_mobile_num, chrome_driver)
    """
    # 1) id_dict에서 전화번호 키 리스트 추출
    ids = list(id_dict.keys())
        
    # 2) pyautogui로 전화번호 선택
    mobile_num = pyautogui.confirm('전화번호를 선택하시오', buttons=ids)
    logger.info(f'선택한 전화번호는 {mobile_num}')

    # 3) 선택된 전화번호에 맞는 크롬 프로필 경로 계산 및 생성
    profile_dir = get_profile_path(mobile_num)


    # 4) 프로필 Preferences 파일 패치
    fix_chrome_profile_preferences(profile_dir)
    
    # 5) ChromeOptions 객체 생성 및 옵션 추가
    options = webdriver.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_dir}")  # 프로필 적용
    
    # 로그레벨 설정 (Print 로그 최소화)
    options.add_argument('--log-level=3')

    # GPU 비활성화 옵션
    options.add_argument('--disable-gpu')
    options.add_argument('--disable-software-rasterizer')

    # 탐지 회피 관련 옵션 추가
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    for opt in DEFAULT_CHROME_OPTIONS:
        options.add_argument(opt)                           # 기본 옵션
    options.add_argument(f"user-agent={USER_AGENT}")       # 사용자 에이전트

    # 5-1)======비밀번호 저장/자동완성 관리 팝업 사전 차단 ======
    # 이 프리퍼런스(prefs) 옵션을 추가하면 로그인 후 비밀번호 저장 안내창이 더 이상 나타나지 않음
    prefs = {
        "credentials_enable_service": False,            # 크롬 비밀번호 관리 서비스 OFF
        "profile.password_manager_enabled": False       # 프로필 비밀번호 저장/자동완성 OFF
    }
    options.add_experimental_option("prefs", prefs)
    
    # 6) ChromeDriverManager로 드라이버 설치/업데이트 후 실행
    service = Service(ChromeDriverManager().install(), log_path='NUL')  # 윈도우 기준 콘솔 로그 숨김
    driver = webdriver.Chrome(service=service, options=options)

    
    from src.utils import move_mouse_naturally
    move_mouse_naturally()


    # 7) 네이버밴드 로그인 페이지로 자동 이동
    driver.get(NAVERBAND_URL)

   # 탐지 JS 속성 우회 강화 (execute_cdp_cmd 사용)
    try:
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
                Object.defineProperty(navigator, 'webdriver', {get: () => false});
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [1, 2, 3, 4, 5],
                });
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['ko-KR', 'ko'],
                });
            """
        })
    except Exception as e:
        logger.error(f"[WARN] 탐지 JS 우회 코드 주입 실패: {e}")


    # 8) 드라이버에 선택된 전화번호 정보 저장
    driver.selected_mobile = mobile_num
    
   # 9) "페이지 복원" 팝업 자동 닫기 시도
    close_restore_popup(driver)

    
    return mobile_num, driver

if __name__ == "__main__":
    # 테스트 실행
    mobile, driver = select_mobile_and_get_driver()
    logger.info(f"{mobile} 계정으로 브라우저가 실행되었습니다.")
    input("아무 키나 누르면 브라우저를 종료합니다...")
    driver.quit()
