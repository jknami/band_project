# check_ua.py
from src.chrome_manager import select_mobile_and_get_driver

mobile, driver = select_mobile_and_get_driver()

# ✅ 이 사이트 열기
driver.get("https://www.whatismybrowser.com/detect/what-is-my-user-agent")

print("\n✅ 자동화 브라우저에서 User-Agent를 확인하세요!")
print("   → Chrome 141로 표시되어야 합니다\n")

input("확인 후 엔터...")
driver.quit()
