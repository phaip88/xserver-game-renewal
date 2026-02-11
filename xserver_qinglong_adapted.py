#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XServer 自动续期脚本 - 青龙面板适配版
适配说明：
1. 移除了 crontab 操作（由青龙面板管理）
2. 移除了交互式验证码输入（需要提前配置或使用 API）
3. 简化了依赖，使用环境变量配置
4. 添加了青龙面板通知支持
"""

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
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import os
import sys

# ========== 青龙面板环境变量配置 ==========
USER_EMAIL = os.getenv("XSERVER_EMAIL", "your_email@example.com")
USER_PASSWORD = os.getenv("XSERVER_PASSWORD", "your_password")
CHROMEDRIVER_PATH = os.getenv("CHROMEDRIVER_PATH", "/usr/bin/chromedriver")

# 邮件配置（使用环境变量）
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.qq.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL", "")

# 续期触发阈值（小时）
TRIGGER_HOUR = int(os.getenv("TRIGGER_HOUR", "23"))

# 时区配置
JST = pytz.timezone('Asia/Tokyo')
LOCAL_TZ = pytz.timezone('Asia/Shanghai')

# 时间提取正则
TIME_EXTRACT_PATTERN = re.compile(r'更新をご希望の場合は、(\d{4}-\d{2}-\d{2} \d{2}:\d{2})以降にお試しください')

# 元素定位
LOGIN_URL = "https://secure.xserver.ne.jp/xapanel/login/xserver/"
EMAIL_INPUT_XPATH = "//form//input[@name='memberid' or @id='memberid']"
PWD_INPUT_XPATH = "//form//input[@name='user_password' or @id='user_password']"
LOGIN_BTN_XPATH = "//form//input[@type='submit' and @value='ログインする']"
SERVICE_MANAGEMENT_TOGGLE = "//span[contains(@class, 'serviceNav__toggle') and contains(text(), 'サービス管理')]"
GAME_SERVER_LINK = "//a[@id='ga-xsa-serviceNav-xmgame' and @href='/xapanel/xmgame/index']"
GAME_MANAGE_BLUE_BTN_XPATH = "//a[contains(text(), 'ゲーム管理') and contains(@class, 'btn--primary')]"
SERVER_HOME_PAGE_FLAG = "//*[contains(text(), 'サーバー管理')]"
EXTEND_BUTTON_XPATH = "//a[contains(text(), 'アップグレード・期限延長')]"
STEP1_RENEW_BTN = "//button[contains(text(), '期限を延長する')]"
STEP2_CONFIRM_BTN = "//button[contains(text(), '確認画面に進む')]"
STEP3_FINAL_BTN = "//button[contains(text(), '期限を延長する')]"
FAILED_CHECK_BTN = "//button[contains(text(), '期限を延長する')]"
LOGIN_SUCCESS_FLAGS = ["//*[contains(text(), 'エックスサーバー契約管理ページ')]"]

TIMEOUT = 60
NOW_TIME = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_TIME_FORMAT = "%Y-%m-%d %H:%M:%S"

def log(message):
    """日志输出"""
    timestamp = datetime.now().strftime(LOG_TIME_FORMAT)
    print(f"[{timestamp}] {message}")

def send_notification(title, content):
    """青龙面板通知（兼容多种通知方式）"""
    try:
        # 方式1：青龙面板内置通知
        if os.path.exists("/ql/scripts/notify.py"):
            sys.path.append("/ql/scripts")
            import notify
            notify.send(title, content)
            log("✅ 已通过青龙面板通知发送")
            return
    except Exception as e:
        log(f"⚠️  青龙通知失败：{e}")
    
    # 方式2：邮件通知（备用）
    if SENDER_EMAIL and SENDER_PASSWORD:
        send_email(title, content)

def send_email(subject, content, screenshot_path=None):
    """邮件通知"""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = RECEIVER_EMAIL
        msg['Subject'] = subject
        msg.attach(MIMEText(content, 'plain', 'utf-8'))
        
        if screenshot_path and os.path.exists(screenshot_path):
            with open(screenshot_path, 'rb') as f:
                img = MIMEImage(f.read(), _subtype='png')
                img.add_header('Content-Disposition', 'attachment', 
                             filename=os.path.basename(screenshot_path))
                msg.attach(img)
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        log(f"✅ 邮件已发送至 {RECEIVER_EMAIL}")
        
        if screenshot_path and os.path.exists(screenshot_path):
            os.remove(screenshot_path)
    except Exception as e:
        log(f"❌ 邮件发送失败：{e}")
