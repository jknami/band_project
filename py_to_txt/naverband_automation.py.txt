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
from selenium.common.exceptions import UnexpectedAlertPresentException, NoAlertPresentException
from selenium.webdriver.common.keys import Keys
from src.utils import (resource_path,
    get_random_file, x_path_click, human_delay, move_mouse_naturally, focus_window, logger)
from config import *
from resources.xpath_dict import xpath_dict
from src.utils import realistic_typing, safe_xpath_click, x_path_human_click

def write_text_from_folder(driver, xpath: str, folder_path: str, wait_time=10, do_clear=True):
    """
    지정된 폴더 내 랜덤 텍스트 파일에서 내용을 읽어 해당 xpath 텍스트 입력란에 현실적인 타이핑 패턴으로 자동 입력합니다.

    Args:
        driver: Selenium WebDriver 객체
        xpath: 텍스트 입력란 xpath
        folder_path: 텍스트 파일이 위치한 폴더 경로
        wait_time: 요소 대기 시간(초), 기본 10초
        do_clear: 기존 텍스트를 지울지 여부, 기본 True

    Raises:
        UnicodeDecodeError: 텍스트 인코딩 실패 시 발생
        Exception: 그 외 예외 발생 시 로그 및 스크린샷 후 예외 재발생
    """
    file = get_random_file(folder_path)
    try:
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        element = driver.find_element(By.XPATH, xpath)

        if do_clear:
            try:
                element.clear()
            except Exception as e:
                logger.warning(f"[WARN] 텍스트 입력 전 클리어 실패: {e}")

        human_delay('click')  # 클릭 전 자연 딜레이 삽입
        element.click()
        time.sleep(random.uniform(0.3, 1.1))  # 클릭 후 자연스러운 대기

        text_content = None
        for encoding in ('utf-8', 'utf-8-sig', 'cp949'):
            try:
                with open(file, 'r', encoding=encoding) as f:
                    text_content = f.read()
                break
            except UnicodeDecodeError:
                continue

        if text_content is None:
            raise UnicodeDecodeError(f"모든 인코딩 시도 실패: {file}")

        text_content = text_content.strip()
        if len(text_content) > 1600:
            text_content = text_content[:random.randint(1200, 1500)]

        realistic_typing(element, text_content)
        logger.info(f"[INFO] 본문 자동 입력 성공: {file}")

    except Exception as e:
        # 에러 시 스크린샷과 로그 기록
        driver.save_screenshot("input_error_debug.png")
        logger.error(f"[ERROR] 본문 입력 실패: {file}\n에러: {e}")
        raise

def upload_file_from_folder(driver, folder_path: str, wait_time=10):
    """
    지정 폴더 내 랜덤 파일(.gif, .jpg 등)을 input[type='file'] 요소에 첨부
    예외 발생 시 홈으로 가지 않고, print 후 raise.
    """
    file_path = get_random_file(folder_path)
    move_mouse_naturally()
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
    """
    밴드 작업을 사람 행동처럼 자연스럽게 수행
    """
    # 브라우저 창 포커스 유지 (윈도우창 제목 예시)
    focus_window("band")

    # 마우스 자연 이동 후 밴드 클릭
    move_mouse_naturally()
    x_path_click(driver, band)
    human_delay("click")

    # 글쓰기 버튼 클릭 + 고민 시간
    human_delay("thinking")
    x_path_human_click(driver, xpath_dict['글쓰기_1'])

    # 텍스트 입력 (느린 타이핑 포함)
    write_text_from_folder(driver, xpath_dict['글쓰기_2'], TXT_DIR)
    human_delay("typing")

    # 이미지 업로드 + 대기
    upload_file_from_folder(driver, IMAGE_DIR)
    human_delay("upload")

    # 이미지 첨부 클릭 (마우스 이동 포함)
    move_mouse_naturally()
    x_path_click(driver, xpath_dict['이미지첨부'])
    human_delay("click")

    # 게시하기 클릭 + 생각시간
    x_path_click(driver, xpath_dict['이미지게시'])
    human_delay("thinking")

    # 화면 스크롤 후 홈으로 돌아가기
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

from src.utils import go_home
def roof_bands(driver, xpath_dict, BAND_LIST, TXT_DIR, IMAGE_DIR, MAX_ERROR_CNT=3, mobile_num=None):
    band_list = BAND_LIST.copy()
    random.shuffle(band_list)
    error_cnt = 0
    log_failed_bands = []

    for row, band in enumerate(band_list[:]):
        try:
            # process_band 내에서 복구는 하지 않고, 예외를 상위로 던짐
            process_band(driver, xpath_dict, band, TXT_DIR, IMAGE_DIR)
            error_cnt = 0

        except UnexpectedAlertPresentException:
            try:
                alert = Alert(driver)
                alert.accept()
                logger.info(f"{row + 1}번째 밴드: alert 자동 닫기 성공")
                human_delay("thinking")
            except NoAlertPresentException:
                logger.warning(f"{row + 1}번째 밴드: alert 존재하지 않음")
            except Exception as e:
                logger.error(f"{row + 1}번째 밴드: alert 처리 에러: {e}")
            error_cnt += 1
            if band not in log_failed_bands:
                log_failed_bands.append(band)

            # 홈 복귀 처리 - 상위에서 관리
            try:
                go_home(driver, xpath_dict)
            except Exception as recover_e:
                logger.error(f"[복구 실패] 홈 복귀 실패: {recover_e}")

        except Exception as e:
            logger.warning(f"{row + 1}번째 밴드 실패: {type(e)} - {e}")
            error_cnt += 1
            if band not in log_failed_bands:
                log_failed_bands.append(band)

            try:
                go_home(driver, xpath_dict)
            except Exception as recover_e:
                logger.error(f"[복구 실패] 홈 복귀 실패: {recover_e}")

        finally:
            if error_cnt >= MAX_ERROR_CNT:
                logger.critical(f"연속 {MAX_ERROR_CNT}회 실패 발생! 관리자 개입 필요")
                # 필요시 관리자 알림 콜 등 추가 가능
                error_cnt = 0

            band_list.remove(band)
            sleep_time = random.randint(5, 15)
            logger.info(f"{row + 1}번째 밴드 작업 완료, 남은 밴드: {len(band_list)}, {sleep_time}초 대기 중")
            time.sleep(sleep_time)
            move_mouse_naturally()

    logger.info(f"roof_bands 실패 밴드 리스트: {log_failed_bands}")
    return log_failed_bands

