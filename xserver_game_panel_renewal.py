#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
XServer Game Panel 直接登录续期脚本
登录页面: https://secure.xserver.ne.jp/xapanel/login/xmgame/game/

登录字段:
1. ログインID (Login ID)
2. ゲームパネルパスワード (Game Panel Password)
3. ご利用中のドメイン または IPアドレス (Domain or IP Address)
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
    # 账号配置 - Game Panel 专用
    LOGIN_ID = os.getenv("GAME_LOGIN_ID")  # ログインID
    GAME_PASSWORD = os.getenv("GAME_PASSWORD")  # ゲームパネルパスワード
    DOMAIN_OR_IP = os.getenv("DOMAIN_OR_IP")  # ご利用中のドメイン または IPアドレス
    
    # Game Panel 登录页面
    LOGIN_URL = "https://secure.xserver.ne.jp/xapanel/login/xmgame/game/"
    
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
    
    # 续期触发阈值 (小时)
    TRIGGER_HOUR = int(os.getenv("TRIGGER_HOUR", "23"))
    
    # ========== Game Panel 专用元素定位 ==========
    
    # 登录相关（实际字段名）
    LOGIN_ID_INPUT = "input[name='username']"
    PASSWORD_INPUT = "input[name='server_password']"
    DOMAIN_INPUT = "input[name='server_identify']"
    LOGIN_SUBMIT_BTN = "input[name='action_user_login']"
    
    # 续期按钮
    EXTEND_BUTTON = "//a[contains(text(), 'アップグレード・期限延長')]"
    
    # 到期时间元素 - 使用 CSS 选择器
    TTL_TEXT_SELECTOR = "span.ttlTxt"
    
    # 时间提取正则 - 从 ttlTxt 中提取
    # 例如: "2024年02月15日 23:59まで" 或 "あと 2日 5時間" 或 "(2026-02-14まで)" 或 "残り64時間23分"
    TIME_PATTERN_DATE = re.compile(r'(\d{4})年(\d{2})月(\d{2})日\s+(\d{2}):(\d{2})')
    TIME_PATTERN_DATE_ISO = re.compile(r'\((\d{4})-(\d{2})-(\d{2})まで\)')
    TIME_PATTERN_REMAIN = re.compile(r'あと\s+(\d+)日\s+(\d+)時間')
    TIME_PATTERN_REMAIN_HOURS = re.compile(r'残り(\d+)時間(\d+)分')


# ======================== 日志 ==========================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('game_panel_renewal.log', encoding='utf-8'),
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


# ======================== 核心类 ==========================

class XServerGamePanelRenewal:
    """XServer Game Panel 直接登录续期"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self._pw = None
        
        self.renewal_status: str = "Unknown"
        self.expiry_time: Optional[str] = None
        self.next_check_time: Optional[str] = None
        self.error_message: Optional[str] = None
        
        # 时区
        self.JST = datetime.timezone(timedelta(hours=9))
        self.LOCAL_TZ = datetime.timezone(timedelta(hours=8))
    
    # ---------- 缓存 ----------
    def load_cache(self) -> Optional[Dict]:
        if os.path.exists("game_panel_cache.json"):
            try:
                with open("game_panel_cache.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载缓存失败: {e}")
        return None
    
    def save_cache(self):
        cache = {
            "expiry_time": self.expiry_time,
            "next_check_time": self.next_check_time,
            "status": self.renewal_status,
            "last_check": datetime.datetime.now(timezone.utc).isoformat(),
        }
        try:
            with open("game_panel_cache.json", "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存缓存失败: {e}")
    
    # ---------- 下次执行时间记录 ----------
    def load_next_run_time(self) -> Optional[str]:
        """从 NEXT_RUN.md 读取下次执行时间"""
        if os.path.exists("NEXT_RUN.md"):
            try:
                with open("NEXT_RUN.md", "r", encoding="utf-8") as f:
                    content = f.read()
                    # 提取时间信息，格式: **下次执行时间**: `2026-02-13 23:59 (JST)`
                    import re
                    match = re.search(r'\*\*下次执行时间\*\*:\s*`([^`]+)`', content)
                    if match:
                        time_str = match.group(1).split(' (')[0]  # 移除时区标记
                        logger.info(f"📋 从 NEXT_RUN.md 读取: {time_str}")
                        return time_str
            except Exception as e:
                logger.error(f"读取 NEXT_RUN.md 失败: {e}")
        return None
    
    def save_next_run_time(self):
        """保存下次执行时间到 NEXT_RUN.md"""
        now = datetime.datetime.now(self.LOCAL_TZ)
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        
        content = "# 下次执行时间\n\n"
        content += f"**最后更新**: `{ts} (UTC+8)`\n\n"
        content += "---\n\n"
        
        if self.next_check_time:
            content += f"## ⏰ 下次执行时间\n\n"
            content += f"**下次执行时间**: `{self.next_check_time} (JST)`\n\n"
            
            # 计算距离下次执行的时间
            try:
                next_dt = datetime.datetime.strptime(
                    self.next_check_time, "%Y-%m-%d %H:%M"
                ).replace(tzinfo=self.JST)
                now_jst = datetime.datetime.now(self.JST)
                hours_until = (next_dt - now_jst).total_seconds() / 3600
                
                if hours_until > 0:
                    days = int(hours_until // 24)
                    hours = int(hours_until % 24)
                    content += f"**距离下次执行**: `{days}天 {hours}小时`\n\n"
                else:
                    content += f"**状态**: `已到执行时间`\n\n"
            except Exception as e:
                logger.error(f"计算时间差失败: {e}")
        else:
            content += f"## ℹ️ 暂无执行计划\n\n"
            content += f"请先运行一次脚本以获取服务器到期时间\n\n"
        
        if self.expiry_time:
            content += f"## 📅 服务器到期时间\n\n"
            content += f"**到期时间**: `{self.expiry_time} (JST)`\n\n"
        
        content += f"## 📊 最后执行状态\n\n"
        
        status_emoji = {
            "Success": "✅ 续期成功",
            "Unexpired": "ℹ️ 尚未到期",
            "Skipped": "⏸️ 跳过检查",
            "Failed": "❌ 执行失败",
            "Unknown": "❓ 未知状态"
        }
        
        content += f"**状态**: {status_emoji.get(self.renewal_status, self.renewal_status)}\n\n"
        
        if self.error_message:
            content += f"**错误信息**: `{self.error_message}`\n\n"
        
        content += "---\n\n"
        content += "*此文件由脚本自动生成和更新*\n"
        
        try:
            with open("NEXT_RUN.md", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info("📄 NEXT_RUN.md 已更新")
        except Exception as e:
            logger.error(f"保存 NEXT_RUN.md 失败: {e}")
    
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
        """初始化 Playwright 浏览器"""
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
            
            if Config.USE_HEADLESS:
                logger.info("ℹ️ 使用无头模式(headless=True)")
            else:
                logger.info("ℹ️ 使用非无头模式(headless=False)")
            
            if proxy_url:
                launch_args.append(f"--proxy-server={proxy_url}")
            
            launch_kwargs = {
                "headless": Config.USE_HEADLESS,
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
        """登录 XServer Game Panel"""
        try:
            logger.info("🌐 开始登录 XServer Game Panel")
            await self.page.goto(Config.LOGIN_URL, timeout=30000)
            await asyncio.sleep(3)
            await self.shot("01_login_page")
            
            # 调试：打印页面 HTML 片段
            logger.info("� 检查登页面表单元素...")
            form_html = await self.page.evaluate("""
                () => {
                    const forms = document.querySelectorAll('form');
                    const inputs = document.querySelectorAll('input');
                    return {
                        formCount: forms.length,
                        inputCount: inputs.length,
                        inputNames: Array.from(inputs).map(i => ({
                            name: i.name,
                            type: i.type,
                            id: i.id,
                            placeholder: i.placeholder
                        }))
                    };
                }
            """)
            logger.info(f"📋 表单数量: {form_html['formCount']}")
            logger.info(f"📋 输入框数量: {form_html['inputCount']}")
            logger.info(f"📋 输入框详情: {form_html['inputNames']}")
            
            # 尝试多种定位方式
            logger.info("📝 填写登录信息...")
            
            # 字段1: username (ログインID)
            try:
                await self.page.fill("input[name='username']", Config.LOGIN_ID, timeout=5000)
                logger.info("✅ 用户名字段: name='username'")
            except:
                await self.page.fill("input[id='username']", Config.LOGIN_ID, timeout=5000)
                logger.info("✅ 用户名字段: id='username'")
            
            # 字段2: server_password (ゲームパネルパスワード)
            try:
                await self.page.fill("input[name='server_password']", Config.GAME_PASSWORD, timeout=5000)
                logger.info("✅ 密码字段: name='server_password'")
            except:
                await self.page.fill("input[id='server_password']", Config.GAME_PASSWORD, timeout=5000)
                logger.info("✅ 密码字段: id='server_password'")
            
            # 字段3: server_identify (ご利用中のドメイン または IPアドレス)
            try:
                await self.page.fill("input[name='server_identify']", Config.DOMAIN_OR_IP, timeout=5000)
                logger.info("✅ 域名/IP字段: name='server_identify'")
            except:
                await self.page.fill("input[id='server_identify']", Config.DOMAIN_OR_IP, timeout=5000)
                logger.info("✅ 域名/IP字段: id='server_identify'")
            
            await self.shot("02_before_login")
            
            logger.info("📤 提交登录表单...")
            # 尝试多种提交方式
            try:
                await self.page.click("button[type='submit']", timeout=5000)
            except:
                try:
                    await self.page.click("input[type='submit']", timeout=5000)
                except:
                    # 按回车键提交
                    await self.page.press("input[type='password']", "Enter")
                    logger.info("✅ 通过回车键提交")
            
            await asyncio.sleep(5)
            await self.shot("03_after_login")
            
            # 验证登录成功
            current_url = self.page.url
            logger.info(f"🔍 当前 URL: {current_url}")
            
            if "login" not in current_url.lower() or "game" in current_url:
                logger.info("🎉 登录成功")
                return True
            
            logger.error("❌ 登录失败")
            self.error_message = "登录失败"
            return False
        except Exception as e:
            logger.error(f"❌ 登录错误: {e}")
            self.error_message = f"登录错误: {e}"
            return False
    
    # ---------- 提取到期时间 ----------
    async def get_expiry_time(self) -> bool:
        """从页面提取到期时间"""
        try:
            logger.info("🔍 开始提取到期时间...")
            
            # 先打印页面上所有 span 元素，帮助调试
            spans_info = await self.page.evaluate("""
                () => {
                    const spans = document.querySelectorAll('span');
                    return Array.from(spans).map(s => ({
                        class: s.className,
                        text: s.innerText.substring(0, 100)
                    })).filter(s => s.text.length > 0);
                }
            """)
            logger.info(f"📋 页面上的 span 元素: {spans_info[:10]}")  # 只显示前10个
            
            # 尝试定位时间元素
            ttl_text = None
            
            # 方法1: 尝试 span.ttlTxt (CSS 选择器)
            try:
                ttl_element = await self.page.wait_for_selector(
                    "span.ttlTxt",
                    timeout=5000
                )
                ttl_text = await ttl_element.inner_text()
                logger.info(f"📅 从 span.ttlTxt 提取: {ttl_text}")
            except Exception as e:
                logger.warning(f"⚠️ 无法定位 span.ttlTxt: {e}")
            
            # 方法2: 尝试 span.dateLimit
            if not ttl_text:
                try:
                    date_limit_element = await self.page.wait_for_selector(
                        "span.dateLimit",
                        timeout=5000
                    )
                    ttl_text = await date_limit_element.inner_text()
                    logger.info(f"📅 从 span.dateLimit 提取: {ttl_text}")
                except Exception as e:
                    logger.warning(f"⚠️ 无法定位 span.dateLimit: {e}")
            
            # 方法3: 从整个页面文本中提取
            if not ttl_text:
                try:
                    ttl_text = await self.page.evaluate("""
                        () => {
                            // 查找包含 "まで" 或 "あと" 的文本
                            const allText = document.body.innerText;
                            const timeMatch = allText.match(/(\d{4}年\d{2}月\d{2}日\s+\d{2}:\d{2}まで|あと\s+\d+日\s+\d+時間|\(\d{4}-\d{2}-\d{2}まで\)|残り\d+時間\d+分)/);
                            return timeMatch ? timeMatch[0] : null;
                        }
                    """)
                    if ttl_text:
                        logger.info(f"📅 从页面文本提取: {ttl_text}")
                except Exception as e:
                    logger.error(f"❌ 页面文本提取失败: {e}")
            
            if not ttl_text:
                logger.error("❌ 无法提取到期时间")
                await self.shot("04_no_ttl_text")
                return False
            
            # 解析时间
            now_jst = datetime.datetime.now(self.JST)
            
            # 方法1: 尝试匹配绝对日期 "2024年02月15日 23:59まで"
            date_match = Config.TIME_PATTERN_DATE.search(ttl_text)
            if date_match:
                year = int(date_match.group(1))
                month = int(date_match.group(2))
                day = int(date_match.group(3))
                hour = int(date_match.group(4))
                minute = int(date_match.group(5))
                
                expiry_dt = datetime.datetime(year, month, day, hour, minute, tzinfo=self.JST)
                self.expiry_time = expiry_dt.strftime("%Y-%m-%d %H:%M")
                
                # 计算剩余时间
                remaining_seconds = (expiry_dt - now_jst).total_seconds()
                remaining_hours = remaining_seconds / 3600
                
                logger.info(f"📅 到期时间: {self.expiry_time} (JST)")
                logger.info(f"📊 剩余时间: {remaining_hours:.2f} 小时")
                
                # 计算下次检查时间 (到期前 24 小时)
                next_check_dt = expiry_dt - timedelta(hours=24)
                self.next_check_time = next_check_dt.strftime("%Y-%m-%d %H:%M")
                logger.info(f"⏰ 下次检查时间: {self.next_check_time} (JST)")
                
                return True
            
            # 方法2: 尝试匹配 ISO 格式日期 "(2026-02-14まで)"
            date_iso_match = Config.TIME_PATTERN_DATE_ISO.search(ttl_text)
            if date_iso_match:
                year = int(date_iso_match.group(1))
                month = int(date_iso_match.group(2))
                day = int(date_iso_match.group(3))
                
                # 假设到期时间是当天的 23:59
                expiry_dt = datetime.datetime(year, month, day, 23, 59, tzinfo=self.JST)
                self.expiry_time = expiry_dt.strftime("%Y-%m-%d %H:%M")
                
                # 计算剩余时间
                remaining_seconds = (expiry_dt - now_jst).total_seconds()
                remaining_hours = remaining_seconds / 3600
                
                logger.info(f"📅 到期时间: {self.expiry_time} (JST)")
                logger.info(f"📊 剩余时间: {remaining_hours:.2f} 小时")
                
                # 计算下次检查时间 (到期前 24 小时)
                next_check_dt = expiry_dt - timedelta(hours=24)
                self.next_check_time = next_check_dt.strftime("%Y-%m-%d %H:%M")
                logger.info(f"⏰ 下次检查时间: {self.next_check_time} (JST)")
                
                return True
            
            # 方法3: 尝试匹配相对时间 "あと 2日 5時間"
            remain_match = Config.TIME_PATTERN_REMAIN.search(ttl_text)
            if remain_match:
                days = int(remain_match.group(1))
                hours = int(remain_match.group(2))
                
                total_hours = days * 24 + hours
                expiry_dt = now_jst + timedelta(hours=total_hours)
                self.expiry_time = expiry_dt.strftime("%Y-%m-%d %H:%M")
                
                logger.info(f"📅 到期时间: {self.expiry_time} (JST)")
                logger.info(f"📊 剩余时间: {total_hours} 小时")
                
                # 计算下次检查时间
                next_check_dt = expiry_dt - timedelta(hours=24)
                self.next_check_time = next_check_dt.strftime("%Y-%m-%d %H:%M")
                logger.info(f"⏰ 下次检查时间: {self.next_check_time} (JST)")
                
                return True
            
            # 方法4: 尝试匹配 "残り64時間23分"
            remain_hours_match = Config.TIME_PATTERN_REMAIN_HOURS.search(ttl_text)
            if remain_hours_match:
                hours = int(remain_hours_match.group(1))
                minutes = int(remain_hours_match.group(2))
                
                total_hours = hours + minutes / 60
                expiry_dt = now_jst + timedelta(hours=total_hours)
                self.expiry_time = expiry_dt.strftime("%Y-%m-%d %H:%M")
                
                logger.info(f"📅 到期时间: {self.expiry_time} (JST)")
                logger.info(f"📊 剩余时间: {total_hours:.2f} 小时")
                
                # 计算下次检查时间
                next_check_dt = expiry_dt - timedelta(hours=24)
                self.next_check_time = next_check_dt.strftime("%Y-%m-%d %H:%M")
                logger.info(f"⏰ 下次检查时间: {self.next_check_time} (JST)")
                
                return True
            
            logger.warning(f"⚠️ 无法解析时间格式: {ttl_text}")
            return False
            
        except Exception as e:
            logger.error(f"❌ 提取到期时间失败: {e}")
            return False
    
    # ---------- 判断是否需要续期 ----------
    async def should_renew(self) -> bool:
        """判断是否需要续期"""
        try:
            if not self.expiry_time:
                logger.warning("⚠️ 未获取到到期时间，无法判断")
                return True  # 保险起见，尝试续期
            
            now_jst = datetime.datetime.now(self.JST)
            expiry_dt = datetime.datetime.strptime(
                self.expiry_time, "%Y-%m-%d %H:%M"
            ).replace(tzinfo=self.JST)
            
            remaining_seconds = (expiry_dt - now_jst).total_seconds()
            remaining_hours = remaining_seconds / 3600
            
            logger.info(f"📊 当前时间: {now_jst.strftime('%Y-%m-%d %H:%M:%S')} (JST)")
            logger.info(f"📊 到期时间: {expiry_dt.strftime('%Y-%m-%d %H:%M:%S')} (JST)")
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
            return True
    
    # ---------- 点击续期按钮 ----------
    async def click_extend_button(self) -> bool:
        """点击アップグレード・期限延長按钮"""
        try:
            logger.info("🔍 查找续期按钮...")
            
            # 先调试：打印页面上所有链接和按钮
            links_info = await self.page.evaluate("""
                () => {
                    const links = document.querySelectorAll('a, button');
                    return Array.from(links).map(el => ({
                        tag: el.tagName,
                        text: el.innerText.substring(0, 100),
                        href: el.href || '',
                        class: el.className,
                        id: el.id
                    })).filter(el => el.text.length > 0);
                }
            """)
            logger.info(f"📋 页面上的链接和按钮: {links_info[:20]}")  # 显示前20个
            
            # 尝试多种定位方式
            extend_btn = None
            
            # 方法1: XPath - 包含文本 "アップグレード・期限延長"
            try:
                extend_btn = await self.page.wait_for_selector(
                    "xpath=//a[contains(text(), 'アップグレード・期限延長')]",
                    timeout=5000
                )
                logger.info("✅ 方法1成功: XPath 包含文本")
            except Exception as e:
                logger.warning(f"⚠️ 方法1失败: {e}")
            
            # 方法2: XPath - 包含文本 "期限延長"
            if not extend_btn:
                try:
                    extend_btn = await self.page.wait_for_selector(
                        "xpath=//a[contains(text(), '期限延長')]",
                        timeout=5000
                    )
                    logger.info("✅ 方法2成功: XPath 包含 '期限延長'")
                except Exception as e:
                    logger.warning(f"⚠️ 方法2失败: {e}")
            
            # 方法3: XPath - 包含文本 "アップグレード"
            if not extend_btn:
                try:
                    extend_btn = await self.page.wait_for_selector(
                        "xpath=//a[contains(text(), 'アップグレード')]",
                        timeout=5000
                    )
                    logger.info("✅ 方法3成功: XPath 包含 'アップグレード'")
                except Exception as e:
                    logger.warning(f"⚠️ 方法3失败: {e}")
            
            # 方法4: 通过 JavaScript 查找
            if not extend_btn:
                try:
                    found = await self.page.evaluate("""
                        () => {
                            const links = Array.from(document.querySelectorAll('a'));
                            const target = links.find(a => 
                                a.innerText.includes('アップグレード') || 
                                a.innerText.includes('期限延長')
                            );
                            if (target) {
                                target.setAttribute('data-extend-button', 'true');
                                return true;
                            }
                            return false;
                        }
                    """)
                    if found:
                        extend_btn = await self.page.wait_for_selector(
                            "a[data-extend-button='true']",
                            timeout=5000
                        )
                        logger.info("✅ 方法4成功: JavaScript 查找")
                except Exception as e:
                    logger.warning(f"⚠️ 方法4失败: {e}")
            
            if not extend_btn:
                logger.error("❌ 无法找到续期按钮")
                await self.shot("error_no_extend_button")
                self.error_message = "无法找到续期按钮"
                return False
            
            logger.info("🖱️ 点击アップグレード・期限延長按钮...")
            await extend_btn.click()
            await asyncio.sleep(3)
            await self.shot("05_after_click_extend")
            
            logger.info("✅ 续期按钮点击成功")
            return True
            
        except Exception as e:
            logger.error(f"❌ 点击续期按钮失败: {e}")
            await self.shot("error_extend_button")
            self.error_message = f"点击续期按钮失败: {e}"
            return False
    
    # ---------- README 生成 ----------
    def generate_readme(self):
        """生成状态报告"""
        now = datetime.datetime.now(self.LOCAL_TZ)
        ts = now.strftime("%Y-%m-%d %H:%M:%S")
        
        out = "# XServer Game Panel 续期状态\n\n"
        out += f"**运行时间**: `{ts} (UTC+8)`<br>\n"
        out += f"**登录方式**: Game Panel 直接登录<br>\n\n---\n\n"
        
        if self.renewal_status == "Success":
            out += (
                "## ✅ 续期成功\n\n"
                f"- 🕛 **到期时间**: `{self.expiry_time}`\n"
                f"- ⏰ **下次检查**: `{self.next_check_time}`\n"
            )
        elif self.renewal_status == "Unexpired":
            out += (
                "## ℹ️ 尚未到期\n\n"
                f"- 🕛 **到期时间**: `{self.expiry_time}`\n"
                f"- ⏰ **下次检查**: `{self.next_check_time}`\n"
                f"- 📊 **触发阈值**: 剩余 < {Config.TRIGGER_HOUR} 小时\n"
            )
        else:
            out += (
                "## ❌ 执行失败\n\n"
                f"- 🕛 **到期时间**: `{self.expiry_time or '未知'}`\n"
                f"- ⚠️ **错误**: {self.error_message or '未知'}\n"
            )
        
        out += f"\n---\n\n*最后更新: {ts}*\n"
        
        with open("README.md", "w", encoding="utf-8") as f:
            f.write(out)
        
        logger.info("📄 README.md 已更新")
    
    # ---------- 智能检查逻辑 ----------
    def should_run_check(self) -> bool:
        """基于 NEXT_RUN.md 判断是否需要运行检查"""
        next_check_time = self.load_next_run_time()
        
        if not next_check_time:
            logger.info("📋 无下次执行时间记录，需要运行检查")
            return True
        
        try:
            next_check_dt = datetime.datetime.strptime(
                next_check_time, "%Y-%m-%d %H:%M"
            ).replace(tzinfo=self.JST)
            now_jst = datetime.datetime.now(self.JST)
            
            if now_jst >= next_check_dt:
                logger.info(f"⏰ 已到检查时间 ({next_check_time})，需要运行检查")
                return True
            else:
                hours_until = (next_check_dt - now_jst).total_seconds() / 3600
                days = int(hours_until // 24)
                hours = int(hours_until % 24)
                logger.info(f"⏸️ 未到检查时间，还需等待 {days}天 {hours}小时")
                logger.info(f"📅 下次检查时间: {next_check_time} (JST)")
                return False
        except Exception as e:
            logger.error(f"❌ 解析检查时间失败: {e}")
            return True
    
    # ---------- 主流程 ----------
    async def run(self):
        """主执行流程"""
        try:
            logger.info("=" * 60)
            logger.info("🚀 XServer Game Panel 续期检查开始")
            logger.info("=" * 60)
            
            # 0. 智能检查：是否需要运行
            if not self.should_run_check():
                self.renewal_status = "Skipped"
                self.save_next_run_time()
                logger.info("=" * 60)
                logger.info("✅ 跳过本次检查 - 未到检查时间")
                logger.info("=" * 60)
                return
            
            # 1. 启动浏览器
            if not await self.setup_browser():
                self.renewal_status = "Failed"
                self.save_next_run_time()
                self.generate_readme()
                await Notifier.notify(
                    "❌ Game Panel 续期失败",
                    f"浏览器初始化失败: {self.error_message}"
                )
                return
            
            # 2. 登录
            if not await self.login():
                self.renewal_status = "Failed"
                self.save_next_run_time()
                self.generate_readme()
                await Notifier.notify(
                    "❌ Game Panel 续期失败",
                    f"登录失败: {self.error_message}"
                )
                return
            
            # 3. 提取到期时间
            if not await self.get_expiry_time():
                self.renewal_status = "Failed"
                self.save_next_run_time()
                self.generate_readme()
                await Notifier.notify(
                    "❌ Game Panel 续期失败",
                    "无法提取到期时间"
                )
                return
            
            # 4. 判断是否需要续期
            if not await self.should_renew():
                # 未到续期时间
                self.save_cache()
                self.save_next_run_time()
                self.generate_readme()
                await Notifier.notify(
                    "ℹ️ Game Panel 尚未到期",
                    f"当前到期时间: {self.expiry_time}\n"
                    f"下次检查时间: {self.next_check_time}\n"
                    f"触发阈值: 剩余 < {Config.TRIGGER_HOUR} 小时"
                )
                return
            
            # 5. 点击续期按钮
            if not await self.click_extend_button():
                self.renewal_status = "Failed"
                self.save_next_run_time()
                self.generate_readme()
                await Notifier.notify(
                    "❌ Game Panel 续期失败",
                    f"点击续期按钮失败: {self.error_message}"
                )
                return
            
            # 6. 这里可以继续添加后续的续期确认流程
            # TODO: 添加续期确认逻辑
            
            self.renewal_status = "Success"
            self.save_cache()
            self.save_next_run_time()
            self.generate_readme()
            
            await Notifier.notify(
                "✅ Game Panel 续期成功",
                f"到期时间: {self.expiry_time}\n"
                f"下次检查: {self.next_check_time}"
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
    runner = XServerGamePanelRenewal()
    await runner.run()


if __name__ == "__main__":
    asyncio.run(main())
