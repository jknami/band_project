# 파일: src/naverband_automation.py
# 역할: 네이버밴드 자동화 핵심 로직 (pyautogui 활용 및 반복문으로 브라우저 컨트롤)

import time
import random
import pyautogui
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.utils import resource_path, get_random_file, x_path_click
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def write_text_from_folder(driver, xpath: str, folder_path: str, wait_time=10, do_clear=True):
    """
    지정 경로에서 랜덤 텍스트파일 내용을 XPath 위치에 입력.
    예외 발생 시 복구URL 이동 없이 print + raise.
    """
    file = get_random_file(folder_path)
    try:
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        time.sleep(0.5)
        text_content = None
        for enc in ('utf-8', 'utf-8-sig', 'cp949'):
            try:
                with open(file, 'r', encoding=enc) as f:
                    text_content = f.read()
                break
            except UnicodeDecodeError:
                continue
        if text_content is None:
            raise UnicodeDecodeError(f"인코딩 모든 시도가 실패했습니다: {file}")
        element = driver.find_element(By.XPATH, xpath)
        if do_clear:
            element.clear()
        element.send_keys(text_content)
        print(f"[INFO] 파일 첨부 성공: {file}")
    except (TimeoutException, NoSuchElementException) as e:
        print(f"[WARN] 텍스트 입력 실패: {xpath}\n에러: {e}")
        raise
    except FileNotFoundError as e:
        print(f"[ERROR] 파일 없음: {file}\n에러: {e}")
        raise
    except UnicodeDecodeError as e:
        print(f"[ERROR] 인코딩 실패: {file}\n에러: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] 알 수 없는 예외: {e}")
        raise


def upload_file_from_folder(driver, folder_path: str, wait_time=10):
    """
    지정 폴더 내 랜덤 파일(.gif, .jpg 등)을 input[type='file'] 요소에 첨부
    예외 발생 시 홈으로 가지 않고, print 후 raise.
    """
    file_path = get_random_file(folder_path)
    try:
        wait = WebDriverWait(driver, wait_time)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='file']")))
        file_input = driver.find_element(By.CSS_SELECTOR, "input[type='file']")
        file_input.send_keys(file_path)
        print(f"[INFO] 파일 첨부 성공: {file_path}")
    except (TimeoutException, NoSuchElementException) as e:
        print(f"[WARN] 파일 첨부 실패: input[type='file']\n에러: {e}")
        raise
    except FileNotFoundError as e:
        print(f"[ERROR] 첨부파일 없음: {file_path}\n에러: {e}")
        raise
    except Exception as e:
        print(f"[ERROR] 알 수 없는 예외: {e}")
        raise



def process_band(driver, xpath_dict, band, TXT_DIR, IMAGE_DIR):
    """
    단일 밴드에 대해 각 자동화 작업을 수행하는 함수입니다.
    각 단계에는 네이버밴드 게시글 작성의 실제 플로우와 일치하는 상세 주석을 달았습니다.
    Args:
        driver: Selenium 브라우저 객체
        xpath_dict: 주요 버튼의 XPath 정보를 담아둔 딕셔너리
        band: 현재 반복에서 조작할 밴드 XPath
        TXT_DIR: 게시글에 사용할 텍스트 파일 폴더 경로
        IMAGE_DIR: 업로드할 이미지 폴더 경로
    """

    # 1. 밴드(XPATH) 클릭: 네이버밴드 홈에서 해당 밴드 페이지로 이동
    x_path_click(driver, band)
    time.sleep(random.uniform(1, 3))  # 사람처럼 보이도록 랜덤 대기

    # 2. 글쓰기 버튼 클릭: 밴드 내 게시글 작성/업로드 창 열기
    x_path_click(driver, xpath_dict['글쓰기_1'])
    time.sleep(random.uniform(1, 3))

    # 3. 게시글 내용 입력: 지정 텍스트 파일 내용을 해당 입력창에 send_keys
    write_text_from_folder(driver, xpath_dict['글쓰기_2'], TXT_DIR)
    time.sleep(random.uniform(1, 3))

    # 4. 이미지 업로드: IMAGE_DIR에서 랜덤 이미지를 선택해 input[type='file']에 첨부
    upload_file_from_folder(driver, IMAGE_DIR)
    time.sleep(random.uniform(1, 3))

    # 5. 이미지 첨부 버튼 클릭: 첨부한 파일을 게시글 본문에 실제로 첨부
    x_path_click(driver, xpath_dict['이미지첨부'])
    time.sleep(random.uniform(1, 3))

    # 6. 게시 버튼 클릭: 게시글+이미지 업로드 최종 제출/게시하기
    x_path_click(driver, xpath_dict['이미지게시'])
    time.sleep(random.uniform(1, 3))

    # 7. 홈으로 복귀: 모든 게시 작업을 마친 뒤 네이버밴드 홈 화면으로 돌아가기
    x_path_click(driver, xpath_dict['홈'])
    time.sleep(random.uniform(1, 3))

def roof_bands(
    driver, 
    xpath_dict, 
    BAND_LIST, 
    TXT_DIR, 
    IMAGE_DIR, 
    URL_MODES, 
    MAX_ERROR_CNT=3
):
    """
    밴드 전체 반복 업로드/예외관리 루프 함수 (모듈화 예시)
    Args:
        driver: selenium webdriver 객체
        xpath_dict: 각 버튼 xpath정보
        BAND_LIST: 전체 밴드 리스트
        TXT_DIR: 텍스트 파일 디렉토리
        IMAGE_DIR: 이미지 파일 디렉토리
        URL_MODES: URL 구분 dict
        MAX_ERROR_CNT: 연속 오류 허용 횟수
    Returns:
        실패한 밴드 리스트
    """
    import random, time
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.common.alert import Alert
    from selenium.webdriver.common.keys import Keys

    band_list = BAND_LIST.copy()
    random.shuffle(band_list)
    error_cnt = 0
    log_failed_bands = []

    for row, band in enumerate(band_list[:]):
        try:
            process_band(driver, xpath_dict, band, TXT_DIR, IMAGE_DIR)
            error_cnt = 0
        except Exception as exception:
            print(f"[WARN] {row+1}번째 밴드 실패: {type(exception)}")
            error_cnt += 1
            log_failed_bands.append(band)
            # 복구 루틴
            try:
                ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                time.sleep(1)
                alert = Alert(driver)
                alert.accept()
            except Exception as e:
                print("[INFO] 복구 중 추가 에러:", e)
            # 에러 누적이면 홈 복구
            if error_cnt >= MAX_ERROR_CNT:
                print(f"[CRITICAL] {MAX_ERROR_CNT}회 연속 에러! 홈으로 복구합니다.")
                driver.get(URL_MODES.get("home", "/home"))
                time.sleep(2)
                error_cnt = 0
        finally:
            band_list.remove(band)
            rand_sleep = random.randrange(5, 15)
            print(f'{row+1}번째 upload완료, {len(band_list)}개 밴드 대기 / {rand_sleep}초간 중지')
            time.sleep(rand_sleep)

    print("작업 실패 밴드:", log_failed_bands)
    return log_failed_bands
