from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.chrome.service import Service
import time
import re
import pytz
from datetime import datetime, timedelta
import getpass
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import subprocess
import os

# 基础配置
USER_EMAIL = "Xserver账号"
USER_PASSWORD = "Xserver密码"
CHROMEDRIVER_PATH = "/root/.cache/selenium/chromedriver/linux64/144.0.7559.133/chromedriver"

# 周期控制
TRIGGER_HOUR = 23
ADD_DELAY_HOUR = 2
RETRY_INTERVAL_HOUR = 2
DEFAULT_CRON = "0 9 * * *"
SCRIPT_PATH = "/root/xs/1145.py"
TASK_CMD = f"cd /root/xs && /usr/bin/python3 {SCRIPT_PATH} >> /root/xs/run_log.log 2>&1"

# 时区配置
JST = pytz.timezone('Asia/Tokyo')
LOCAL_TZ = pytz.timezone('Asia/Shanghai')

# 时间提取正则
TIME_EXTRACT_PATTERN = re.compile(r'更新をご希望の場合は、(\d{4}-\d{2}-\d{2} \d{2}:\d{2})以降にお試しください')

# 邮件配置
SMTP_SERVER = "smtp.qq.com"
SMTP_PORT = 587
SENDER_EMAIL = "你的QQ邮箱"
SENDER_PASSWORD = "aveurtavngvmdgig"
RECEIVER_EMAIL = "你的QQ邮箱"

# 元素定位
SUBMIT_BTN_XPATH = "//input[@value='ログイン']"
NEW_ENV_VERIFY_FLAG = "//h1[contains(text(), '新しい環境からのログイン')]"
NEW_ENV_CODE_INPUT = "//input[@id='auth_code' and @name='auth_code']"
LOGIN_BTN_XPATH = "//form//input[@type='submit' and @value='ログインする']"
EMAIL_INPUT_XPATH = "//form//input[@name='memberid' or @id='memberid']"
PWD_INPUT_XPATH = "//form//input[@name='user_password' or @id='user_password']"
SEND_VERIFY_XPATHS = ["//input[@type='submit' and @value='認証コードを送信']"]
VERIFY_INPUT_XPATH = "//input[@name='auth_code' and @id='auth_code']"
SERVICE_MANAGEMENT_TOGGLE = "//span[contains(@class, 'serviceNav__toggle') and contains(text(), 'サービス管理')]"
GAME_SERVER_LINK = "//a[@id='ga-xsa-serviceNav-xmgame' and @href='/xapanel/xmgame/index']"
GAME_MANAGE_BLUE_BTN_XPATH = "//a[contains(text(), 'ゲーム管理') and contains(@class, 'btn--primary') and contains(@href, 'jumpvps')]"
SERVER_HOME_PAGE_FLAG = "//*[contains(text(), 'サーバー管理') or contains(@href, 'server_management')]"
EXTEND_BUTTON_XPATH = "//a[contains(text(), 'アップグレード・期限延長') or (contains(@href, 'extend') and contains(text(), '延長'))]"
STEP1_RENEW_BTN = "//button[contains(text(), '期限を延長する')]"
STEP2_CONFIRM_BTN = "//button[contains(text(), '確認画面に進む')]"
STEP3_FINAL_BTN = "//button[contains(text(), '期限を延長する')]"
FAILED_CHECK_BTN = "//button[contains(text(), '期限を延長する')]"
LOGIN_SUCCESS_FLAGS = ["//p[contains(text(), 'aaaunlockwang@gmail.com')]", "//*[contains(text(), 'エックスサーバー契約管理ページ')]"]
LOGIN_URL = "https://secure.xserver.ne.jp/xapanel/login/xserver/"
TIMEOUT = 80
WAIT_AFTER_SUBMIT = 25
NOW_TIME = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def execute_crontab(cmd):
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        log(f"❌ crontab命令失败：{cmd} | 错误：{e.stderr.strip()}")
        return None

def delete_default_crontab():
    current_tasks = execute_crontab("crontab -l 2>/dev/null").splitlines() if execute_crontab("crontab -l 2>/dev/null") else []
    new_tasks = [task for task in current_tasks if DEFAULT_CRON not in task]
    if len(new_tasks) != len(current_tasks):
        tasks_str = "\n".join(new_tasks) + "\n" if new_tasks else ""
        execute_crontab(f"echo '{tasks_str}' | crontab -")
        log(f"✅ 已删除默认任务：{DEFAULT_CRON} {TASK_CMD}")
        return True
    log("✅ 无默认「每天9点」任务可删除")
    return False

def delete_all_script_crontab():
    current_tasks = execute_crontab("crontab -l 2>/dev/null").splitlines() if execute_crontab("crontab -l 2>/dev/null") else []
    new_tasks = [task for task in current_tasks if SCRIPT_PATH not in task]
    if len(new_tasks) != len(current_tasks):
        tasks_str = "\n".join(new_tasks) + "\n" if new_tasks else ""
        execute_crontab(f"echo '{tasks_str}' | crontab -")
        log(f"✅ 已删除所有本脚本相关的旧任务")
    return new_tasks

def add_once_crontab(delay_hours):
    future_time = datetime.now() + timedelta(hours=delay_hours)
    cron_expr = f"{future_time.minute} {future_time.hour} {future_time.day} {future_time.month} *"
    delete_all_script_crontab()
    current_tasks = execute_crontab("crontab -l 2>/dev/null").splitlines() if execute_crontab("crontab -l 2>/dev/null") else []
    current_tasks.append(f"{cron_expr} {TASK_CMD}")
    tasks_str = "\n".join(current_tasks) + "\n"
    execute_crontab(f"echo '{tasks_str}' | crontab -")
    next_run_local = future_time.strftime(LOG_TIME_FORMAT)
    log(f"✅ 已添加一次性任务：{cron_expr} {TASK_CMD}（下次执行时间：{next_run_local} 本地时区）")
    return next_run_local

def ensure_default_crontab():
    current_tasks = execute_crontab("crontab -l 2>/dev/null").splitlines() if execute_crontab("crontab -l 2>/dev/null") else []
    default_task_exists = any(DEFAULT_CRON in task and SCRIPT_PATH in task for task in current_tasks)
    if not default_task_exists:
        delete_all_script_crontab()
        current_tasks.append(f"{DEFAULT_CRON} {TASK_CMD}")
        tasks_str = "\n".join(current_tasks) + "\n"
        execute_crontab(f"echo '{tasks_str}' | crontab -")
        log(f"✅ 已确保默认任务存在：{DEFAULT_CRON} {TASK_CMD}（每天9点执行）")
    else:
        log(f"✅ 默认任务已存在：{DEFAULT_CRON} {TASK_CMD}，无需调整")
    return True

def log(message):
    timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
    print(f"[{timestamp}] {message}")

def send_email(status, subject, content, screenshot_path=None):
    try:
        if not isinstance(content, str):
            content = str(content)
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, 'rb') as f:
                img = MIMEImage(f.read(), _subtype='png')
                img.add_header('Content-Disposition', 'attachment', filename=os.path.basename(screenshot_path))
                msg.attach(img)
            log(f"✅ 已添加截图附件：{os.path.basename(screenshot_path)}")
        elif screenshot_path:
            log(f"⚠️  截图文件不存在：{screenshot_path}，跳过附件")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        log(f"✅ 【邮件通知】{status}状态邮件已发送至 {RECEIVER_EMAIL}（QQ邮箱）")
        if screenshot_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            log(f"✅ 已删除截图文件：{screenshot_path}")
    except Exception as e:
        log(f"❌ 【邮件通知】发送失败：{type(e).__name__} - {str(e)}")
        if screenshot_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)
            log(f"✅ 已删除截图文件：{screenshot_path}")

def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    options.page_load_strategy = 'eager'
    service = Service(executable_path=CHROMEDRIVER_PATH)
    return webdriver.Chrome(service=service, options=options)

def save_page_source(driver, file_name):
    try:
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(driver.page_source)
        log(f"✅ 页面源码已保存为：{file_name}")
    except Exception as e:
        log(f"❌ 保存源码失败：{str(e)}")

def wait_for_element(driver, xpath, element_name):
    try:
        element = WebDriverWait(driver, TIMEOUT).until(EC.element_to_be_clickable((By.XPATH, xpath)))
        log(f"✅ 找到「{element_name}」（XPath：{xpath}）")
        return element
    except TimeoutException:
        raise Exception(f"❌ 未找到「{element_name}」（XPath：{xpath}）")

def is_element_exist(driver, xpath):
    try:
        driver.find_element(By.XPATH, xpath)
        return True
    except NoSuchElementException:
        return False

def handle_verify_code(driver):
    if is_element_exist(driver, SEND_VERIFY_XPATHS[0]):
        log("⚠️  检测到登录验证码，执行流程...")
        send_btn = wait_for_element(driver, SEND_VERIFY_XPATHS[0], "验证码发送按钮")
        send_btn.click()
        time.sleep(12)
        log("✅ 已发送登录验证码，查收邮箱")
        driver.save_screenshot(f"login_verify_sent_{NOW_TIME}.png")
        verify_input = wait_for_element(driver, VERIFY_INPUT_XPATH, "登录验证码输入框")
        verify_code = getpass.getpass(prompt="\n📧 输入登录验证码（4-6位数字）：")
        while not verify_code.isdigit() or len(verify_code) not in (4,5,6):
            verify_code = getpass.getpass(prompt="❌ 格式错误！重新输入：")
        verify_input.clear()
        verify_input.send_keys(verify_code)
        time.sleep(5)
        driver.save_screenshot(f"login_verify_input_{NOW_TIME}.png")
        submit_btn = wait_for_element(driver, SUBMIT_BTN_XPATH, "登录验证码提交按钮")
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(WAIT_AFTER_SUBMIT)
        log(f"✅ 已点击提交按钮（XPath：{SUBMIT_BTN_XPATH}）")
        driver.save_screenshot(f"login_verify_submitted_{NOW_TIME}.png")
        if is_element_exist(driver, VERIFY_INPUT_XPATH):
            raise Exception("❌ 登录验证码提交失败！页面未跳转")
    else:
        log("✅ 未检测到登录验证码，直接继续")

def handle_new_env_verify(driver):
    if is_element_exist(driver, NEW_ENV_VERIFY_FLAG):
        log("⚠️  检测到新环境二次验证，执行流程...")
        save_page_source(driver, f"new_env_verify_page_{NOW_TIME}.html")
        code_input = wait_for_element(driver, NEW_ENV_CODE_INPUT, "二次验证码输入框")
        verify_code = getpass.getpass(prompt="\n📧 输入新环境二次验证码（4-6位数字）：")
        while not verify_code.isdigit() or len(verify_code) not in (4,5,6):
            verify_code = getpass.getpass(prompt="❌ 格式错误！重新输入：")
        code_input.clear()
        code_input.send_keys(verify_code)
        time.sleep(5)
        driver.save_screenshot(f"new_env_verify_input_{NOW_TIME}.png")
        submit_btn = wait_for_element(driver, SUBMIT_BTN_XPATH, "二次验证提交按钮")
        driver.execute_script("arguments[0].click();", submit_btn)
        time.sleep(WAIT_AFTER_SUBMIT)
        log(f"✅ 已点击提交按钮（XPath：{SUBMIT_BTN_XPATH}）")
        driver.save_screenshot(f"new_env_verify_submitted_{NOW_TIME}.png")
        if not any(is_element_exist(driver, flag) for flag in LOGIN_SUCCESS_FLAGS):
            raise Exception("❌ 二次验证码提交失败！未进入主界面")
        log("✅ 新环境二次验证提交成功！")
    else:
        log("✅ 未检测到新环境二次验证，直接进入主界面")

def safe_click(driver, xpath, element_name, post_wait=15):
    log(f"🔍 定位「{element_name}」按钮...")
    element = wait_for_element(driver, xpath, element_name)
    driver.execute_script("arguments[0].click();", element)
    time.sleep(post_wait)
    driver.save_screenshot(f"click_{element_name}_{NOW_TIME}.png")
    log(f"✅ 成功点击「{element_name}」按钮")
    return True

def open_service_menu(driver):
    log("🔍 定位并展开「サービス管理」下拉菜单...")
    toggle_btn = wait_for_element(driver, SERVICE_MANAGEMENT_TOGGLE, "サービス管理下拉触发按钮")
    driver.execute_script("arguments[0].click();", toggle_btn)
    time.sleep(8)
    driver.save_screenshot(f"service_menu_opened_{NOW_TIME}.png")
    if not is_element_exist(driver, GAME_SERVER_LINK):
        raise Exception("❌ 「サービス管理」菜单展开失败")
    log("✅ 「サービス管理」菜单展开成功")
    return True

def verify_page_jump(driver, flag_xpath, page_name):
    log(f"🔍 验证是否进入{page_name}...")
    try:
        WebDriverWait(driver, TIMEOUT).until(EC.presence_of_element_located((By.XPATH, flag_xpath)))
        log(f"✅ 成功进入{page_name}")
        save_page_source(driver, f"{page_name.replace(' ', '_')}_{NOW_TIME}.html")
        return True
    except TimeoutException:
        raise Exception(f"❌ 未成功进入{page_name}")

def extract_renew_time(driver):
    log("🔍 开始从续期页面提取可续期时间...")
    page_html = driver.page_source
    match_result = TIME_EXTRACT_PATTERN.search(page_html)
    if not match_result:
        raise Exception("❌ 未从续期页面提取到可续期时间，页面内容可能更新")
    renew_start_str = match_result.group(1)
    renew_start_time = datetime.strptime(renew_start_str, "%Y-%m-%d %H:%M")
    renew_start_jst = JST.localize(renew_start_time)
    expire_time_jst = renew_start_jst + timedelta(hours=24)
    log(f"✅ 提取到可续期时间：{renew_start_jst.strftime('%Y-%m-%d %H:%M:%S')}（JST）")
    log(f"✅ 推导服务器到期时间：{expire_time_jst.strftime('%Y-%m-%d %H:%M:%S')}（JST）")
    return expire_time_jst

def calculate_remaining_hour(expire_time_jst):
    now_jst = datetime.now(JST)
    remaining_seconds = (expire_time_jst - now_jst).total_seconds()
    remaining_hour = round(remaining_seconds / 3600, 2) if remaining_seconds > 0 else 0.0
    log(f"✅ 计算剩余到期时间：{remaining_hour}小时（JST，当前JST时间：{now_jst.strftime(LOG_TIME_FORMAT)}）")
    return remaining_hour, now_jst

def calculate_next_run_time(now_jst, remaining_hour):
    if not isinstance(remaining_hour, float):
        next_run_jst = now_jst + timedelta(hours=RETRY_INTERVAL_HOUR)
        run_type = f"【{RETRY_INTERVAL_HOUR}小时重试】"
        desc = "任意步骤执行失败，触发重试机制"
    elif remaining_hour >= TRIGGER_HOUR:
        to_23hour = round(remaining_hour - TRIGGER_HOUR, 2)
        next_run_delay = round(to_23hour + ADD_DELAY_HOUR, 2)
        next_run_jst = now_jst + timedelta(hours=next_run_delay)
        run_type = f"【延迟检测-{next_run_delay}小时】"
        desc = f"距离剩余{TRIGGER_HOUR}小时还有{to_23hour}h + 追加{ADD_DELAY_HOUR}h"
    else:
        next_run_jst = now_jst + timedelta(hours=48)
        run_type = f"【默认周期-48小时】"
        desc = "签到+续期全部成功，恢复两天默认周期"
    next_run_local = next_run_jst.astimezone(LOCAL_TZ)
    return {
        "next_jst": next_run_jst,
        "next_local": next_run_local,
        "run_type": run_type,
        "desc": desc,
        "next_delay_hour": round((next_run_jst - now_jst).total_seconds() / 3600, 2)
    }

def renew_task():
    driver = None
    expire_time_jst = None
    remaining_hour = None
    task_status = "fail"
    email_subject = ""
    email_content = ""
    task_adjust_detail = ""
    screenshot_path = None
    try:
        driver = init_driver()
        driver.get(LOGIN_URL)
        time.sleep(10)
        driver.save_screenshot(f"step1_visit_login_{NOW_TIME}.png")
        
        if is_element_exist(driver, LOGIN_BTN_XPATH):
            log("⚠️  检测到登录按钮，执行登录流程")
            email_input = wait_for_element(driver, EMAIL_INPUT_XPATH, "账号输入框")
            email_input.clear()
            email_input.send_keys(USER_EMAIL)
            time.sleep(3)
            pwd_input = wait_for_element(driver, PWD_INPUT_XPATH, "密码输入框")
            pwd_input.clear()
            pwd_input.send_keys(USER_PASSWORD)
            time.sleep(3)
            driver.save_screenshot(f"step2_input_account_{NOW_TIME}.png")
            login_btn = wait_for_element(driver, LOGIN_BTN_XPATH, "登录按钮")
            driver.execute_script("arguments[0].click();", login_btn)
            time.sleep(15)
            driver.save_screenshot(f"step3_after_login_click_{NOW_TIME}.png")
            handle_verify_code(driver)
            handle_new_env_verify(driver)
            log("🔍 验证主界面状态...")
            for flag in LOGIN_SUCCESS_FLAGS:
                if is_element_exist(driver, flag):
                    log(f"✅ 已进入契約管理主界面（检测到标识：{flag}）")
                    break
            save_page_source(driver, f"main_ui_{NOW_TIME}.html")
        else:
            log("✅ 已处于登录状态")
            save_page_source(driver, f"already_logged_in_{NOW_TIME}.html")
        
        open_service_menu(driver)
        safe_click(driver, GAME_SERVER_LINK, "ゲーム用マルチサーバー", post_wait=20)
        verify_page_jump(driver, "//*[contains(text(), 'XServer GAMEs')]", "XServer GAMEs页面")
        safe_click(driver, GAME_MANAGE_BLUE_BTN_XPATH, "蓝色ゲーム管理按钮", post_wait=20)
        verify_page_jump(driver, SERVER_HOME_PAGE_FLAG, "服务器主页")
        safe_click(driver, EXTEND_BUTTON_XPATH, "アップグレード・期限延長", post_wait=15)
        save_page_source(driver, f"final_renew_page_{NOW_TIME}.html")
        log("✅ 成功进入续期页面，开始时间判断...")
        
        expire_time_jst = extract_renew_time(driver)
        remaining_hour, now_jst = calculate_remaining_hour(expire_time_jst)
        next_run_info = calculate_next_run_time(now_jst, remaining_hour)
        
        if remaining_hour >= TRIGGER_HOUR:
            screenshot_path = f"no_renew_{NOW_TIME}.png"
            driver.save_screenshot(screenshot_path)
            log(f"✅ 已生成未续期截图：{screenshot_path}")
            to_23hour = round(remaining_hour - TRIGGER_HOUR, 2)
            delay_hours = to_23hour + ADD_DELAY_HOUR
            delete_default_crontab()
            next_run_local = add_once_crontab(delay_hours)
            task_adjust_detail = f"""🔧 任务调整详情（未续期，按原逻辑计算延迟）：
- 原任务：{DEFAULT_CRON}（每天9点执行）→ 已删除
- 新任务：{delay_hours}小时后执行一次（下次执行时间：{next_run_local} 本地时区）
- 计算逻辑：延迟时间 =（剩余时间{remaining_hour}h - 触发阈值{TRIGGER_HOUR}h）+ 追加延迟{ADD_DELAY_HOUR}h = {to_23hour}h + {ADD_DELAY_HOUR}h
- 调整原因：剩余时间≥{TRIGGER_HOUR}小时，按原规则设置延迟检测"""
            log(f"✅ 任务调整完成：{delay_hours}小时后执行一次（计算逻辑：{remaining_hour}h-23h+2h）")
            task_status = "no_renew"
            email_subject = "[XServer续期通知] 暂无需续期（带截图）"
            email_content = f"""XServer服务器续期检测完成！

📊 核心信息：
- 执行时间：{datetime.now().strftime(LOG_TIME_FORMAT)}（本地时区）
- 服务器到期时间：{expire_time_jst.strftime(LOG_TIME_FORMAT)}（JST）
- 剩余到期时间：{remaining_hour}小时
- 续期状态：无需续期（剩余时间≥{TRIGGER_HOUR}小时触发阈值）

{task_adjust_detail}

📝 后续逻辑：
下次任务执行时，重新计算剩余时间
→若仍≥{TRIGGER_HOUR}小时：继续按「（剩余时间-23h）+2h」调整
→若<{TRIGGER_HOUR}小时：自动执行续期，成功后保持每天9点执行

📸 附件说明：
已附带当前续期页面截图，邮件发送后将自动删除截图文件，不占用内存。"""
        else:
            log(f"⚠️  剩余{remaining_hour}小时<{TRIGGER_HOUR}小时，执行续期操作！")
            safe_click(driver, STEP1_RENEW_BTN, "图一红圈-期限を延長する", post_wait=10)
            safe_click(driver, STEP2_CONFIRM_BTN, "图二红圈-確認画面に進む", post_wait=10)
            safe_click(driver, STEP3_FINAL_BTN, "图三红圈-期限を延長する", post_wait=15)
            
            if is_element_exist(driver, FAILED_CHECK_BTN):
                screenshot_path = f"renew_failed_{NOW_TIME}.png"
                driver.save_screenshot(screenshot_path)
                log(f"✅ 已生成续期失败截图：{screenshot_path}")
                delete_default_crontab()
                next_run_local = add_once_crontab(RETRY_INTERVAL_HOUR)
                task_adjust_detail = f"""🔧 任务调整详情（续期失败，添加重试）：
- 原任务：{DEFAULT_CRON}（每天9点执行）→ 已删除
- 新任务：{RETRY_INTERVAL_HOUR}小时后重试一次（下次执行时间：{next_run_local} 本地时区）
- 调整原因：续期操作失败，触发重试机制"""
                log("❌ 续期失败，添加重试任务")
                task_status = "fail"
                email_subject = "[XServer续期通知] 续期失败（带截图）"
                email_content = f"""XServer服务器续期操作失败！

📊 核心信息：
- 执行时间：{datetime.now().strftime(LOG_TIME_FORMAT)}（本地时区）
- 服务器到期时间：{expire_time_jst.strftime(LOG_TIME_FORMAT)}（JST）
- 剩余到期时间：{remaining_hour}小时
- 失败原因：续期后仍显示续期按钮，推测未生效

{task_adjust_detail}

📝 注意：若多次重试失败，请登录XServer官网手动续期！

📸 附件说明：
已附带失败页面截图，邮件发送后将自动删除截图文件，不占用内存。"""
                raise Exception("续期失败：图三按钮未消失")
            else:
                screenshot_path = f"renew_success_{NOW_TIME}.png"
                driver.save_screenshot(screenshot_path)
                log(f"✅ 已生成续期成功截图：{screenshot_path}")
                ensure_default_crontab()
                task_adjust_detail = f"""🔧 任务调整详情（续期成功，保持默认）：
- 当前任务：{DEFAULT_CRON}（每天9点执行）→ 保持不变
- 调整原因：续期成功，无需改变默认检测周期"""
                log("✅ 续期成功，保持每天9点执行任务")
                task_status = "success"
                email_subject = "[XServer续期通知] 续期成功（带截图）"
                email_content = f"""XServer服务器续期操作成功！

📊 核心信息：
- 执行时间：{datetime.now().strftime(LOG_TIME_FORMAT)}（本地时区）
- 服务器原到期时间：{expire_time_jst.strftime(LOG_TIME_FORMAT)}（JST）
- 续期触发条件：剩余到期时间{remaining_hour}小时<{TRIGGER_HOUR}小时
- 续期状态：已成功延长服务器有效期

{task_adjust_detail}

📝 后续逻辑：
之后每天9点自动执行检测，未续期时按「（剩余时间-23h）+2h」调整任务

📸 附件说明：
已附带成功页面截图，邮件发送后将自动删除截图文件，不占用内存。"""
        
        return True, remaining_hour, now_jst
    
    except Exception as e:
        error_msg = str(e)
        log(f"❌ 任务执行失败：{error_msg}")
        if driver:
            screenshot_path = f"task_error_{NOW_TIME}.png"
            driver.save_screenshot(screenshot_path)
            log(f"✅ 已生成异常截图：{screenshot_path}")
            save_page_source(driver, f"task_error_page_{NOW_TIME}.html")
        
        delete_default_crontab()
        next_run_local = add_once_crontab(RETRY_INTERVAL_HOUR)
        task_adjust_detail = f"""🔧 任务调整详情（执行异常，添加重试）：
- 原任务：{DEFAULT_CRON}（每天9点执行）→ 已删除
- 新任务：{RETRY_INTERVAL_HOUR}小时后重试一次（下次执行时间：{next_run_local} 本地时区）
- 调整原因：任务执行异常，触发重试机制"""
        
        task_status = "fail"
        email_subject = "[XServer续期通知] 任务执行失败（带截图）"
        email_content = f"""XServer服务器续期任务执行失败！

📊 核心信息：
- 执行时间：{datetime.now().strftime(LOG_TIME_FORMAT)}（本地时区）
- 失败原因：{error_msg}
- 错误页面源码：task_error_page_{NOW_TIME}.html

{task_adjust_detail}

📝 注意：
请查看日志和截图排查问题（日志路径：/root/xst/run_log.log）

📸 附件说明：
已附带异常页面截图，邮件发送后将自动删除截图文件，不占用内存。"""
        
        return False, remaining_hour, datetime.now(JST)
    
    finally:
        if driver:
            driver.quit()
            log(f"✅ 浏览器已关闭")
        send_email(task_status, email_subject, email_content, screenshot_path)


if __name__ == "__main__":
    log("==================================== 脚本启动 ====================================")
    log(f"📌 核心规则：续期成功保持每天9点，未续期时延迟=（剩余时间-23h）+2h")
    log(f"📌 触发阈值：剩余<{TRIGGER_HOUR}小时自动续期")
    log(f"📌 邮件通知：{RECEIVER_EMAIL}（QQ邮箱，带截图附件+自动删除）")
    log("==================================== 开始执行 ====================================")
    
    task_success, remaining_hour, now_jst = renew_task()
    next_run_info = calculate_next_run_time(now_jst, remaining_hour)
    
    log("==================================== 执行结果 ====================================")
    if task_success:
        log(f"✅ 整体任务执行成功 | {next_run_info['run_type']} | {next_run_info['desc']}")
    else:
        log(f"❌ 整体任务执行失败 | {next_run_info['run_type']} | {next_run_info['desc']}")
    log(f"📅 下次执行时间-JST：{next_run_info['next_jst'].strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📅 下次执行时间-本地：{next_run_info['next_local'].strftime('%Y-%m-%d %H:%M:%S')}")
    log("==================================== 脚本结束 ====================================")
