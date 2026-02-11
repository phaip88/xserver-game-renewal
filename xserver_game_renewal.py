#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XServer Game Server 自动续期脚本 (Playwright 版本)
基于 Xserver-VPS-Renew 项目改造，适配 XServer GAME 产品

主要改动：
1. 登录 URL: /xapanel/login/xserver/
2. 导航逻辑: 6步复杂导航 (サービス管理 → ゲーム用マルチサーバー → ...)
3. 续期操作: 三步确认流程
4. 到期时间提取: 从续期页面提取
"""

import asyncio
import re
import datetime
from datetime import timezone, timedelta
import os
import json
import logging
from typing import Optional, Dict

from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeout

# 尝试兼容 playwright-stealth
try:
    from playwright_stealth import stealth_async
    STEALTH_VERSION = 'old'
except ImportError:
    STEALTH_VERSION = 'new'
    stealth_async = None


# ======================== 配置 ==========================

class Config:
    # 账号配置
    LOGIN_EMAIL = os.getenv("XSERVER_EMAIL")
    LOGIN_PASSWORD = os.getenv("XSERVER_PASSWORD")
    
    # Game Server 专用配置
    LOGIN_URL = "https://secure.xserver.ne.jp/xapanel/login/xserver/"
    
    # 浏览器配置
    USE_HEADLESS = os.getenv("USE_HEADLESS", "true").lower() == "true"
    WAIT_TIMEOUT = int(os.getenv("WAIT_TIMEOUT", "30000"))
    
    # 通知配置
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
    
    # 邮件配置 (可选)
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.qq.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SENDER_EMAIL = os.getenv("SENDER_EMAIL")
    SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
    RECEIVER_EMAIL = os.getenv("RECEIVER_EMAIL")
    
    # 代理配置
    PROXY_SERVER = os.getenv("PROXY_SERVER")
    
    # 验证码 API
    CAPTCHA_API_URL = os.getenv(
        "CAPTCHA_API_URL",
        "https://captcha-120546510085.asia-northeast1.run.app"
    )
    
    # 续期触发阈值 (小时)
    TRIGGER_HOUR = int(os.getenv("TRIGGER_HOUR", "23"))
    
    # ========== Game Server 专用元素定位 ==========
    
    # 登录相关
    EMAIL_INPUT = "input[name='memberid']"
    PASSWORD_INPUT = "input[name='user_password']"
    LOGIN_SUBMIT_BTN = "input[type='submit']"
    
    # 导航相关
    SERVICE_MENU_TOGGLE = "//span[contains(@class, 'serviceNav__toggle') and contains(text(), 'サービス管理')]"
    GAME_SERVER_LINK = "//a[@id='ga-xsa-serviceNav-xmgame' and @href='/xapanel/xmgame/index']"
    GAME_MANAGE_BTN = "//a[contains(text(), 'ゲーム管理') and contains(@class, 'btn--primary')]"
    SERVER_HOME_FLAG = "//*[contains(text(), 'サーバー管理')]"
    EXTEND_BUTTON = "//a[contains(text(), 'アップグレード・期限延長')]"
    
    # 续期相关
    STEP1_RENEW_BTN = "//button[contains(text(), '期限を延長する')]"
    STEP2_CONFIRM_BTN = "//button[contains(text(), '確認画面に進む')]"
    STEP3_FINAL_BTN = "//button[contains(text(), '期限を延長する')]"
    
    # 时间提取正则
    TIME_EXTRACT_PATTERN = re.compile(
        r'更新をご希望の場合は、(\d{4}-\d{2}-\d{2} \d{2}:\d{2})以降にお試しください'
    )


# ======================== 日志 ==========================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('game_renewal.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


# ======================== 通知器 ==========================

class Notifier:
    @staticmethod
    async def send_telegram(message: str):
        if not all([Config.TELEGRAM_BOT_TOKEN, Config.TELEGRAM_CHAT_ID]):
            return
        try:
            import aiohttp
            url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": Config.TELEGRAM_CHAT_ID,
                "text": message,
                "parse_mode": "HTML"
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as resp:
                    if resp.status == 200:
                        logger.info("✅ Telegram 通知发送成功")
                    else:
                        logger.error(f"❌ Telegram 返回非 200 状态码: {resp.status}")
        except Exception as e:
            logger.error(f"❌ Telegram 发送失败: {e}")
    
    @staticmethod
    async def send_email(subject: str, content: str):
        """邮件通知 (备用)"""
        if not all([Config.SENDER_EMAIL, Config.SENDER_PASSWORD, Config.RECEIVER_EMAIL]):
            return
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            msg = MIMEMultipart()
            msg['From'] = Config.SENDER_EMAIL
            msg['To'] = Config.RECEIVER_EMAIL
            msg['Subject'] = subject
            msg.attach(MIMEText(content, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT)
            server.starttls()
            server.login(Config.SENDER_EMAIL, Config.SENDER_PASSWORD)
            server.send_message(msg)
            server.quit()
            logger.info(f"✅ 邮件已发送至 {Config.RECEIVER_EMAIL}")
        except Exception as e:
            logger.error(f"❌ 邮件发送失败: {e}")
    
    @staticmethod
    async def notify(subject: str, message: str):
        """统一通知接口"""
        await Notifier.send_telegram(message)
        await Notifier.send_email(subject, message)


# ======================== 验证码识别 ==========================

class CaptchaSolver:
    """外部 API OCR 验证码识别器 (复用 VPS 版本)"""
    
    def __init__(self):
        self.api_url = Config.CAPTCHA_API_URL
    
    def _validate_code(self, code: str) -> bool:
        """验证识别出的验证码是否合理"""
        if not code:
            return False
        
        if len(code) < 4 or len(code) > 6:
            logger.warning(f"⚠️ 验证码长度异常: {len(code)} 位")
            return False
        
        if len(set(code)) == 1:
            logger.warning(f"⚠️ 验证码可疑(所有数字相同): {code}")
            return False
        
        if not code.isdigit():
            logger.warning(f"⚠️ 验证码包含非数字字符: {code}")
            return False
        
        return True
    
    async def solve(self, img_data_url: str) -> Optional[str]:
        """使用外部 API 识别验证码"""
        try:
            import aiohttp
            
            logger.info(f"📤 发送验证码到 API: {self.api_url}")
            
            max_retries = 3
            retry_count = 0
            
            while retry_count < max_retries:
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.post(
                            self.api_url,
                            data=img_data_url,
                            headers={'Content-Type': 'text/plain'},
                            timeout=aiohttp.ClientTimeout(total=20)
                        ) as resp:
                            if not resp.ok:
                                raise Exception(f"API 请求失败: {resp.status}")
                            
                            code_response = await resp.text()
                            code = code_response.strip()
                            
                            logger.info(f"📥 API 返回验证码: {code}")
                            
                            if code and len(code) >= 4:
                                numbers = re.findall(r'\d+', code)
                                if numbers:
                                    code = numbers[0][:6]
                                    
                                    if self._validate_code(code):
                                        logger.info(f"🎯 API 识别成功: {code}")
                                        return code
                            
                            raise Exception('API 返回无效验证码')
                
                except Exception as err:
                    retry_count += 1
                    if retry_count >= max_retries:
                        logger.error(f"❌ API 识别失败(已重试 {max_retries} 次): {err}")
                        return None
                    logger.info(f"🔄 验证码识别失败,正在进行第 {retry_count} 次重试...")
                    await asyncio.sleep(2)
        
        except Exception as e:
            logger.error(f"❌ API 识别错误: {e}")
        
        return None


# ======================== 核心类 ==========================

class XServerGameRenewal:
    """XServer Game Server 自动续期"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self._pw = None
        
        self.renewal_status: str = "Unknown"
        self.old_expiry_time: Optional[str] = None
        self.new_expiry_time: Optional[str] = None
        self.error_message: Optional[str] = None
        
        self.captcha_solver = CaptchaSolver()
        
        # 时区
        self.JST = datetime.timezone(timedelta(hours=9))
        self.LOCAL_TZ = datetime.timezone(timedelta(hours=8))
    
    # ---------- 缓存 ----------
    def load_cache(self) -> Optional[Dict]:
        if os.path.exists("game_cache.json"):
            try:
                with open("game_cache.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载缓存失败: {e}")
        return None
    
    def save_cache(self):
        cache = {
            "last_expiry": self.old_expiry_time,
            "status": self.renewal_status,
            "last_check": datetime.datetime.now(timezone.utc).isoformat(),
        }
        try:
            with open("game_cache.json", "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    # ---------- 截图 ----------
    async def shot(self, name: str):
        """安全截图"""
        if not self.page:
            return
        try:
            await self.page.screenshot(path=f"{name}.png", full_page=True)
        except Exception:
            pass

    # ---------- 浏览器初始化 ----------
    async def setup_browser(self) -> bool:
        """初始化 Playwright 浏览器 (复用 VPS 版本)"""
        try:
            self._pw = await async_playwright().start()
            launch_args = [
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
                "--disable-infobars",
                "--start-maximized",
            ]
            
            # 代理配置
            proxy_url = None
            if Config.PROXY_SERVER:
                proxy_url = Config.PROXY_SERVER
                logger.info(f"🌐 使用代理: {Config.PROXY_SERVER}")
            
            # 强制关闭无头模式 (Turnstile 需要)
            if Config.USE_HEADLESS:
                logger.info("⚠️ 为了通过 Turnstile，强制使用非无头模式(headless=False)")
            else:
                logger.info("ℹ️ 已配置非无头模式(headless=False)")
            
            if proxy_url:
                launch_args.append(f"--proxy-server={proxy_url}")
            
            launch_kwargs = {
                "headless": False,  # 关键：强制关闭 headless
                "args": launch_args
            }
            
            self.browser = await self._pw.chromium.launch(**launch_kwargs)
            
            context_options = {
                "viewport": {"width": 1920, "height": 1080},
                "locale": "ja-JP",
                "timezone_id": "Asia/Tokyo",
                "user_agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
            }
            
            self.context = await self.browser.new_context(**context_options)
            
            # Anti-bot 注入
            await self.context.add_init_script("""
Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
Object.defineProperty(navigator, 'plugins', {get: () => [1,2,3]});
Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN','ja-JP','en-US']});
Object.defineProperty(navigator, 'permissions', {
    get: () => ({
        query: ({name}) => Promise.resolve({state: 'granted'})
    })
});
""")
            
            self.page = await self.context.new_page()
            self.page.set_default_timeout(Config.WAIT_TIMEOUT)
            
            # 旧版 stealth 支持
            if STEALTH_VERSION == 'old' and stealth_async is not None:
                await stealth_async(self.page)
            else:
                logger.info("ℹ️ 使用新版 playwright_stealth 或未安装,跳过 stealth 处理")
            
            logger.info("✅ 浏览器初始化成功")
            return True
        except Exception as e:
            logger.error(f"❌ 浏览器初始化失败: {e}")
            self.error_message = str(e)
            return False
    
    # ---------- 登录 ----------
    async def login(self) -> bool:
        """登录 XServer Game Server"""
        try:
            logger.info("🌐 开始登录 XServer Game Server")
            await self.page.goto(Config.LOGIN_URL, timeout=30000)
            await asyncio.sleep(2)
            await self.shot("01_login_page")
            
            # 填写账号密码
            await self.page.fill(Config.EMAIL_INPUT, Config.LOGIN_EMAIL)
            await self.page.fill(Config.PASSWORD_INPUT, Config.LOGIN_PASSWORD)
            await self.shot("02_before_login")
            
            logger.info("📤 提交登录表单...")
            await self.page.click(Config.LOGIN_SUBMIT_BTN)
            await asyncio.sleep(5)
            await self.shot("03_after_login")
            
            # 验证登录成功
            if "xmgame" in self.page.url or "login" not in self.page.url.lower():
                logger.info("🎉 登录成功")
                return True
            
            logger.error("❌ 登录失败")
            self.error_message = "登录失败"
            return False
        except Exception as e:
            logger.error(f"❌ 登录错误: {e}")
            self.error_message = f"登录错误: {e}"
            return False
    
    # ---------- 导航到续期页面 (Game Server 专用) ----------
    async def navigate_to_extend_page(self) -> bool:
        """6步导航到续期页面"""
        try:
            logger.info("🔍 开始导航到续期页面...")
            
            # 步骤 1: 展开"サービス管理"菜单
            logger.info("🔍 步骤1: 展开サービス管理菜单...")
            await asyncio.sleep(2)
            toggle_btn = await self.page.wait_for_selector(
                Config.SERVICE_MENU_TOGGLE, 
                timeout=10000
            )
            await toggle_btn.click()
            await asyncio.sleep(3)
            await self.shot("04_service_menu_opened")
            
            # 验证菜单展开
            game_link_visible = await self.page.is_visible(Config.GAME_SERVER_LINK)
            if not game_link_visible:
                raise Exception("サービス管理菜单展开失败")
            logger.info("✅ サービス管理菜单展开成功")
            
            # 步骤 2: 点击"ゲーム用マルチサーバー"
            logger.info("🔍 步骤2: 点击ゲーム用マルチサーバー...")
            game_link = await self.page.wait_for_selector(
                Config.GAME_SERVER_LINK,
                timeout=10000
            )
            await game_link.click()
            await asyncio.sleep(5)
            await self.shot("05_game_server_page")
            
            # 验证进入 XServer GAMEs 页面
            content = await self.page.content()
            if "XServer GAMEs" not in content and "xmgame" not in self.page.url:
                raise Exception("未进入 XServer GAMEs 页面")
            logger.info("✅ 成功进入 XServer GAMEs 页面")
            
            # 步骤 3: 点击蓝色"ゲーム管理"按钮
            logger.info("🔍 步骤3: 点击ゲーム管理按钮...")
            manage_btn = await self.page.wait_for_selector(
                Config.GAME_MANAGE_BTN,
                timeout=10000
            )
            await manage_btn.click()
            await asyncio.sleep(5)
            await self.shot("06_server_home")
            
            # 验证进入服务器主页
            content = await self.page.content()
            if "サーバー管理" not in content:
                raise Exception("未进入服务器主页")
            logger.info("✅ 成功进入服务器主页")
            
            # 步骤 4: 点击"アップグレード・期限延長"
            logger.info("🔍 步骤4: 点击アップグレード・期限延長...")
            extend_btn = await self.page.wait_for_selector(
                Config.EXTEND_BUTTON,
                timeout=10000
            )
            await extend_btn.click()
            await asyncio.sleep(5)
            await self.shot("07_extend_page")
            
            logger.info("✅ 成功进入续期页面")
            return True
            
        except Exception as e:
            logger.error(f"❌ 导航失败: {e}")
            await self.shot("error_navigation")
            self.error_message = f"导航失败: {e}"
            return False

    # ---------- Cloudflare Turnstile 处理 (复用 VPS 版本) ----------
    async def complete_turnstile_verification(self, max_wait: int = 120) -> bool:
        """使用多种方法尝试完成 Cloudflare Turnstile 验证"""
        try:
            logger.info("🔐 开始 Cloudflare Turnstile 验证流程...")
            
            # 检查是否有 Turnstile
            has_turnstile = await self.page.evaluate("""
                () => {
                    return document.querySelector('.cf-turnstile') !== null;
                }
            """)
            
            if not has_turnstile:
                logger.info("ℹ️ 未检测到 Cloudflare Turnstile,跳过验证")
                return True
            
            logger.info("🔍 检测到 Turnstile,尝试多种方法触发验证...")
            
            # 方法1: 获取 iframe 并尝试坐标点击
            try:
                await asyncio.sleep(3)
                
                iframe_info = await self.page.evaluate("""
                    () => {
                        const container = document.querySelector('.cf-turnstile');
                        if (!container) return null;
                        
                        const iframe = container.querySelector('iframe');
                        if (!iframe) return null;
                        
                        const rect = iframe.getBoundingClientRect();
                        return {
                            x: rect.x,
                            y: rect.y,
                            width: rect.width,
                            height: rect.height,
                            visible: rect.width > 0 && rect.height > 0
                        };
                    }
                """)
                
                if iframe_info and iframe_info['visible']:
                    click_x = iframe_info['x'] + 35
                    click_y = iframe_info['y'] + (iframe_info['height'] / 2)
                    
                    logger.info(f"🖱️ 方法1: 点击 iframe 坐标 ({click_x:.0f}, {click_y:.0f})")
                    await self.page.mouse.click(click_x, click_y)
                    await asyncio.sleep(2)
                    await self.shot("08_turnstile_method1")
                else:
                    logger.info("⚠️ 方法1: 无法获取 iframe 位置")
            
            except Exception as e:
                logger.info(f"ℹ️ 方法1 失败: {e}")
            
            # 方法2: 模拟真实用户鼠标移动
            try:
                logger.info("🖱️ 方法2: 模拟真实用户鼠标移动...")
                
                iframe_info = await self.page.evaluate("""
                    () => {
                        const container = document.querySelector('.cf-turnstile');
                        if (!container) return null;
                        const iframe = container.querySelector('iframe');
                        if (!iframe) return null;
                        const rect = iframe.getBoundingClientRect();
                        return {x: rect.x + 35, y: rect.y + rect.height/2};
                    }
                """)
                
                if iframe_info:
                    await self.page.mouse.move(100, 100)
                    await asyncio.sleep(0.5)
                    
                    steps = 15
                    current_x, current_y = 100, 100
                    target_x, target_y = iframe_info['x'], iframe_info['y']
                    
                    for i in range(steps):
                        x = current_x + (target_x - current_x) * (i + 1) / steps
                        y = current_y + (target_y - current_y) * (i + 1) / steps
                        await self.page.mouse.move(x, y)
                        await asyncio.sleep(0.06)
                    
                    await self.page.mouse.down()
                    await asyncio.sleep(0.15)
                    await self.page.mouse.up()
                    
                    logger.info("✅ 方法2: 已模拟真实点击")
                    await asyncio.sleep(3)
                    await self.shot("08_turnstile_method2")
            
            except Exception as e:
                logger.info(f"ℹ️ 方法2 失败: {e}")
            
            # 模拟页面滚动
            try:
                await self.page.mouse.move(200, 200, steps=20)
                await asyncio.sleep(0.4)
                await self.page.evaluate("window.scrollBy(0, 300)")
                await asyncio.sleep(0.6)
                await self.page.evaluate("window.scrollBy(0, -200)")
                await asyncio.sleep(0.5)
            except Exception:
                pass
            
            # 等待验证完成
            logger.info("⏳ 等待 Turnstile 验证完成...")
            
            for i in range(max_wait):
                await asyncio.sleep(1)
                
                verification_status = await self.page.evaluate("""
                    () => {
                        const tokenField = document.querySelector('[name="cf-turnstile-response"]');
                        const hasToken = tokenField && tokenField.value && tokenField.value.length > 0;
                        
                        const pageText = document.body.innerText || document.body.textContent;
                        const hasSuccessText = pageText.includes('成功しました') || pageText.includes('成功');
                        
                        const container = document.querySelector('.cf-turnstile');
                        let hasCheckmark = false;
                        if (container) {
                            hasCheckmark = container.classList.contains('success') ||
                                           container.classList.contains('verified') ||
                                           container.querySelector('[aria-checked="true"]') !== null;
                        }
                        
                        return {
                            hasToken: hasToken,
                            hasSuccessText: hasSuccessText,
                            hasCheckmark: hasCheckmark,
                            verified: hasToken || hasSuccessText || hasCheckmark
                        };
                    }
                """)
                
                if verification_status['verified']:
                    logger.info("✅ Cloudflare Turnstile 验证成功!")
                    await self.shot("08_turnstile_success")
                    return True
                
                if i % 10 == 0 and i > 0:
                    logger.info(f"⏳ Turnstile 验证中... ({i}/{max_wait}秒)")
            
            logger.warning(f"⚠️ Turnstile 验证超时({max_wait}秒)")
            await self.shot("08_turnstile_timeout")
            return False
        
        except Exception as e:
            logger.error(f"❌ Turnstile 验证失败: {e}")
            return False

    # ---------- 提取到期时间 (Game Server 专用) ----------
    async def get_expiry(self) -> bool:
        """从续期页面提取到期时间"""
        try:
            logger.info("🔍 开始提取到期时间...")
            content = await self.page.content()
            
            match = Config.TIME_EXTRACT_PATTERN.search(content)
            
            if match:
                renew_start_str = match.group(1)
                renew_start_time = datetime.datetime.strptime(
                    renew_start_str, "%Y-%m-%d %H:%M"
                )
                # 推导到期时间 (续期开始时间 + 24小时)
                renew_start_jst = renew_start_time.replace(tzinfo=self.JST)
                expire_time_jst = renew_start_jst + timedelta(hours=24)
                
                self.old_expiry_time = expire_time_jst.strftime("%Y-%m-%d")
                logger.info(f"📅 可续期开始时间: {renew_start_jst.strftime('%Y-%m-%d %H:%M:%S')} (JST)")
                logger.info(f"📅 推导到期时间: {self.old_expiry_time} (JST)")
                return True
            
            logger.warning("⚠️ 未能提取到期时间")
            return False
        except Exception as e:
            logger.error(f"❌ 提取到期时间失败: {e}")
            return False
    
    # ---------- 判断是否需要续期 ----------
    async def should_renew(self) -> bool:
        """判断是否需要续期 (剩余时间 < TRIGGER_HOUR)"""
        try:
            if not self.old_expiry_time:
                logger.warning("⚠️ 未获取到到期时间，无法判断")
                return True  # 保险起见，尝试续期
            
            # 使用 JST 当前时间
            now_jst = datetime.datetime.now(self.JST)
            expiry_date = datetime.datetime.strptime(
                self.old_expiry_time, "%Y-%m-%d"
            ).replace(tzinfo=self.JST)
            
            # 计算剩余时间
            remaining_seconds = (expiry_date - now_jst).total_seconds()
            remaining_hours = remaining_seconds / 3600
            
            logger.info(f"📊 当前时间: {now_jst.strftime('%Y-%m-%d %H:%M:%S')} (JST)")
            logger.info(f"📊 到期时间: {expiry_date.strftime('%Y-%m-%d %H:%M:%S')} (JST)")
            logger.info(f"📊 剩余时间: {remaining_hours:.2f} 小时")
            logger.info(f"📊 触发阈值: {Config.TRIGGER_HOUR} 小时")
            
            if remaining_hours < Config.TRIGGER_HOUR:
                logger.info(f"✅ 剩余时间 < {Config.TRIGGER_HOUR} 小时，需要续期")
                return True
            else:
                logger.info(f"ℹ️ 剩余时间 >= {Config.TRIGGER_HOUR} 小时，暂不需要续期")
                self.renewal_status = "Unexpired"
                return False
        
        except Exception as e:
            logger.error(f"❌ 判断是否需要续期失败: {e}")
            return True  # 保险起见，尝试续期
    
    # ---------- 提交续期 (Game Server 三步确认) ----------
    async def submit_extend(self) -> bool:
        """提交续期 - Game Server 三步确认流程"""
        try:
            logger.info("📄 开始提交续期表单 (三步确认)")
            await asyncio.sleep(3)
            
            # 模拟用户行为
            logger.info("👤 模拟用户行为...")
            try:
                await self.page.mouse.move(50, 50, steps=25)
                await asyncio.sleep(0.7)
                await self.page.mouse.move(200, 160, steps=20)
                await asyncio.sleep(0.6)
                await self.page.evaluate("window.scrollBy(0, 300)")
                await asyncio.sleep(0.8)
                await self.page.evaluate("window.scrollBy(0, -200)")
                await asyncio.sleep(0.6)
            except Exception:
                pass
            
            # 步骤 1: 处理 Turnstile (如果有)
            logger.info("🔐 步骤1: 检查并处理 Cloudflare Turnstile...")
            turnstile_success = await self.complete_turnstile_verification(max_wait=90)
            
            if not turnstile_success:
                logger.warning("⚠️ Turnstile 验证未完全确认,但继续尝试提交...")
            
            await asyncio.sleep(2)
            
            # 步骤 2: 点击第一个"期限を延長する"按钮
            logger.info("🖱️ 步骤2: 点击第一个「期限を延長する」按钮...")
            await self.shot("09_before_step1")
            
            step1_btn = await self.page.wait_for_selector(
                Config.STEP1_RENEW_BTN,
                timeout=10000
            )
            await step1_btn.click()
            await asyncio.sleep(3)
            await self.shot("10_after_step1")
            logger.info("✅ 第一步完成")
            
            # 步骤 3: 点击"確認画面に進む"按钮
            logger.info("🖱️ 步骤3: 点击「確認画面に進む」按钮...")
            step2_btn = await self.page.wait_for_selector(
                Config.STEP2_CONFIRM_BTN,
                timeout=10000
            )
            await step2_btn.click()
            await asyncio.sleep(3)
            await self.shot("11_after_step2")
            logger.info("✅ 第二步完成")
            
            # 步骤 4: 点击最后的"期限を延長する"按钮
            logger.info("🖱️ 步骤4: 点击最终确认「期限を延長する」按钮...")
            step3_btn = await self.page.wait_for_selector(
                Config.STEP3_FINAL_BTN,
                timeout=10000
            )
            await step3_btn.click()
            await asyncio.sleep(5)
            await self.shot("12_after_step3")
            logger.info("✅ 第三步完成")
            
            # 步骤 5: 验证续期成功
            logger.info("🔍 验证续期结果...")
            
            # 方法1: 检查按钮是否消失
            try:
                await self.page.wait_for_selector(
                    Config.STEP3_FINAL_BTN,
                    state='hidden',
                    timeout=5000
                )
                logger.info("✅ 续期按钮已消失，续期成功")
                self.renewal_status = "Success"
                self.new_expiry_time = self.old_expiry_time
                return True
            except:
                pass
            
            # 方法2: 检查页面内容
            content = await self.page.content()
            
            if any(success in content for success in [
                "完了",
                "継続",
                "完成",
                "更新しました",
                "延長しました"
            ]):
                logger.info("🎉 续期成功 (检测到成功标识)")
                self.renewal_status = "Success"
                self.new_expiry_time = self.old_expiry_time
                return True
            
            # 检查错误
            if any(err in content for err in [
                "エラー",
                "間違",
                "失敗"
            ]):
                logger.error("❌ 续期失败 (检测到错误标识)")
                await self.shot("12_error")
                self.renewal_status = "Failed"
                self.error_message = "续期失败"
                return False
            
            logger.warning("⚠️ 续期结果未知")
            self.renewal_status = "Unknown"
            return False
        
        except Exception as e:
            logger.error(f"❌ 续期错误: {e}")
            await self.shot("error_submit")
            self.renewal_status = "Failed"
            self.error_message = str(e)
            return False

    # ---------- README 生成 ----------
    def generate_readme(self):
        """生成状态报告"""
        now = datetime.datetime.now(self.LOCAL_TZ)
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        
        out = "# XServer Game Server 自动续期状态\n\n"
        out += f"**运行时间**: `{ts} (UTC+8)`<br>\n"
        out += f"**产品**: XServer GAME (ゲーム用マルチサーバー)<br>\n\n---\n\n"
        
        if self.renewal_status == "Success":
            out += (
                "## ✅ 续期成功\n\n"
                f"- 🕛 **旧到期**: `{self.old_expiry_time}`\n"
                f"- 🕡 **新到期**: `{self.new_expiry_time}`\n"
            )
        elif self.renewal_status == "Unexpired":
            out += (
                "## ℹ️ 尚未到期\n\n"
                f"- 🕛 **到期时间**: `{self.old_expiry_time}`\n"
                f"- 📊 **触发阈值**: 剩余 < {Config.TRIGGER_HOUR} 小时\n"
            )
        else:
            out += (
                "## ❌ 续期失败\n\n"
                f"- 🕛 **到期**: `{self.old_expiry_time or '未知'}`\n"
                f"- ⚠️ **错误**: {self.error_message or '未知'}\n"
            )
        
        out += f"\n---\n\n*最后更新: {ts}*\n"
        
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(out)
        
        logger.info("📄 README.md 已更新")
    
    # ---------- 主流程 ----------
    async def run(self):
        """主执行流程"""
        try:
            logger.info("=" * 60)
            logger.info("🚀 XServer Game Server 自动续期开始")
            logger.info("=" * 60)
            
            # 1. 启动浏览器
            if not await self.setup_browser():
                self.renewal_status = "Failed"
                self.generate_readme()
                await Notifier.notify(
                    "❌ Game Server 续期失败",
                    f"浏览器初始化失败: {self.error_message}"
                )
                return
            
            # 2. 登录
            if not await self.login():
                self.renewal_status = "Failed"
                self.generate_readme()
                await Notifier.notify(
                    "❌ Game Server 续期失败",
                    f"登录失败: {self.error_message}"
                )
                return
            
            # 3. 导航到续期页面
            if not await self.navigate_to_extend_page():
                self.renewal_status = "Failed"
                self.generate_readme()
                await Notifier.notify(
                    "❌ Game Server 续期失败",
                    f"导航失败: {self.error_message}"
                )
                return
            
            # 4. 提取到期时间
            await self.get_expiry()
            
            # 5. 判断是否需要续期
            if not await self.should_renew():
                # 未到续期时间
                self.generate_readme()
                await Notifier.notify(
                    "ℹ️ Game Server 尚未到期",
                    f"当前到期时间: {self.old_expiry_time}\n"
                    f"触发阈值: 剩余 < {Config.TRIGGER_HOUR} 小时"
                )
                return
            
            # 6. 提交续期
            await self.submit_extend()
            
            # 7. 保存缓存 & README & 通知
            self.save_cache()
            self.generate_readme()
            
            if self.renewal_status == "Success":
                await Notifier.notify(
                    "✅ Game Server 续期成功",
                    f"续期成功，新到期时间: {self.new_expiry_time}"
                )
            elif self.renewal_status == "Unexpired":
                await Notifier.notify(
                    "ℹ️ Game Server 尚未到期",
                    f"当前到期时间: {self.old_expiry_time}"
                )
            else:
                await Notifier.notify(
                    "❌ Game Server 续期失败",
                    f"错误信息: {self.error_message or '未知错误'}"
                )
        
        finally:
            logger.info("=" * 60)
            logger.info(f"✅ 流程完成 - 状态: {self.renewal_status}")
            logger.info("=" * 60)
            # 关闭浏览器
            try:
                if self.page:
                    await self.page.close()
                if self.context:
                    await self.context.close()
                if self.browser:
                    await self.browser.close()
                if self._pw:
                    await self._pw.stop()
                logger.info("🧹 浏览器已关闭")
            except Exception as e:
                logger.warning(f"关闭浏览器时出错: {e}")


async def main():
    """主入口"""
    runner = XServerGameRenewal()
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
