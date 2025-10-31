# 파일: src/naverband_automation.py
# 역할: 네이버밴드 자동화 핵심 로직 (pyautogui 활용 및 반복문으로 브라우저 컨트롤)

import time
import random
import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.alert import Alert
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException, InvalidSessionIdException, NoSuchWindowException
from selenium.webdriver.common.keys import Keys
from src.utils import (resource_path,
    get_random_file, safe_go_home, x_path_click, human_delay, move_mouse_naturally, focus_window)
from config import *
from resources.xpath_dict import xpath_dict
from src.utils import realistic_typing, safe_xpath_click, x_path_human_click
from src.utils import handle_js_alert

import logging
logger = logging.getLogger(__name__)

def write_text_from_folder(driver, xpath: str, folder_path: str, wait_time=10, do_clear=True, js_alert_action='accept'):
    """
    텍스트 자동 입력 (Alert 발생 시 자동 처리 및 글쓰기 창 닫기)
    """
    from selenium.common.exceptions import UnexpectedAlertPresentException, ElementNotInteractableException
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.by import By
    
    file = get_random_file(folder_path)
    
    try:
        # 텍스트 입력 로직
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        element = driver.find_element(By.XPATH, xpath)

        if do_clear:
            try:
                element.clear()
            except Exception as e:
                logger.warning(f"[WARN] 클리어 실패: {e}")

        element.click()
        time.sleep(random.uniform(0.3, 1.1))

        text_content = None
        for encoding in ('utf-8', 'utf-8-sig', 'cp949'):
            try:
                with open(file, 'r', encoding=encoding) as f:
                    text_content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if text_content is None:
            logger.error(f"인코딩 실패: {file}")
            return False

        text_content = text_content.strip()
        if len(text_content) > 1600:
            text_content = text_content[:random.randint(1200, 1500)]

        realistic_typing(element, text_content)
        logger.info(f"[INFO] 본문 입력 성공: {file}")
        return True

    except (UnexpectedAlertPresentException, ElementNotInteractableException) as e:
        # ✅ Alert 감지 및 처리
        logger.info(f"⚠️  Alert 감지, 자동 처리 중...")
        
        # 1. Alert 처리
        handle_js_alert(driver, action=js_alert_action)
        time.sleep(1)
        
        # 2. 글쓰기 창 닫기
        try:
            driver.find_element(By.TAG_NAME, '//*[@id="wrap"]/div[3]/div/div/section/div/footer/button').send_keys(Keys.ESCAPE)
            time.sleep(1)
            handle_js_alert(driver, action='accept')  # 취소 확인
            logger.info("✅ 글쓰기 창 닫기 완료")
        except Exception as close_err:
            logger.warning(f"글쓰기 창 닫기 실패: {close_err}")
        
        return False
    
    except Exception as e:
        logger.warning(f"⚠️  에러: {type(e).__name__}")
        handle_js_alert(driver, action=js_alert_action)
        
        # 글쓰기 창 닫기
        try:
            driver.find_element(By.TAG_NAME, 'body').send_keys(Keys.ESCAPE)
            time.sleep(1)
            handle_js_alert(driver, action='accept')
        except:
            pass
        
        return False


def upload_file_from_folder(driver, folder_path: str, wait_time=10):
    """
    지정 폴더 내 랜덤 파일(.gif, .jpg 등)을 input[type='file'] 요소에 첨부
    예외 발생 시 홈으로 가지 않고, print 후 raise.
    """
    file_path = get_random_file(folder_path)
    # move_mouse_naturally()
    try:
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        human_delay('upload')
        file_input.send_keys(file_path)
        logger.info(f"[INFO] 파일 첨부 성공: {file_path}")
    except (TimeoutException, NoSuchElementException) as e:
        logger.warning(f"[WARN] 파일 첨부 실패: input[type='file']\n에러: {e}")
        raise
    except FileNotFoundError as e:
        logger.error(f"[ERROR] 첨부파일 없음: {file_path}\n에러: {e}")
        raise
    except Exception as e:
        logger.error(f"[ERROR] 알 수 없는 예외: {e}")
        raise

def process_band(driver, xpath_dict, band, TXT_DIR, IMAGE_DIR):
    
    focus_window("band") # 창 포커스 맞추기가 문제의 핵심이었음
    move_mouse_naturally()
    x_path_click(driver, band)
    human_delay("click")

    human_delay("thinking")
    x_path_human_click(driver, xpath_dict['글쓰기_1'])

    write_text_from_folder(driver, xpath_dict['글쓰기_2'], TXT_DIR)
    human_delay("typing")

    upload_file_from_folder(driver, IMAGE_DIR)
    human_delay("upload")

    # move_mouse_naturally()
    x_path_click(driver, xpath_dict['이미지첨부'])
    human_delay("click")

    x_path_click(driver, xpath_dict['이미지게시'])
    human_delay("thinking")

    driver.execute_script("window.scrollBy(0, window.innerHeight / 3)")
    human_delay("scroll")
    x_path_click(driver, xpath_dict['홈'])
    human_delay("scroll")


def perform_logout(driver):
    """
    안전하게 로그아웃 절차를 수행하는 함수로 분리

    - 순서대로 버튼 클릭
    - 중간중간 sleep으로 안정성 확보
    """
    logger.info("[INFO] 로그아웃 절차 시작")
    try:
        x_path_click(driver, xpath_dict['let_me'])
        human_delay('click')
        x_path_click(driver, xpath_dict['log_out'])
        human_delay('click')
        x_path_click(driver, xpath_dict['log_out_but'])
        human_delay('click')
    except Exception as e:
        logger.error(f"[ERROR] 로그아웃 도중 오류: {e}")


def roof_bands(driver, xpath_dict, BAND_LIST, TXT_DIR, IMAGE_DIR, mobile_num=None):
    """
    밴드 순회 함수
    
    Args:
        driver: Selenium WebDriver
        xpath_dict: XPath 딕셔너리
        BAND_LIST: 밴드 목록
        TXT_DIR: 텍스트 디렉토리
        IMAGE_DIR: 이미지 디렉토리
        mobile_num (str, optional): 계정 번호 (로깅용)
    
    Returns:
        list: 실패한 밴드 목록
    """
    # ===== 초기화 =====
    band_list = BAND_LIST.copy()
    random.shuffle(band_list)
    
    total_bands = len(band_list)
    success_count = 0
    failed_bands = []
    
    # 로깅용 프리픽스
    prefix = f"[{mobile_num}] " if mobile_num else ""
    logger.info(f"{prefix}🚀 밴드 순회 시작 (총 {total_bands}개)")
    
    # ===== 밴드 순회 =====
    while band_list:
        band = band_list[0]
        current = total_bands - len(band_list) + 1
        band_success = False
        
        try:
            logger.info(f"{prefix}[{current}/{total_bands}] 밴드 처리 시작")
            
            # 밴드 처리
            process_band(driver, xpath_dict, band, TXT_DIR, IMAGE_DIR)
            
            # 성공!
            band_success = True
            logger.info(f"{prefix}[{current}] ✅ 성공!")
        
        # ===== 예외 처리 =====
        except UnexpectedAlertPresentException:
            # Alert 팝업 처리
            logger.warning(f"{prefix}[{current}] ⚠️  Alert 팝업 감지")
            
            # ✅ 당신의 함수 사용!
            handle_js_alert(driver, action='accept')
            human_delay("thinking")
            
            # Alert 처리 후 홈 복귀
            try:
                safe_go_home(driver)
            except Exception as home_err:
                logger.error(f"{prefix}홈 복귀 실패: {home_err}")
        
        except Exception as e:
            # 그 외 모든 에러
            error_type = type(e).__name__
            error_msg = str(e)
            logger.warning(f"{prefix}[{current}] ⚠️  에러 ({error_type}): {error_msg[:100]}")
            
            # ✅ 여기서도 Alert 처리 (당신의 함수)
            handle_js_alert(driver, action='accept')
            
            # 홈 복귀 시도
            try:
                safe_go_home(driver)
            except Exception as home_err:
                logger.error(f"{prefix}홈 복귀 실패: {home_err}")
        
        # ===== 후처리 =====
        finally:
            # 성공 여부에 따라 처리
            if band_success:
                band_list.remove(band)
                success_count += 1
            else:
                band_list.remove(band)
                failed_bands.append(band)
            
            # 다음 밴드 전 대기 및 마우스 이동
            if band_list:
                sleep_time = random.randint(5, 15)
                logger.info(f"{prefix}[{current}] 완료, 남은 밴드: {len(band_list)}개, {sleep_time}초 대기")
                time.sleep(sleep_time)
                move_mouse_naturally()
    
    # ===== 결과 요약 =====
    logger.info("=" * 50)
    logger.info(f"{prefix}🎉 밴드 순회 완료!")
    logger.info(f"{prefix}✅ 성공: {success_count}/{total_bands}개")
    logger.info(f"{prefix}❌ 실패: {len(failed_bands)}/{total_bands}개")
    logger.info("=" * 50)
    
    if failed_bands:
        logger.warning(f"{prefix}실패한 밴드 목록: {failed_bands}")
    
    return failed_bands



