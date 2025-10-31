#resources/xpath_dict.py
xpath_dict = {

    #변수정의
    'log_in': '//*[@id="input_local_phone_number"]',
    'password': '//*[@id="pw"]',
    '인증번호': '//*[@id="code"]',
    '인증번호확인': '//*[@id="code"]',
    '문자메시지받기': '//*[@id="content"]/div/div[1]/a[2]',
    '글쓰기_1': '//*[@id="content"]/section/div[2]/div/button',
    '글쓰기_2': '//*[@id="wrap"]/div[3]/div/div/section/div/div/div/div[2]/div',
    '이미지첨부': '//*[@id="wrap"]/div[3]/div[2]/section/div/footer/button[2]',
    '이미지게시': '//*[@id="wrap"]/div[3]/div/div/section/div/div/div/div[3]/div/div[2]/button',
    '홈': '//*[@id="header"]/div/div[1]/h1/a',
    '쿠키': '/html/body/div[4]/div/div[2]/button[1]',
    'let_me': '//*[@id="header"]/div/div[2]/ul/li[5]/button',
    'log_out': '//*[@id="gnbProfileMenuPopup"]/ul[3]/li/a',
    'log_out_but': '//*[@id="wrap"]/div[3]/div/div/section/div/footer/button[2]',
    #2차인증요구
    'sms_but':'//*[@id="content"]/div/div[1]/a',
    'sms_input_space':'//*[@id="code"]',
    'sms_input_submit':'//*[@id="inputForm"]/button[1]',
    '다시묻지않기':'//*[@id="trust"]',
    
}

id_dict= {
    #id:pw
    '01075381965': 'nam4732@',
    '01020664732': 'nam4732@',
    '01027851965': 'nam4732@',
}