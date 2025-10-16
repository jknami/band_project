# 파일: src/account_manager.py
# 역할: 여러 계정의 쿠키 저장·로드 및 로그인 처리
# 수정: driver.selected_mobile 사용, id_dict에서 비밀번호 로드, xpath_dict 사용

import os
import pickle
import time
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from config import COOKIE_DIRNAME, NAVERBAND_LOGIN_URL
from src.utils import resource_path, ensure_dir, get_cookie_path, x_path_click, x_path_send_keys, logger, move_mouse_naturally
from resources.xpath_dict import xpath_dict, id_dict
from selenium.webdriver.support.ui import WebDriverWait

def save_cookies(driver: webdriver.Chrome):
    """
    현재 브라우저 세션의 쿠키를 account_id별 폴더에 저장합니다.
    """
    account_id = driver.selected_mobile
    cookie_dir = get_cookie_path(account_id)
    cookie_path = os.path.join(cookie_dir, "cookies.pkl")
    with open(cookie_path, 'wb') as f:
        pickle.dump(driver.get_cookies(), f)

def load_cookies(driver: webdriver.Chrome):
    """
    계정별로 저장된 쿠키(cookies.pkl)를 읽어서
    쿠키의 domain에 따라 브라우저를 해당 도메인 페이지에 이동시킨 뒤
    알맞은 쿠키만 add_cookie로 추가합니다.
    도메인 불일치(InvalidCookieDomainException) 방지를 위한 확장 패턴입니다.
    """
    # 브라우저가 어떤 계정(전화번호)으로 실행 중인지 가져옴
    account_id = driver.selected_mobile
    
    # 해당 계정의 쿠키 파일 경로 생성 (ex: D:/coding/login/accounts/01075381965/cookies/cookies.pkl)
    cookie_path = os.path.join(get_cookie_path(account_id), "cookies.pkl")
    
    # 쿠키 파일이 존재하면 처리 시작
    if os.path.exists(cookie_path):
        # 쿠키 파일 읽기
        with open(cookie_path, 'rb') as f:
            cookies = pickle.load(f)
        
        # 도메인 처리 관련 코드는 현재 주석처리, 추후 프록시/도메인 구축 시 복구
        """
        # 쿠키 내 모든 domain 종류 추출 (set으로 중복 제거)
        domains = set([c['domain'] for c in cookies])
        
        # domain별로 반복하며,
        for domain in domains:
            # 브라우저를 해당 도메인 홈으로 이동 (ex: 'www.band.us' -> 'https://www.band.us/')
            url = f"https://{domain.lstrip('.')}/"
            driver.get(url)
            time.sleep(1)  # 페이지가 완전히 열린 뒤 처리
            
            # 현재 도메인에 해당하는 쿠키만 찾아서 추가
            for cookie in [c for c in cookies if c['domain'] == domain]:
                try:
                    driver.add_cookie(cookie)  # 쿠키 추가
                    logger.info(f"[INFO] 쿠키 추가 성공: {cookie['domain']} ({cookie.get('name')})")
                except Exception as ex:
                    logger.warning(f"[WARN] 쿠키 추가 실패(domain={domain}, name={cookie.get('name')}): {ex}")
        """
        logger.info("[쿠키 복원] 현재 도메인/프록시 기능이 활성화되지 않아 쿠키 주입은 건너뜁니다. 환경 구축 후 주석 해제 필요.")
    else:
        logger.info("[쿠키 복원] 쿠키 파일이 존재하지 않아 건너뜀.")

def login(driver: webdriver.Chrome):
    """
    네이버밴드 계정 자동 로그인 (쿠키 복원, 입력창 확인, 자동 입력).
    쿠키 저장은 자동화 전체 작업이 끝난 뒤(로그아웃 후)에만 수행!
    """
    account_id = driver.selected_mobile
    wait = WebDriverWait(driver, 10)

    # 1. 쿠키 인증 복원(도메인별 add_cookie)
    load_cookies(driver)
    time.sleep(1)

    # 2. 로그인 페이지로 이동
    driver.get(NAVERBAND_LOGIN_URL)
    time.sleep(2)

    # 3. 전화번호 입력창(XPath) 실존 체크
    log_in_xpath = xpath_dict['log_in']
    if driver.find_elements(By.XPATH, log_in_xpath):
        x_path_send_keys(driver, log_in_xpath, account_id)
        move_mouse_naturally()
        x_path_send_keys(driver, log_in_xpath, Keys.RETURN)
        logger.info("[INFO] 전화번호 입력 성공")
    else:
        logger.warning("[WARN] 입력창 없음(자동 인증/사이트 구조 변경 등)")
        return

    # 4. 비밀번호 입력도 동일하게 처리
    password_xpath = xpath_dict['password']
    if driver.find_elements(By.XPATH, password_xpath):
        x_path_send_keys(driver, password_xpath, id_dict[account_id])
        move_mouse_naturally()
        x_path_send_keys(driver, password_xpath, Keys.RETURN)
        logger.info("[INFO] 비밀번호 입력 성공")
    else:
        logger.warning("[WARN] 비밀번호 입력창 없음!")
        return

