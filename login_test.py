# 파일: main.py
# 역할: 전체 자동화 프로세스 실행 진입점

import time  # 시간 지연
from src.chrome_manager import select_mobile_and_get_driver  # 전화번호 선택 및 드라이버 생성
from src.account_manager import login, save_cookies  # 로그인 및 쿠키 저장
from src.utils import logger  # 로깅 함수

def main():
    """
    네이버밴드 자동화 메인 함수
    1. 전화번호 선택 및 드라이버 생성
    2. 로그인 수행 (쿠키 복원 포함)
    3. 자동화 작업 수행 (밴드 순회 등)
    4. 작업 종료 후 쿠키 저장
    5. 브라우저 종료
    """
    driver = None  # 드라이버 초기화
    
    try:
        # 1. 전화번호 선택 및 크롬 드라이버 생성
        mobile_num, driver = select_mobile_and_get_driver()  # pyautogui 팝업으로 전화번호 선택
        logger.info(f"[INFO] {mobile_num} 계정으로 드라이버 생성 완료")
        
        # 2. 로그인 수행 (쿠키 복원 시도 포함)
        login(driver)  # account_manager의 login 함수 호출
        logger.info("[INFO] 로그인 완료")
        
        # 3. 자동화 작업 수행 (예: 밴드 순회, 게시글 작성 등)
        # 여기에 실제 자동화 로직 추가
        # 예: rotate_bands(driver), post_content(driver) 등
        
        time.sleep(5)  # 임시 대기 (실제 작업으로 대체)
        logger.info("[INFO] 자동화 작업 완료")
        
        # 4. 작업 종료 후 쿠키 저장 (세션 유지용)
        save_cookies(driver)  # 현재 세션 쿠키 JSON으로 저장
        logger.info("[INFO] 쿠키 저장 완료")
        
    except Exception as e:
        logger.error(f"[ERROR] 메인 프로세스 오류 발생: {e}")
    
    finally:
        # 5. 브라우저 종료
        if driver:
            input("아무 키나 누르면 브라우저를 종료합니다...")
            driver.quit()  # 드라이버 종료
            logger.info("[INFO] login완료")


if __name__ == "__main__":
    main()  # 메인 함수 실행
