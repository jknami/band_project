import logging
logger = logging.getLogger(__name__)
import os
import json
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, NoSuchElementException
import pyautogui
from config import NAVERBAND_LOGIN_URL

from src.chrome_manager import select_mobile_and_get_driver
mobile, driver = select_mobile_and_get_driver()
from src.utils import *
from src.naverband_automation import *

def process_band(driver, xpath_dict, band, TXT_DIR, IMAGE_DIR):
    """
    단일 밴드 작업 수행
    - 예외 발생 시: raise로 상위에 전달
    - 복구 책임 없음
    """
    logger.debug(f"밴드 작업 시작: {band}")
    # 각 단계별 상세 로깅 (디버깅용)
    focus_window("band")
    move_mouse_naturally()
    x_path_click(driver, band)
    logger.debug("밴드 클릭 완료")
    
    human_delay("thinking")
    
    x_path_human_click(driver, xpath_dict['글쓰기_1'])
    logger.debug("글쓰기 버튼 클릭 완료")
    
    write_text_from_folder(driver, xpath_dict['글쓰기_2'], TXT_DIR)
    logger.debug("텍스트 입력 완료")
    
    human_delay("typing")
    
    upload_file_from_folder(driver, IMAGE_DIR)
    logger.debug("이미지 업로드 완료")
    
    human_delay("upload")
    move_mouse_naturally()
    
    x_path_click(driver, xpath_dict['이미지첨부'])
    logger.debug("이미지 첨부 버튼 클릭 완료")
    
    human_delay("click")
    
    x_path_click(driver, xpath_dict['이미지게시'])
    logger.info(f"밴드 게시 완료: {band}")
    
    human_delay("thinking")
    driver.execute_script("window.scrollBy(0, window.innerHeight / 3)")
    human_delay("scroll")
    
    x_path_click(driver, xpath_dict['홈'])
    logger.debug("홈으로 복귀")
    human_delay("scroll")
    
    # ✅ 예외는 raise로 상위로 전달
    # ✅ 복구 시도 없음
    
from selenium.common.exceptions import (
    TimeoutException, NoSuchElementException, ElementNotInteractableException,
    StaleElementReferenceException, WebDriverException, UnexpectedAlertPresentException,
    ElementClickInterceptedException, InvalidSessionIdException, NoSuchWindowException
)
from selenium.webdriver.common.alert import Alert

def safe_go_home(driver, xpath_dict, max_retries=2):
    """안전하게 홈으로 복귀"""
    for attempt in range(max_retries):
        try:
            logger.debug(f"홈 복귀 시도 {attempt + 1}/{max_retries}")
            
            # 방법 1: 홈 버튼 클릭
            try:
                x_path_click(driver, xpath_dict['홈'])
                time.sleep(2)
                logger.info("✅ 홈 버튼으로 복귀")
                return True
            except Exception as e:
                logger.warning(f"홈 버튼 실패: {e}")
                
                # 방법 2: URL로 직접 이동
                try:
                    from config import NAVERBAND_URL
                    driver.get(NAVERBAND_URL)
                    time.sleep(3)  # 페이지 로드 대기
                    logger.info("✅ URL로 홈 복귀")
                    return True
                except Exception as e2:
                    logger.warning(f"URL 이동 실패: {e2}")
                    
        except Exception as e:
            logger.error(f"홈 복귀 오류: {e}")
            
        if attempt < max_retries - 1:
            time.sleep(2)
    
    logger.error("❌ 홈 복귀 최종 실패")
    return False


n = 1
error_count = 0  # 연속 에러 카운트
MAX_CONSECUTIVE_ERRORS = 3  # 연속 3번 실패하면 중단

for band in BAND_LIST:
    try:
        logger.info(f"[{n}] 밴드 시작: {band}")
        process_band(driver, xpath_dict, band, TXT_DIR, IMAGE_DIR)
        
        # 성공하면 에러 카운트 초기화
        error_count = 0
        logger.info(f"[{n}] ✅ 성공")
        
    except UnexpectedAlertPresentException:
        logger.warning(f"[{n}] ⚠️  Alert 팝업")
        error_count += 1
        try:
            Alert(driver).accept()
            logger.info("Alert 닫기 완료")
        except:
            pass
        safe_go_home(driver, xpath_dict)
        
    except TimeoutException:
        logger.warning(f"[{n}] ⏱️  타임아웃")
        error_count += 1
        safe_go_home(driver, xpath_dict)
        
    except NoSuchElementException:
        logger.warning(f"[{n}] 🔍 요소 없음")
        error_count += 1
        safe_go_home(driver, xpath_dict)
        
    except ElementNotInteractableException:
        logger.warning(f"[{n}] 🚫 요소 클릭 불가")
        error_count += 1
        safe_go_home(driver, xpath_dict)
        
    except ElementClickInterceptedException:
        logger.warning(f"[{n}] 🛑 클릭 방해")
        error_count += 1
        safe_go_home(driver, xpath_dict)
        
    except StaleElementReferenceException:
        logger.warning(f"[{n}] 🔄 요소 오래됨")
        error_count += 1
        safe_go_home(driver, xpath_dict)
        
    except (InvalidSessionIdException, NoSuchWindowException):
        logger.critical(f"[{n}] 💥 브라우저 종료됨")
        break
        
    except WebDriverException as e:
        logger.error(f"[{n}] 🔧 WebDriver 오류: {e}")
        error_count += 1
        
        # Windows 오류 특별 처리
        if "Error code from Windows" in str(e):
            logger.warning("⚠️  Windows API 오류 감지, 브라우저 새로고침 시도")
            try:
                driver.refresh()
                time.sleep(3)
            except:
                pass
        
        safe_go_home(driver, xpath_dict)
        
    except Exception as e:
        logger.error(f"[{n}] ❌ 예상치 못한 오류: {e}")
        error_count += 1
        safe_go_home(driver, xpath_dict)
    
    finally:
        print(f'{n}번째 밴드 완료')
        n += 1
        
        # 연속 에러 체크
        if error_count >= MAX_CONSECUTIVE_ERRORS:
            logger.critical(f"🚨 연속 {error_count}회 실패! 프로그램 중단")
            break
        
        # 다음 밴드 전 대기
        if n <= len(BAND_LIST):
            time.sleep(3)  # 대기 시간 늘림

logger.info("=== 밴드 순회 완료 ===")
