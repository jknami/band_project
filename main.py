# main.py
import logging
from logging.handlers import RotatingFileHandler
import os
import pyautogui    # prompt 입력에 필요
import time         # sleep, 시간 계산 등에 필요
import random       # rand_sleep, 셔플 등에 필요
from selenium.webdriver.common.alert import Alert   # Alert 처리 필요
from selenium.webdriver.common.keys import Keys     # 키입력(ESC, ENTER)에 필요

from src.chrome_manager import select_mobile_and_get_driver
from src.account_manager import login, save_cookies
from src.utils import x_path_click, move_mouse_naturally
from resources.xpath_dict import xpath_dict, id_dict
from src.naverband_automation import roof_bands, perform_logout
from config import *

def setup_logging():
    """
    프로그램 전체의 로깅을 초기화합니다.
    - 파일: logs/band_project.log (DEBUG 레벨, 10MB 순환, 최대 10개 보관)
    - 콘솔: INFO 레벨 이상만 출력
    """
    # logs 폴더 생성
    os.makedirs("logs", exist_ok=True)
    
    # 루트 로거 설정
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # 파일 핸들러 - 모든 로그 상세 기록
    file_handler = RotatingFileHandler(
        'logs/band_project.log',
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_formatter)
    
    # 콘솔 핸들러 - 중요한 정보만 출력
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('[%(levelname)s] %(message)s')
    console_handler.setFormatter(console_formatter)
    
    # 핸들러 추가
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    

    
def main():
    logger = logging.getLogger(__name__)
    """메인 실행 함수"""
    driver = None
    mobile = None
    
    try:
        logger.info("=" * 60)
        logger.info("🚀 프로그램 시작")
        logger.info("=" * 60)
        
        # ===== 1. 드라이버 초기화 =====
        mobile, driver = select_mobile_and_get_driver()
        logger.info(f"✅ {mobile} 계정으로 브라우저 실행됨")
        
        # ===== 2. 로그인 =====
        login(driver)
        logger.info("✅ 로그인 완료")
        
        # ===== 3. 실행 시간 입력 (입력 검증) =====
        while True:
            p_time = pyautogui.prompt(
                title="실행시간",
                default='1',
                text="시간을 입력하세요 (예: 1 = 1시간, 0.5 = 30분)"
            )
            
            # 취소 버튼 처리
            if p_time is None:
                logger.warning("⚠️  사용자가 취소를 눌렀습니다")
                return
            
            # 입력 검증
            try:
                p_time_float = float(p_time)
                if p_time_float <= 0:
                    pyautogui.alert("0보다 큰 숫자를 입력하세요!", "입력 오류")
                    continue
                break
            except ValueError:
                pyautogui.alert("숫자만 입력 가능합니다!", "입력 오류")
                continue
        
        # ===== 4. 시간 계산 =====
        e_time = time.time() + 60 * 60 * p_time_float
        
        start_time = time.strftime('%p %I시%M분%S초', time.localtime())
        end_time = time.strftime('%p %I시%M분%S초', time.localtime(e_time))
        
        logger.info("=" * 60)
        logger.info(f"📱 계정: {mobile}")
        logger.info(f"🕐 시작 시간: {start_time}")
        logger.info(f"🕐 종료 예정: {end_time}")
        logger.info(f"⏱️  실행 시간: {p_time_float}시간")
        logger.info("=" * 60)
        
        # ===== 5. 밴드 순회 반복 =====
        rotation_count = 0
        
        while time.time() < e_time:
            rotation_count += 1
            
            logger.info("=" * 60)
            logger.info(f"🔄 {rotation_count}회차 밴드 순회 시작")
            logger.info("=" * 60)
            
            # 밴드 순회 실행
            failed_bands = roof_bands(
                driver=driver,
                xpath_dict=xpath_dict,
                BAND_LIST=BAND_LIST,
                TXT_DIR=TXT_DIR,
                IMAGE_DIR=IMAGE_DIR,
                mobile_num=mobile
            )
            
            logger.info(f"✅ {rotation_count}순환 완료 (실패: {len(failed_bands)}개)")
            
            # 남은 시간 확인
            if time.time() < e_time:
                # 다음 회차 전 휴식
                rand_sleep = random.randint(10, 20)
                move_mouse_naturally()
                
                restart_time = time.strftime(
                    '%p %I시%M분',
                    time.localtime(time.time() + rand_sleep)
                )
                
                logger.info("-" * 60)
                logger.info(f"😴 {rotation_count+1}회차 시작, {rand_sleep}초간 휴식")
                logger.info(f"🔄 {restart_time}에 다시 시작합니다")
                logger.info("-" * 60)
                
                time.sleep(rand_sleep)
        
        # ===== 6. 정상 종료 =====
        logger.info("=" * 60)
        logger.info(f"🎉 예정된 시간 종료!")
        logger.info(f"📊 총 {rotation_count}회 순회 완료")
        logger.info("=" * 60)
    
    except KeyboardInterrupt:
        logger.warning("⚠️  사용자가 프로그램을 중단했습니다 (Ctrl+C)")
    
    except Exception as e:
        logger.error(f"❌ 프로그램 실행 중 예외 발생: {e}", exc_info=True)
    
    finally:
        # ===== 7. 종료 처리 =====
        if driver is not None:
            try:
                logger.info("=" * 60)
                logger.info("🔄 종료 처리 중...")
                logger.info("=" * 60)
                
                # 로그아웃
                perform_logout(driver)
                logger.info("✅ 로그아웃 완료")
                
                # 쿠키 저장
                if mobile:
                    save_cookies(driver, mobile)
                    logger.info(f"✅ {mobile} 쿠키 저장 완료")
                
                # 브라우저 종료
                driver.quit()
                logger.info("✅ 브라우저 종료 완료")
                
                # 최종 메시지
                close_time = time.strftime('%p %I시%M분%S초', time.localtime())
                logger.info("=" * 60)
                logger.info(f"🎉 {mobile} 프로젝트가 {close_time}에 완료되었습니다")
                logger.info("=" * 60)
                
            except Exception as e:
                logger.error(f"❌ 종료 처리 중 예외 발생: {e}", exc_info=True)
        else:
            logger.warning("⚠️  driver가 초기화되지 않았습니다")
if __name__ == "__main__":
    setup_logging()  # 가장 먼저 로깅 초기화
    main()