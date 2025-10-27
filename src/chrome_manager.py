# 파일: src/chrome_manager.py
# 역할: 전화번호별 크롬 프로필 관리 및 브라우저 생성 (로그인 페이지 자동 오픈 포함)

import os  # 경로 및 파일 처리
import time  # 시간 지연
import json  # JSON 파일 읽기/쓰기
import pyautogui  # 전화번호 선택 팝업

# from selenium import webdriver  # 셀레니움 웹드라이버
import undetected_chromedriver as uc  # ⭐ 탐지 회피용 (webdriver 대체)
from selenium_stealth import stealth # ⭐ 탐지 회피용(import undetected_chromedriver as 와 함께 사용하면 효과 up)
from selenium.webdriver.common.keys import Keys  # 키보드 입력 (이건 필요)
from selenium.webdriver.common.action_chains import ActionChains  # 액션체인 (이것도 필요)

from config import USER_AGENT, DEFAULT_CHROME_OPTIONS, NAVERBAND_URL, MOBILE_USER_AGENT_MAPPING

from src.utils import get_profile_path, logger, move_mouse_naturally
from resources.xpath_dict import id_dict

def fix_chrome_profile_preferences(profile_dir):
    """
    크롬 프로필의 Preferences 파일을 수정하여
    '페이지 복원' 팝업과 비밀번호 저장 팝업을 사전 차단합니다.
    """
    pref_file = os.path.join(profile_dir, "Default", "Preferences")  # Preferences 파일 경로
    if os.path.exists(pref_file):  # 파일 존재 여부 확인
        try:
            with open(pref_file, 'r', encoding='utf-8') as f:
                prefs = json.load(f)  # JSON 형식으로 읽기
            
            prefs['profile'] = prefs.get('profile', {})  # profile 키 확보
            prefs['profile']['exit_type'] = 'Normal'  # 정상 종료로 설정
            prefs['profile']['exited_cleanly'] = True  # 깨끗하게 종료된 것으로 표시
            
            with open(pref_file, 'w', encoding='utf-8') as f:
                json.dump(prefs, f, ensure_ascii=False, indent=4)  # 수정 내용 저장
            logger.info(f"[INFO] 프로필 Preferences 수정 완료: {profile_dir}")
        except Exception as e:
            logger.error(f"[ERROR] Preferences 수정 실패: {e}")


def close_restore_popup(driver):
    """
    크롬 브라우저에서 '페이지를 복원하시겠습니까?' 팝업이 떴을 때,
    ESC 키를 보내서 팝업을 강제로 닫아 자동화가 계속 진행되게 하는 함수.
    """
    try:
        actions = ActionChains(driver)  # 액션체인 객체 생성
        actions.send_keys(Keys.ESCAPE)  # ESC 키 전송
        actions.perform()  # 액션 실행
        logger.info("[INFO] 복원 팝업 ESC 키 전송으로 닫음")
    except Exception as e:
        logger.error(f"[WARN] 복원 팝업 닫기 실패: {e}")

import undetected_chromedriver as uc
from selenium_stealth import stealth
from config import DEFAULT_CHROME_OPTIONS  # 탐지 우회용 기본 옵션들
import logging

logger = logging.getLogger(__name__)

def get_stealth_driver(profile_dir: str, user_agent: str):
    """
    탐지 회피 강화용 undetected_chromedriver와 selenium-stealth를 적용한 크롬 드라이버 생성 함수
    
    Args:
        profile_dir (str): 크롬 프로필 경로
        user_agent (str): User-Agent 문자열

    Returns:
        uc.Chrome: 크롬 드라이버 인스턴스
    """
    try:
        options = uc.ChromeOptions()

        # 사용자 크롬 프로필 적용
        options.add_argument(f"--user-data-dir={profile_dir}")
        # 불필요한 로그 레벨 제한
        options.add_argument('--log-level=3')
        # GPU 가속 비활성화
        options.add_argument('--disable-gpu')
        # 계정별 User-Agent 지정
        options.add_argument(f"user-agent={user_agent}")

        # config.py에 정의된 탐지회피 옵션 모두 추가
        for opt in DEFAULT_CHROME_OPTIONS:
            options.add_argument(opt)

        # 비밀번호 저장 및 자동완성 팝업 차단
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        options.add_experimental_option("prefs", prefs)

        # 드라이버 생성 (서브프로세스 사용 권장)
        driver = uc.Chrome(options=options, use_subprocess=True)

        # selenium-stealth 적용하여 navigator 등 JS 속성 위조 및 탐지 회피
        stealth(driver,
                languages=["ko-KR", "ko"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)

        # 창 위치 및 크기 설정
        driver.set_window_position(0, 0)
        driver.maximize_window()

        logger.info("[INFO] 탐지회피 크롬 드라이버 생성 완료")

        return driver

    except Exception as e:
        logger.error(f"[ERROR] 탐지회피 크롬 드라이버 생성 실패: {e}")
        raise


# from src.chrome_manager import get_stealth_driver  # 경로는 환경에 따라 달라질 수 있음
def select_mobile_and_get_driver():
    ids = list(id_dict.keys())
    mobile_num = pyautogui.confirm('전화번호를 선택하시오', buttons=ids)
    logger.info(f'선택한 전화번호: {mobile_num}')

    profile_dir = get_profile_path(mobile_num)
    fix_chrome_profile_preferences(profile_dir)

    user_agent = MOBILE_USER_AGENT_MAPPING.get(mobile_num, USER_AGENT)
    logger.info(f"[INFO] 사용할 User-Agent: {user_agent}")

    # 모듈화된 탐지회피 드라이버 생성 함수 호출
    driver = get_stealth_driver(profile_dir, user_agent)

    move_mouse_naturally()
    driver.get(NAVERBAND_URL)
    time.sleep(2)

    driver.selected_mobile = mobile_num
    close_restore_popup(driver)

    return mobile_num, driver



if __name__ == "__main__":
    # 테스트 실행
    mobile, driver = select_mobile_and_get_driver()
    logger.info(f"{mobile} 계정으로 브라우저가 실행되었습니다.")
    input("아무 키나 누르면 브라우저를 종료합니다...")
    driver.quit()
