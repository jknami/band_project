# 파일: src/account_manager.py
# 역할: 여러 계정의 쿠키 저장·로드 및 로그인 처리 (2차 인증 자동 처리 포함)

import os
import json
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException

from config import NAVERBAND_LOGIN_URL
from src.utils import get_cookie_path, x_path_send_keys, logger, move_mouse_naturally
from resources.xpath_dict import xpath_dict, id_dict


def save_cookies(driver):
    """
    현재 브라우저 세션의 쿠키를 account_id별 폴더에 JSON 형식으로 저장합니다.
    
    주의: 이 함수는 login() 함수 안에서 호출되지 않습니다!
         main.py에서 모든 자동화 작업(밴드 순회 등)이 완료된 후 호출됩니다.
    """
    account_id = driver.selected_mobile
    cookie_dir = get_cookie_path(account_id)
    cookie_path = os.path.join(cookie_dir, "cookies.json")
    
    try:
        cookies = driver.get_cookies()
        with open(cookie_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=4)
        logger.info(f"[INFO] 쿠키 저장 완료: {cookie_path}")
    except Exception as e:
        logger.error(f"[ERROR] 쿠키 저장 실패: {e}")


def load_cookies(driver, max_retries=1):
    """
    계정별로 저장된 JSON 쿠키를 불러와 현재 세션에 적용합니다.
    
    중요: 네이버밴드는 쿠키 복원 실패해도 1차 로그인을 진행하므로
         재시도 로직은 불필요합니다. 단순히 시도만 하고 결과를 반환합니다.
    
    Args:
        driver: 웹드라이버 객체
        max_retries: 재시도 횟수 (기본 1, 실제로는 재시도 안 함)
    
    Returns:
        bool: 쿠키 로드 성공 여부
    """
    account_id = driver.selected_mobile
    cookie_dir = get_cookie_path(account_id)
    cookie_path = os.path.join(cookie_dir, "cookies.json")
    
    # 1. 쿠키 파일 존재 여부 확인
    if not os.path.exists(cookie_path):
        logger.info(f"[INFO] 쿠키 파일 없음: {cookie_path}")
        logger.info("[INFO] 첫 로그인이거나 쿠키가 삭제된 상태입니다. 1차 로그인을 진행합니다.")
        return False
    
    try:
        # 2. 쿠키 파일 읽기
        with open(cookie_path, 'r', encoding='utf-8') as f:
            cookies = json.load(f)
        
        if not cookies:
            logger.warning("[WARN] 쿠키 파일이 비어있습니다.")
            logger.info("[INFO] 1차 로그인을 진행합니다.")
            return False
        
        # 3. 쿠키 드라이버에 추가
        added_count = 0
        failed_count = 0
        
        for cookie in cookies:
            try:
                if 'domain' in cookie and cookie['domain'].lstrip('.') in driver.current_url:
                    driver.add_cookie(cookie)
                    added_count += 1
            except WebDriverException as e:
                failed_count += 1
                logger.warning(f"[WARN] 쿠키 추가 실패 (무시): {e}")
                pass
        
        # 4. 쿠키 추가 결과 로그
        logger.info(f"[INFO] 쿠키 추가 완료: 성공 {added_count}개, 실패 {failed_count}개")
        
        if added_count == 0:
            logger.warning("[WARN] 추가된 쿠키가 없습니다. 1차 로그인을 진행합니다.")
            return False
        
        # 5. 페이지 새로고침으로 쿠키 적용
        driver.refresh()
        logger.info(f"[INFO] 쿠키 복원 완료: {cookie_path}")
        logger.info("[INFO] 쿠키 기반 자동 로그인을 시도합니다.")
        
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"[ERROR] 쿠키 파일 형식 오류: {e}")
        logger.info("[INFO] 손상된 쿠키 파일입니다. 1차 로그인을 진행합니다.")
        return False
        
    except Exception as e:
        logger.error(f"[ERROR] 쿠키 로드 실패: {e}")
        logger.info("[INFO] 쿠키 복원 실패. 1차 로그인을 진행합니다.")
        return False



def check_2fa_required(driver):
    """
    2차 인증 페이지가 나타났는지 확인합니다.
    
    Returns:
        bool: 2차 인증이 필요한 경우 True
    """
    try:
        current_url = driver.current_url
        
        # 1. URL에 2차 인증 관련 페이지 패턴 포함 여부 체크
        if "validation_welcome" in current_url or "validation" in current_url:
            logger.info("[INFO] 2차 인증 페이지 URL 감지: " + current_url)
            return True
        
        # 2. XPath 기반 2차 인증 요소 존재 여부 확인
        two_fa_keys = ['sms_but', 'sms_input_space', 'sms_input_submit']
        
        for key in two_fa_keys:
            xpath = xpath_dict.get(key)  # XPath 가져오기
            if xpath and driver.find_elements(By.XPATH, xpath):
                logger.info(f"[INFO] 2차 인증 요소 감지: {key} ({xpath})")
                return True
        
        return False
        
    except Exception as e:
        logger.warning(f"[WARN] 2차 인증 확인 중 오류: {e}")
        return False


def handle_2fa_authentication(driver):
    """
    2차 인증을 자동 처리합니다.

    단계별 작업:
    1. '문자로 받기' 버튼 클릭
    2. 사용자 인증번호 입력 요청
    3. 인증번호 입력창에 입력 처리
    4. '다시 묻지 않기' 선택 (선택적)
    5. '인증번호 확인' 버튼 클릭
    6. 인증 완료 후 홈 화면 진입 확인

    Returns:
        bool: 인증 성공 여부
    """
    try:
        sms_button_xpath = xpath_dict.get('sms_but')
        if not sms_button_xpath:
            logger.error("[ERROR] XPath 'sms_but' 정의 누락")
            return False

        if driver.find_elements(By.XPATH, sms_button_xpath):
            x_path_send_keys(driver, sms_button_xpath, Keys.RETURN)
            logger.info("[INFO] '문자로 받기' 버튼 클릭 완료")
            time.sleep(3)
        else:
            logger.warning("[WARN] '문자로 받기' 버튼 미발견")
            return False

        auth_code = input("[입력 필요] 핸드폰으로 전송된 인증번호 입력: ")
        if not auth_code:
            logger.error("[ERROR] 인증번호 미입력")
            return False

        logger.info(f"[INFO] 입력된 인증번호: {auth_code}")

        code_input_xpath = xpath_dict.get('sms_input_space')
        if not code_input_xpath:
            logger.error("[ERROR] XPath 'sms_input_space' 정의 누락")
            return False

        if driver.find_elements(By.XPATH, code_input_xpath):
            x_path_send_keys(driver, code_input_xpath, auth_code)
            logger.info("[INFO] 인증번호 입력 완료")
            time.sleep(1)
        else:
            logger.warning("[WARN] 인증번호 입력창 미발견")
            return False

        dont_ask_again_xpath = xpath_dict.get('다시묻지않기')
        if dont_ask_again_xpath and driver.find_elements(By.XPATH, dont_ask_again_xpath):
            try:
                x_path_send_keys(driver, dont_ask_again_xpath, Keys.SPACE)
                logger.info("[INFO] '다시 묻지 않기' 체크 완료")
                time.sleep(0.5)
            except Exception as e:
                logger.warning(f"[WARN] '다시 묻지 않기' 클릭 오류: {e}")

        confirm_button_xpath = xpath_dict.get('sms_input_submit')
        if not confirm_button_xpath:
            logger.error("[ERROR] XPath 'sms_input_submit' 정의 누락")
            return False

        if driver.find_elements(By.XPATH, confirm_button_xpath):
            x_path_send_keys(driver, confirm_button_xpath, Keys.RETURN)
            logger.info("[INFO] '인증번호 확인' 버튼 클릭 완료")
            time.sleep(3)
        else:
            logger.warning("[WARN] '인증번호 확인' 버튼 미발견")
            return False

        if "band.us/home" in driver.current_url or "band.us/band" in driver.current_url:
            logger.info("[INFO] 2차 인증 완료, 홈 화면 진입 성공")
            return True
        else:
            logger.warning("[WARN] 2차 인증 후 홈 화면 진입 실패")
            return False

    except Exception as e:
        logger.error(f"[ERROR] 2차 인증 처리 중 예외 발생: {e}")
        return False


def login(driver):
    """
    네이버밴드 로그인 수행

    흐름:
    1. 쿠키 복원 시도 (실패해도 진행)
    2. 로그인 페이지 이동 및 전화번호 입력
    3. 비밀번호 입력
    4. 2차 인증 필요 시 자동 처리
    5. 로그인 완료

    쿠키 저장은 로그인 함수 외부에서 진행
    """
    account_id = driver.selected_mobile

    # 쿠키 복원 시도
    load_cookies(driver)
    time.sleep(1)

    # 로그인 페이지 접속
    driver.get(NAVERBAND_LOGIN_URL)
    time.sleep(2)

    log_in_xpath = xpath_dict.get('log_in')
    if not log_in_xpath:
        logger.error("[ERROR] XPath 'log_in' 미정의")
        return False

    if driver.find_elements(By.XPATH, log_in_xpath):
        x_path_send_keys(driver, log_in_xpath, account_id)
        move_mouse_naturally()
        x_path_send_keys(driver, log_in_xpath, Keys.RETURN)
        logger.info("[INFO] 전화번호 입력 성공")
    else:
        logger.warning("[WARN] 전화번호 입력창 미발견")
        return False

    password_xpath = xpath_dict.get('password')
    if not password_xpath:
        logger.error("[ERROR] XPath 'password' 미정의")
        return False

    if driver.find_elements(By.XPATH, password_xpath):
        x_path_send_keys(driver, password_xpath, id_dict[account_id])
        move_mouse_naturally()
        x_path_send_keys(driver, password_xpath, Keys.RETURN)
        logger.info("[INFO] 비밀번호 입력 성공")
        time.sleep(3)
    else:
        logger.warning("[WARN] 비밀번호 입력창 미발견")
        return False

    # 2차 인증 필요 여부 확인
    if check_2fa_required(driver):
        logger.info("[INFO] 2차 인증 필요, 자동 처리 시작")
        if not handle_2fa_authentication(driver):
            logger.error("[ERROR] 2차 인증 처리 실패")
            return False
        logger.info("[INFO] 2차 인증 완료")
    else:
        logger.info("[INFO] 2차 인증 없음, 로그인 완료")

    logger.info("[INFO] 로그인 완료, 쿠키 저장은 외부에서 수행 예정")
    return True
