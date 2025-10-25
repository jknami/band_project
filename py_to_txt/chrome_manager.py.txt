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


def select_mobile_and_get_driver():
    """
    pyautogui로 전화번호를 선택하고, 해당 번호의 크롬 프로필을 적용한 드라이버를 생성,
    네이버밴드 로그인 페이지로 자동 이동하여 반환합니다.
    
    Returns:
        tuple: (selected_mobile_num, chrome_driver)
    """
    # 1) id_dict에서 전화번호 키 리스트 추출
    ids = list(id_dict.keys())  # 사용 가능한 전화번호 목록
    
    # 2) pyautogui로 전화번호 선택
    mobile_num = pyautogui.confirm('전화번호를 선택하시오', buttons=ids)  # 팝업창으로 선택
    logger.info(f'선택한 전화번호는 {mobile_num}')  # 선택된 전화번호 로그 기록

    # 3) 선택된 전화번호에 맞는 크롬 프로필 경로 계산 및 생성
    profile_dir = get_profile_path(mobile_num)  # 전화번호별 프로필 경로 가져오기

    # 4) 프로필 Preferences 파일 패치
    fix_chrome_profile_preferences(profile_dir)  # 복원 팝업 등 차단 설정

    ####기존 탐지회피 옵션#####
    # # 5) ChromeOptions 객체 생성 및 옵션 추가
    # options = webdriver.ChromeOptions()  # 크롬 옵션 객체
    # options.add_argument(f"--user-data-dir={profile_dir}")  # 프로필 적용
    # options.add_argument('--log-level=3')  # 로그 레벨 최소화
    # options.add_argument('--disable-gpu')  # GPU 사용 비활성화
    # options.add_argument('--disable-software-rasterizer')  # 소프트웨어 래스터라이저 비활성화

    # # config.py에 정의된 기본 옵션 일괄 적용
    # for opt in DEFAULT_CHROME_OPTIONS:  # 이미 탐지 회피 옵션 포함
    #     options.add_argument(opt)  # 기본 옵션 추가

    # options.add_argument(f"user-agent={USER_AGENT}")  # 사용자 에이전트 설정
    
    # # 추가 탐지 회피 관련 실험 옵션
    # options.add_experimental_option("excludeSwitches", ["enable-automation"])  # 자동화 스위치 제외
    # options.add_experimental_option("useAutomationExtension", False)  # 자동화 확장 사용 안함


    # 5) 계정별 User-Agent 선택 (있으면 계정별, 없으면 기본값)
    user_agent = MOBILE_USER_AGENT_MAPPING.get(mobile_num, USER_AGENT)
    logger.info(f"[INFO] 사용할 User-Agent: {user_agent}")

    ###⭐6) undetected_chromedriver 옵션 설정새로운 탐지회피 옵션###
    options = uc.ChromeOptions()
    options.add_argument(f"--user-data-dir={profile_dir}")
    options.add_argument('--log-level=3')
    options.add_argument('--disable-gpu')

    options.add_argument(f"user-agent={user_agent}")  # ✅ 계정별 User-Agent 사용

    # config.py에 정의된 기본 옵션 일괄 적용
    for opt in DEFAULT_CHROME_OPTIONS:  # 이미 탐지 회피 옵션 포함
        options.add_argument(opt)  # 기본 옵션 추가


    # 비밀번호 저장/자동완성 관리 팝업 사전 차단
    prefs = {
        "credentials_enable_service": False,  # 크롬 비밀번호 관리 서비스 OFF
        "profile.password_manager_enabled": False  # 프로필 비밀번호 저장/자동완성 OFF
    }
    options.add_experimental_option("prefs", prefs)  # 프리퍼런스 옵션 적용
    
    # 6) ChromeDriverManager로 드라이버 설치/업데이트 후 실행(from selenium import webdriver  # 셀레니움 웹드라이버를 import할 경우사용)
    # service = Service(ChromeDriverManager().install(), log_path='NUL')  # 윈도우 기준 콘솔 로그 숨김
    # driver = webdriver.Chrome(service=service, options=options)  # 드라이버 생성


    # 7) ⭐ undetected_chromedriver로 드라이버 생성
    driver = uc.Chrome(options=options, use_subprocess=True)  # use_subprocess=True 권장

    # ⭐ selenium-stealth 적용
    stealth(driver,
    languages=["ko-KR", "ko"],
    vendor="Google Inc.",
    platform="Win32",
    webgl_vendor="Intel Inc.",
    renderer="Intel Iris OpenGL Engine",
    fix_hairline=True,
)

    # ⭐ 창 크기 및 위치 설정 (undetected-chromedriver는 기본적으로 창 크기와 위치를 자동으로 설정하지 않는 문제해결(듀얼 모니터 문제 해결))
    driver.set_window_position(0, 0)  # 메인 모니터 왼쪽 상단으로 이동
    driver.maximize_window()  # 창 최대화

    move_mouse_naturally()  # 자연스러운 마우스 움직임

    # 8) 네이버밴드 로그인 페이지로 자동 이동
    driver.get(NAVERBAND_URL)  # config.py에서 정의한 URL로 이동
    time.sleep(2)  # 페이지 로딩 대기

    # # 탐지 JS 속성 우회 강화
    # try:
    #     driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
    #         "source": """
    #             Object.defineProperty(navigator, 'webdriver', {get: () => false});
    #             Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
    #             Object.defineProperty(navigator, 'languages', {get: () => ['ko-KR', 'ko']});
    #         """
    #     })
    # except Exception as e:
    #     logger.error(f"[WARN] 탐지 JS 우회 코드 주입 실패: {e}")

    # 9) 드라이버에 선택된 전화번호 정보 저장
    driver.selected_mobile = mobile_num  # driver 객체에 선택 전화번호 속성 추가
    
    # 10) "페이지 복원" 팝업 자동 닫기 시도
    close_restore_popup(driver)  # 복원 팝업 ESC로 닫기
    
    return mobile_num, driver  # 전화번호와 드라이버 반환


if __name__ == "__main__":
    # 테스트 실행
    mobile, driver = select_mobile_and_get_driver()
    logger.info(f"{mobile} 계정으로 브라우저가 실행되었습니다.")
    input("아무 키나 누르면 브라우저를 종료합니다...")
    driver.quit()
