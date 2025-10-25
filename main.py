# main.py

import pyautogui    # prompt 입력에 필요
import time         # sleep, 시간 계산 등에 필요
import random       # rand_sleep, 셔플 등에 필요
from selenium import webdriver   # driver 사용에 필요
from selenium.webdriver.common.alert import Alert   # Alert 처리 필요
from selenium.webdriver.common.keys import Keys     # 키입력(ESC, ENTER)에 필요

from src.chrome_manager import select_mobile_and_get_driver
from src.account_manager import login, save_cookies
from src.utils import x_path_click, move_mouse_naturally, logger
from resources.xpath_dict import xpath_dict, id_dict
from src.naverband_automation import roof_bands, perform_logout
from config import *

def main():
    mobile, driver = select_mobile_and_get_driver()
    logger.info(f"{mobile} 계정으로 브라우저가 실행되었습니다.")
    login(driver)

    # 밴드회전
    p_time = pyautogui.prompt(title="실행시간", default='예) 1 : 1시간, 0.5 = 30분', text = "시간")
    e_time = time.time() + 60*60*float(p_time)

    start_time = time.strftime('%p %I시%M분%S초', time.localtime())
    end_time = time.strftime('%p %I시%M분%S초', time.localtime(e_time))
    logger.info(f'{mobile}는 {start_time}에 시작하여, {end_time}에 종료예정입니다.')

    t = 1 #회전수 확인
    # while t < 1 :
    while time.time() < e_time:
        roof_bands(
        driver, 
        xpath_dict, 
        BAND_LIST, 
        TXT_DIR, 
        IMAGE_DIR, 
        MAX_ERROR_CNT=3
    )
        rand_sleep = random.randrange(10,20)
        move_mouse_naturally()
        rel_time = time.strftime('%p %I시%M분', time.localtime(time.time()+rand_sleep))
        logger.info('-'*20)
        logger.info('{}회전, {}초간 휴식/ {}에 다시 시작합니다'.format(t, rand_sleep, rel_time))
        logger.info('-'*20) 
        time.sleep(rand_sleep)
        t += 1
    time.sleep(1)
    
    perform_logout(driver)

    close_time = time.strftime('%p %I시%M분%S초', time.localtime())
    logger.info('이 project는 {}에 완료하여 logout하였습니다'.format(close_time))
    save_cookies(driver)
    
    driver.quit()


if __name__ == "__main__":
    main()