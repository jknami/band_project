# 파일: src/chrome_manager.py
# 역할: 전화번호별 크롬 프로필 관리 (User-Agent 기반 자동 버전 매칭)

import os
import time
import json
import pyautogui
import shutil
import logging
from pathlib import Path

import undetected_chromedriver as uc
from selenium_stealth import stealth
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

from config import USER_AGENT, DEFAULT_CHROME_OPTIONS, NAVERBAND_URL, MOBILE_USER_AGENT_MAPPING
from src.utils import get_profile_path, move_mouse_naturally
from resources.xpath_dict import id_dict

logger = logging.getLogger(__name__)


# ===== 1. ChromeDriver 캐시 관리 =====
from src.utils import get_cache_timestamp_file

def should_clear_cache(mobile_num: str, days=7):
    """
    계정별 캐시 삭제 필요 여부 확인
    
    Args:
        mobile_num (str): 전화번호 (예: '01027851965')
        days (int): 캐시 유지 기간 (기본 7일)
    
    Returns:
        bool: True면 캐시 삭제 필요, False면 유지
    """
    cache_file_path = get_cache_timestamp_file(mobile_num)
    cache_file = Path(cache_file_path)
    
    if not cache_file.exists():
        logger.info(f"🔄 [{mobile_num}] ChromeDriver 캐시 초기화 필요")
        return True
    
    try:
        with open(cache_file, 'r') as f:
            last_clear = float(f.read().strip())
        
        elapsed_days = (time.time() - last_clear) / 86400
        
        if elapsed_days >= days:
            logger.info(f"🔄 [{mobile_num}] ChromeDriver 캐시 {elapsed_days:.1f}일 경과, 갱신 필요")
            return True
        else:
            logger.debug(f"✅ [{mobile_num}] ChromeDriver 캐시 유효 ({elapsed_days:.1f}일/{days}일)")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️  [{mobile_num}] 타임스탬프 확인 실패: {e}")
        return True

from src.utils import get_root_dir
def clear_chromedriver_cache(mobile_num: str, chrome_version: int):
    """
    계정별 ChromeDriver 캐시 삭제
    
    Args:
        mobile_num (str): 전화번호
        chrome_version (int): Chrome 버전 (예: 141, 142)
    """
    logger.info(f"🗑️ [{mobile_num}] ChromeDriver 캐시 삭제 중... (Chrome {chrome_version})")
    
    project_root = Path(get_root_dir())
    
    # ✅ 계정별 + 버전별 캐시 경로
    cache_paths = [
        # 1. 프로젝트 폴더 (계정별)
        project_root / f"accounts/{mobile_num}/.chromedriver_cache",
        
        # 2. 시스템 캐시 (버전별)
        Path(os.getenv('LOCALAPPDATA', '')) / f".undetected_chromedriver",
        Path(os.getenv('APPDATA', '')) / f".undetected_chromedriver",
        Path.home() / f".undetected_chromedriver",
        Path(os.getenv('TEMP', '')) / f".undetected_chromedriver",
    ]
    
    deleted_count = 0
    
    for cache_path in cache_paths:
        if cache_path.exists():
            try:
                shutil.rmtree(cache_path)
                logger.info(f"✅ 삭제: {cache_path}")
                deleted_count += 1
            except Exception as e:
                logger.warning(f"⚠️  삭제 실패 (무시 가능): {cache_path} - {e}")
    
    # ✅ 계정별 타임스탬프 파일 생성
    if deleted_count > 0 or True:  # 첫 실행 시에도 생성
        cache_file_path = get_cache_timestamp_file(mobile_num)
        cache_file = Path(cache_file_path)
        
        # 부모 폴더 확인 (이미 존재하지만 안전하게)
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(cache_file, 'w') as f:
            f.write(str(time.time()))
        
        logger.info(f"✅ [{mobile_num}] {deleted_count}개 캐시 삭제 완료")


# ===== 2. User-Agent에서 Chrome 버전 추출 =====

def extract_chrome_version_from_ua(user_agent: str):
    """
    User-Agent에서 Chrome 버전 자동 추출
    
    예시:
        입력: "Mozilla/5.0 ... Chrome/141.0.7390.123 ..."
        출력: 141
    
    Args:
        user_agent (str): config.py의 MOBILE_USER_AGENT_MAPPING 값
    
    Returns:
        int or None: Chrome 메이저 버전
    """
    import re
    
    match = re.search(r'Chrome/(\d+)\.\d+\.\d+\.\d+', user_agent)
    
    if match:
        version = int(match.group(1))
        logger.debug(f"User-Agent 버전 추출: Chrome {version}")
        return version
    
    logger.warning("User-Agent에서 버전 추출 실패")
    return None


# ===== 3. Chrome 프로필 관리 =====
def fix_chrome_profile_preferences(profile_dir):
    """
    프로필 Preferences 수정 (팝업 차단)
    ✅ JSON 에러 처리 강화!
    ✅ 손상된 파일 자동 삭제!
    
    Args:
        profile_dir (str): Chrome 프로필 경로
    """
    pref_file = os.path.join(profile_dir, "Default", "Preferences")
    
    # 파일이 없으면 종료 (Chrome이 자동 생성)
    if not os.path.exists(pref_file):
        logger.debug(f"Preferences 파일 없음 (Chrome이 생성 예정): {pref_file}")
        return
    
    try:
        # ✅ 백업 파일 생성 (안전장치!)
        backup_file = pref_file + ".backup"
        if not os.path.exists(backup_file):
            try:
                shutil.copy2(pref_file, backup_file)
                logger.debug(f"✅ Preferences 백업 생성: {backup_file}")
            except Exception as e:
                logger.warning(f"⚠️  백업 생성 실패 (무시): {e}")
        
        # ✅ JSON 파일 읽기 (에러 처리!)
        try:
            with open(pref_file, 'r', encoding='utf-8') as f:
                prefs = json.load(f)
        
        except json.JSONDecodeError as e:
            logger.error(f"❌ Preferences 파일 손상: {e}")
            
            # ✅ 백업에서 복구 시도
            if os.path.exists(backup_file):
                logger.warning("⚠️  백업 파일에서 복구 시도 중...")
                try:
                    with open(backup_file, 'r', encoding='utf-8') as f:
                        prefs = json.load(f)
                    logger.info("✅ 백업에서 복구 성공!")
                
                except Exception as e2:
                    logger.error(f"❌ 백업 파일도 손상: {e2}")
                    
                    # ✅ 백업도 손상 → 둘 다 삭제!
                    logger.warning("⚠️  손상된 파일 및 백업 삭제 (Chrome이 재생성)")
                    try:
                        os.remove(pref_file)
                        logger.info(f"✅ 손상된 Preferences 삭제: {pref_file}")
                    except Exception as e3:
                        logger.error(f"❌ 파일 삭제 실패: {e3}")
                    
                    try:
                        os.remove(backup_file)
                        logger.info(f"✅ 손상된 백업 삭제: {backup_file}")
                    except Exception as e4:
                        logger.error(f"❌ 백업 삭제 실패: {e4}")
                    
                    # Chrome이 재생성하므로 종료
                    return
            
            else:
                # ✅ 백업 없음 → 손상된 파일 삭제!
                logger.warning("⚠️  백업 없음, 손상된 파일 삭제 (Chrome이 재생성)")
                try:
                    os.remove(pref_file)
                    logger.info(f"✅ 손상된 Preferences 삭제: {pref_file}")
                except Exception as e5:
                    logger.error(f"❌ 파일 삭제 실패: {e5}")
                
                # Chrome이 재생성하므로 종료
                return
        
        # ✅ 설정 수정
        if 'profile' not in prefs:
            prefs['profile'] = {}
        
        prefs['profile']['exit_type'] = 'Normal'
        prefs['profile']['exited_cleanly'] = True
        
        if 'session' not in prefs:
            prefs['session'] = {}
        
        prefs['session']['restore_on_startup'] = 0
        
        # ✅ 파일 저장 (UTF-8, BOM 없이)
        with open(pref_file, 'w', encoding='utf-8') as f:
            json.dump(prefs, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ Preferences 수정 완료: {profile_dir}")
        
    except Exception as e:
        logger.error(f"❌ Preferences 수정 실패: {e}")
        logger.warning("⚠️  이 에러는 무시하고 계속 진행합니다")
        # Chrome이 자동으로 재생성하므로 계속 진행


def close_restore_popup(driver):
    """
    복원 팝업 닫기 (ESC)
    
    Args:
        driver: Selenium WebDriver
    """
    try:
        actions = ActionChains(driver)
        actions.send_keys(Keys.ESCAPE)
        actions.perform()
        logger.debug("✅ 복원 팝업 닫기 완료")
    except Exception as e:
        logger.debug(f"복원 팝업 닫기 실패 (무시): {e}")


# ===== 4. Chrome 드라이버 생성 (핵심) =====

def get_stealth_driver(profile_dir: str, user_agent: str):
    """
    undetected_chromedriver + selenium-stealth 드라이버 생성
    
    Args:
        profile_dir (str): Chrome 프로필 경로
        user_agent (str): User-Agent 문자열
    
    Returns:
        WebDriver: Chrome 드라이버 인스턴스
    """
    try:
        # Chrome 버전 추출
        chrome_version = extract_chrome_version_from_ua(user_agent)
        
        # ChromeOptions 설정
        options = uc.ChromeOptions()
        options.add_argument(f'--user-agent={user_agent}')
        options.add_argument('--log-level=3')
        options.add_argument('--disable-gpu')
        
        # config.py의 옵션 추가
        for opt in DEFAULT_CHROME_OPTIONS:
            options.add_argument(opt)
        
        # Preferences 설정
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
        options.add_experimental_option("prefs", prefs)
        
        # 드라이버 생성
        logger.info(f"🚀 드라이버 생성 중... (Chrome {chrome_version})")
        
        driver = uc.Chrome(
            options=options,
            user_data_dir=profile_dir,
            use_subprocess=True,
            version_main=chrome_version
        )
        
        # CDP로 User-Agent 강제 적용
        try:
            driver.execute_cdp_cmd('Network.setUserAgentOverride', {
                "userAgent": user_agent
            })
            logger.info("✅ User-Agent 강제 적용 완료 (CDP)")
        except Exception as e:
            logger.warning(f"⚠️  CDP User-Agent 적용 실패: {e}")
        
        # selenium-stealth 적용
        stealth(driver,
                languages=["ko-KR", "ko"],
                vendor="Google Inc.",
                platform="Win32",
                webgl_vendor="Intel Inc.",
                renderer="Intel Iris OpenGL Engine",
                fix_hairline=True)
        
        logger.info("✅ selenium-stealth 적용 완료")
        
        # 창 설정
        driver.set_window_position(0, 0)
        driver.maximize_window()
        
        logger.info("✅ 드라이버 생성 완료")
        return driver
        
    except Exception as e:
        logger.error(f"❌ 드라이버 생성 실패: {e}")
        raise

# ===== 5. 메인 진입점 =====

def select_mobile_and_get_driver():
    """
    전화번호 선택 및 Chrome 드라이버 생성
    ✅ config.py만 수정하면 모든 게 자동으로 작동
    
    Returns:
        tuple: (mobile_num, driver)
    """
    # 1. 전화번호 선택
    ids = list(id_dict.keys())
    mobile_num = pyautogui.confirm('전화번호를 선택하시오', buttons=ids)
    logger.info(f'📱 선택한 전화번호: {mobile_num}')
    
    # 2. User-Agent 가져오기
    user_agent = MOBILE_USER_AGENT_MAPPING.get(mobile_num, USER_AGENT)
    chrome_version = extract_chrome_version_from_ua(user_agent)
    
    if chrome_version:
        logger.info(f"✅ 사용할 User-Agent: Chrome {chrome_version}")
    else:
        logger.warning("⚠️  User-Agent 버전 감지 실패, 기본값 사용")
    
    # 3. 계정별 캐시 체크 (7일마다)
    if should_clear_cache(mobile_num, days=7):
        clear_chromedriver_cache(mobile_num, chrome_version)
    
    # 4. 프로필 경로
    profile_dir = get_profile_path(mobile_num)
    fix_chrome_profile_preferences(profile_dir)
    
    # 5. 드라이버 생성
    driver = get_stealth_driver(profile_dir, user_agent)
    
    # 6. 네이버밴드 열기
    move_mouse_naturally()
    driver.get(NAVERBAND_URL)
    time.sleep(2)
    
    # 7. 드라이버 속성 설정
    driver.selected_mobile = mobile_num
    close_restore_popup(driver)
    
    logger.info(f"✅ [{mobile_num}] 드라이버 준비 완료")
    
    return mobile_num, driver

# ===== 6. 테스트 코드 =====

if __name__ == "__main__":
    mobile, driver = select_mobile_and_get_driver()
    logger.info(f"{mobile} 브라우저 실행 완료")
    input("아무 키나 누르면 종료...")
    driver.quit()
