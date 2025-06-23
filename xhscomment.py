import time
import random
import pandas as pd
import json
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium.webdriver.edge.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.microsoft import EdgeChromiumDriverManager
from urllib.parse import urlparse

class XiaohongshuSeleniumCrawler:
    def __init__(self, headless=False):
        """
        初始化Selenium爬虫
        :param headless: 是否使用无头模式
        """
        self.comments_data = []
        self.setup_driver(headless)
        
    def setup_driver(self, headless=False):
        """
        设置Microsoft Edge浏览器驱动
        """
        edge_options = Options()
        
        # 基本配置
        edge_options.add_argument('--no-sandbox')
        edge_options.add_argument('--disable-dev-shm-usage')
        edge_options.add_argument('--disable-blink-features=AutomationControlled')
        edge_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        edge_options.add_experimental_option('useAutomationExtension', False)
        
        # 设置用户代理
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0"
        edge_options.add_argument(f'--user-agent={user_agent}')
        
        # 允许图片加载（登录需要验证码）
        prefs = {
            "profile.managed_default_content_settings.images": 1,  # 允许图片
            "profile.default_content_setting_values.notifications": 2,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.geolocation": 2
        }
        edge_options.add_experimental_option("prefs", prefs)
        
        if headless:
            edge_options.add_argument('--headless')
            
        # 设置窗口大小
        edge_options.add_argument('--window-size=1920,1080')
        
        try:
            # 自动下载和设置EdgeDriver
            service = Service(EdgeChromiumDriverManager().install())
            self.driver = webdriver.Edge(service=service, options=edge_options)
            
            # 隐藏自动化特征
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            print("Microsoft Edge浏览器启动成功")
        except Exception as e:
            print(f"浏览器启动失败: {e}")
            print("请确保已安装Microsoft Edge浏览器")
            raise
    
    def extract_note_id(self, url):
        """
        从URL中提取笔记ID
        """
        patterns = [
            r'/explore/([a-f0-9]+)',
            r'/discovery/item/([a-f0-9]+)',
            r'noteId=([a-f0-9]+)',
            r'/([a-f0-9]{24})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        raise ValueError("无法从URL中提取笔记ID")
    
    def wait_for_page_load(self, timeout=30):
        """
        等待页面加载完成
        """
        try:
            WebDriverWait(self.driver, timeout).until(
                lambda driver: driver.execute_script("return document.readyState") == "complete"
            )
            # 额外等待一下，确保动态内容加载
            time.sleep(2)
            return True
        except TimeoutException:
            print("页面加载超时")
            return False
    
    def simulate_human_behavior(self):
        """
        模拟人类行为
        """
        # 随机滚动
        scroll_height = random.randint(100, 500)
        self.driver.execute_script(f"window.scrollBy(0, {scroll_height});")
        
        # 随机等待
        time.sleep(random.uniform(1, 3))
        
        # 随机鼠标移动
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            webdriver.ActionChains(self.driver).move_to_element(body).perform()
        except:
            pass
    
    def login_check_and_wait(self):
        """
        检查登录状态，如果需要登录则等待用户手动登录
        """
        print("\n=== 登录检查 ===")
        print("正在检查登录状态...")
        
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                # 等待页面完全加载
                time.sleep(3)
                
                # 检查URL是否包含登录相关路径
                current_url = self.driver.current_url.lower()
                if 'login' in current_url or 'signin' in current_url:
                    print("⚠️  当前在登录页面")
                    needs_login = True
                else:
                    # 检查页面是否能正常显示评论区域
                    page_source = self.driver.page_source
                    
                    # 更准确的登录检测
                    login_indicators = [
                        "立即登录",
                        "请先登录",
                        "login-button",
                        "登录后查看",
                        "需要登录",
                        "sign-in"
                    ]
                    
                    # 检查是否存在用户信息或评论区域
                    logged_in_indicators = [
                        "用户头像",
                        "个人中心",
                        "我的",
                        "comment",
                        "评论",
                        "user-info",
                        "profile"
                    ]
                    
                    has_login_prompt = any(indicator in page_source for indicator in login_indicators)
                    has_user_content = any(indicator in page_source for indicator in logged_in_indicators)
                    
                    needs_login = has_login_prompt and not has_user_content
                
                if needs_login:
                    if attempt == 0:
                        print("⚠️  检测到需要登录")
                        print("🔧 已启用图片显示，验证码应该可以正常显示")
                        print("💡 建议使用手机号+验证码登录方式")
                        print("\n请在浏览器中完成以下步骤：")
                        print("1. 点击登录按钮")
                        print("2. 选择手机号登录")
                        print("3. 输入手机号和验证码")
                        print("4. 完成登录后，请按Enter继续...")
                        
                        # 尝试自动跳转到登录页面
                        try:
                            login_buttons = self.driver.find_elements(By.XPATH, "//*[contains(text(), '登录') or contains(text(), 'Login')]")
                            if login_buttons:
                                for button in login_buttons:
                                    if button.is_displayed() and button.is_enabled():
                                        button.click()
                                        print("已自动点击登录按钮")
                                        time.sleep(2)
                                        break
                        except:
                            pass
                        
                        input("登录完成后，请按Enter键继续...")
                    else:
                        print(f"第{attempt + 1}次检查登录状态...")
                        input("如果已登录，请按Enter继续；否则请完成登录后再按Enter...")
                    
                    # 重新检查登录状态
                    time.sleep(2)
                    current_url = self.driver.current_url.lower()
                    page_source = self.driver.page_source
                    
                    # 更宽松的登录成功检测
                    success_indicators = [
                        "个人中心",
                        "我的收藏",
                        "用户",
                        "avatar",
                        "profile",
                        not any(indicator in page_source for indicator in login_indicators)
                    ]
                    
                    if 'login' not in current_url and any(success_indicators):
                        print("✅ 登录状态验证成功")
                        return
                    elif attempt < max_attempts - 1:
                        print("⚠️  登录状态仍需确认，请再次检查...")
                    else:
                        print("⚠️  无法确认登录状态，但继续尝试爬取...")
                        return
                else:
                    print("✅ 检测到已登录状态")
                    return
                    
            except Exception as e:
                print(f"登录检查出错: {e}")
                if attempt < max_attempts - 1:
                    time.sleep(2)
                else:
                    print("跳过登录检查，继续执行...")
                    return
    
    def scroll_to_comments_section(self):
        """
        滚动到评论区域
        """
        print("正在定位评论区域...")
        
        # 尝试多种方式定位评论区
        comment_selectors = [
            '[class*="comment"]',
            '[class*="Comment"]',
            '[data-testid*="comment"]',
            '.comments-container',
            '#comments',
            'div[class*="评论"]'
        ]
        
        comment_section = None
        for selector in comment_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    comment_section = elements[0]
                    break
            except:
                continue
        
        if comment_section:
            self.driver.execute_script("arguments[0].scrollIntoView(true);", comment_section)
            time.sleep(2)
            print("已定位到评论区域")
        else:
            # 如果找不到评论区，尝试滚动到页面中部
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            print("滚动到页面中部，寻找评论区域")
    
    def load_more_comments(self, target_count=1083):
        """
        通过滚动和点击"加载更多"来获取更多评论
        """
        print(f"开始加载评论，目标数量: {target_count}")
        
        # 尝试定位评论区容器
        comment_container_selectors = [
            'div[role="dialog"] div.content-container',  # 评论弹窗内容区
            'div[class*="comment-list"]',
            'div.comment-list-container',
            'div[class*="comments-container"]',
            'div.xg-comments',
            'div[class*="feed-comment"]'
        ]
        
        # 获取滚动前所有可能容器的滚动位置
        scroll_positions = {}
        print("\n请在页面上进行以下操作:")
        print("1. 找到评论区域")
        print("2. 用鼠标滚轮在评论区域滚动一下")
        print("3. 按Enter键继续...")
        input()
        
        # 记录所有可能容器当前的滚动位置
        for selector in comment_container_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    if element.is_displayed():
                        try:
                            scroll_top = self.driver.execute_script("return arguments[0].scrollTop;", element)
                            scroll_positions[element] = scroll_top
                        except:
                            continue
            except:
                continue
        
        print("请再次在评论区域滚动一下")
        print("按Enter键继续...")
        input()
        time.sleep(1)  # 等待滚动完成
        
        # 检查哪个容器的滚动位置发生了变化
        comment_container = None
        for element, old_position in scroll_positions.items():
            try:
                new_position = self.driver.execute_script("return arguments[0].scrollTop;", element)
                if new_position != old_position:
                    if self.driver.execute_script("return arguments[0].scrollHeight > arguments[0].clientHeight;", element):
                        comment_container = element
                        print("✓ 成功找到可滚动的评论容器")
                        break
            except:
                continue
        
        if not comment_container:
            print("未检测到评论容器的滚动，尝试其他方法...")
            # 尝试查找带有滚动条的元素
            script = """
            return Array.from(document.querySelectorAll('*')).find(el => {
                let style = window.getComputedStyle(el);
                return el.scrollHeight > el.clientHeight && 
                       (style.overflowY === 'scroll' || style.overflowY === 'auto') &&
                       el.children.length > 0 &&
                       (el.className.includes('comment') || el.className.includes('Comment') ||
                        Array.from(el.children).some(child => 
                            child.className.includes('comment') || child.className.includes('Comment')
                        ))
            });
            """
            try:
                comment_container = self.driver.execute_script(script)
                if comment_container:
                    print("✓ 通过样式特征找到评论容器")
            except:
                pass
        
        if not comment_container:
            print("无法找到评论容器，将在整个页面范围内滚动")
            comment_container = self.driver.find_element(By.TAG_NAME, "body")
        
        loaded_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 100
        last_height = 0
        
        print("\n开始自动滚动加载更多评论...")
        
        while loaded_count < target_count and scroll_attempts < max_scroll_attempts:
            try:
                # 获取当前滚动位置
                current_position = self.driver.execute_script("return arguments[0].scrollTop;", comment_container)
                total_height = self.driver.execute_script("return arguments[0].scrollHeight;", comment_container)
                
                # 计算新的滚动位置 (每次滚动一屏的1/3)
                client_height = self.driver.execute_script("return arguments[0].clientHeight;", comment_container)
                scroll_amount = max(client_height // 3, 100)  # 至少滚动100像素
                new_position = min(current_position + scroll_amount, total_height)
                
                # 执行滚动
                self.driver.execute_script("arguments[0].scrollTop = arguments[1];", comment_container, new_position)
                time.sleep(random.uniform(1, 1.5))
                
                # 在最底部时尝试点击加载更多
                if new_position >= total_height - client_height:
                    button_clicked = self.click_load_more_button(comment_container)
                    if button_clicked:
                        time.sleep(random.uniform(1.5, 2))
                        scroll_attempts = 0
                        continue
                
                # 检查是否有新内容加载
                new_height = self.driver.execute_script("return arguments[0].scrollHeight;", comment_container)
                
                if new_height == last_height:
                    scroll_attempts += 1
                    if scroll_attempts > 10:
                        # 滚动到顶部再到底部，尝试触发加载
                        self.driver.execute_script("arguments[0].scrollTop = 0;", comment_container)
                        time.sleep(0.8)
                        self.driver.execute_script(
                            "arguments[0].scrollTop = arguments[0].scrollHeight;", 
                            comment_container
                        )
                        time.sleep(0.8)
                        
                        # 再次检查高度
                        final_height = self.driver.execute_script("return arguments[0].scrollHeight;", comment_container)
                        if final_height == new_height:
                            print("\n评论容器高度未变化，可能已加载完所有评论")
                            break
                else:
                    scroll_attempts = 0
                    last_height = new_height
                
                # 统计当前已加载的评论数量
                current_comments = self.count_visible_comments()
                if current_comments > loaded_count:
                    loaded_count = current_comments
                    print(f"当前已加载评论数量: {loaded_count}")
                
            except Exception as e:
                print(f"滚动过程出错: {e}")
                scroll_attempts += 1
                if scroll_attempts > 10:
                    break
                time.sleep(random.uniform(1, 2))
                continue
        
        print(f"\n评论加载完成，最终加载数量: {loaded_count}")
        
    def click_load_more_button(self, container):
        """
        在指定容器中查找并点击加载更多按钮
        """
        load_more_buttons = [
            "加载更多",
            "查看更多",
            "展开更多",
            "更多评论",
            "load more",
            "show more"
        ]
        
        for button_text in load_more_buttons:
            try:
                # 在容器内查找按钮
                buttons = container.find_elements(By.XPATH, f".//*/text()[contains(., '{button_text}')]/parent::*")
                buttons.extend(container.find_elements(By.XPATH, f".//*[contains(@class, 'load-more')]"))
                
                for button in buttons:
                    if button.is_displayed() and button.is_enabled():
                        try:
                            button.click()
                        except:
                            self.driver.execute_script("arguments[0].click();", button)
                        print(f"点击了'{button_text}'按钮")
                        time.sleep(random.uniform(1.5, 3))
                        return True
            except Exception as e:
                continue
        
        return False
    
    def count_visible_comments(self):
        """
        统计当前页面可见的评论数量
        """
        comment_selectors = [
            '[class*="comment-item"]',
            '[class*="CommentItem"]',
            '[class*="comment-content"]',
            '.comment',
            '[data-testid*="comment"]'
        ]
        
        total_count = 0
        for selector in comment_selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    total_count = max(total_count, len(elements))
            except:
                continue
        
        return total_count
    
    def extract_comments_from_page(self):
        """
        从页面中提取评论数据
        """
        print("开始提取评论数据...")
        
        # 尝试从页面的JavaScript变量中获取数据
        try:
            # 更安全的JavaScript执行方式
            script_result = None
            
            # 分步骤执行，避免复杂的JavaScript导致错误
            try:
                # 首先检查是否存在常见的数据对象
                has_initial_state = self.driver.execute_script("return typeof window.__INITIAL_STATE__ !== 'undefined';")
                if has_initial_state:
                    script_result = self.driver.execute_script("return window.__INITIAL_STATE__;")
            except:
                pass
            
            if not script_result:
                try:
                    has_apollo_state = self.driver.execute_script("return typeof window.__APOLLO_STATE__ !== 'undefined';")
                    if has_apollo_state:
                        script_result = self.driver.execute_script("return window.__APOLLO_STATE__;")
                except:
                    pass
            
            if not script_result:
                try:
                    has_next_data = self.driver.execute_script("return typeof window.__NEXT_DATA__ !== 'undefined';")
                    if has_next_data:
                        script_result = self.driver.execute_script("return window.__NEXT_DATA__;")
                except:
                    pass
            
            if script_result:
                print("从页面JavaScript数据中提取评论...")
                comments = self.parse_comments_from_js_data(script_result)
                if comments:
                    self.comments_data.extend(comments)
                    print(f"从JavaScript数据中提取到 {len(comments)} 条评论")
                    return
                  
        except Exception as e:
            print(f"从JavaScript数据提取失败: {e}")
        
        # 如果JavaScript方法失败，尝试DOM解析
        self.extract_comments_from_dom()
    
    def parse_comments_from_js_data(self, data):
        """
        从JavaScript数据中解析评论
        """
        comments = []
        
        def find_comments_recursive(obj, depth=0):
            if depth > 10:  # 防止无限递归
                return
            
            if isinstance(obj, dict):
                # 查找评论相关的键
                comment_keys = ['comments', 'comment', 'commentList', 'data']
                for key in comment_keys:
                    if key in obj and isinstance(obj[key], (list, dict)):
                        if isinstance(obj[key], list):
                            for item in obj[key]:
                                comment = self.parse_single_comment_from_js(item)
                                if comment:
                                    comments.append(comment)
                        else:
                            find_comments_recursive(obj[key], depth + 1)
                
                # 递归搜索所有值
                for value in obj.values():
                    if isinstance(value, (dict, list)):
                        find_comments_recursive(value, depth + 1)
            
            elif isinstance(obj, list):
                for item in obj:
                    find_comments_recursive(item, depth + 1)
        
        find_comments_recursive(data)
        return comments
    
    def parse_single_comment_from_js(self, comment_data):
        """
        解析单条评论数据
        """
        if not isinstance(comment_data, dict):
            return None
        
        # 尝试提取评论内容
        content_keys = ['content', 'text', 'comment', 'message', 'body']
        content = ""
        for key in content_keys:
            if key in comment_data and comment_data[key]:
                content = str(comment_data[key])
                break
        
        if not content:
            return None
        
        # 提取用户信息
        user_info = comment_data.get('user', comment_data.get('userInfo', comment_data.get('author', {})))
        
        comment_info = {
            'comment_id': comment_data.get('id', comment_data.get('commentId', '')),
            'content': content,
            'create_time': comment_data.get('createTime', comment_data.get('time', comment_data.get('timestamp', ''))),
            'like_count': comment_data.get('likeCount', comment_data.get('likes', 0)),
            'level': 1,  # 默认为一级评论
            'parent_id': comment_data.get('parentId', ''),
            'user_id': user_info.get('id', user_info.get('userId', '')),
            'nickname': user_info.get('nickname', user_info.get('name', user_info.get('username', ''))),
            'avatar': user_info.get('avatar', user_info.get('profileImage', '')),
            'ip_location': comment_data.get('ipLocation', comment_data.get('location', '')),
            'sub_comment_count': len(comment_data.get('replies', comment_data.get('subComments', []))),
            'at_users': ''
        }
        
        return comment_info
    
    def extract_comments_from_dom(self):
        """
        从DOM中提取评论数据（备用方案）
        """
        print("使用DOM解析方式提取评论...")
        
        # 更精确的评论选择器
        selectors = [
            # 小红书常见的评论类名
            '[class*="comment-item"]',
            '[class*="CommentItem"]', 
            '[class*="comment-content"]',
            '[class*="note-comment"]',
            '[class*="feeds-comment"]',
            # 通用评论选择器
            '.comment',
            '[data-testid*="comment"]',
            # 包含文本内容的div
            'div[class*="content"]:not([class*="note-content"]):not([class*="image"])',
            # 小红书特定选择器
            '[class*="interaction"]',
            '[class*="user-comment"]'
        ]
        
        all_comment_elements = []
        for selector in selectors:
            try:
                elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    all_comment_elements.extend(elements)
                    print(f"选择器 '{selector}' 找到 {len(elements)} 个元素")
            except Exception as e:
                continue
        
        if not all_comment_elements:
            print("未找到评论元素，尝试其他方法...")
            # 尝试通过文本内容查找评论
            try:
                # 查找包含常见评论特征的元素
                text_elements = self.driver.find_elements(By.XPATH, "//div[string-length(text()) > 5 and string-length(text()) < 1000]")
                print(f"通过文本长度找到 {len(text_elements)} 个可能的评论元素")
                all_comment_elements.extend(text_elements)
            except:
                pass
        
        print(f"总共找到 {len(all_comment_elements)} 个可能的评论元素")
        
        if not all_comment_elements:
            print("❌ 未找到任何评论元素")
            return
        
        # 去重和过滤
        unique_elements = []
        seen_texts = set()
        
        for element in all_comment_elements:
            try:
                text = element.text.strip()
                # 过滤条件
                if (text and 
                    text not in seen_texts and 
                    len(text) > 3 and  # 最短3个字符
                    len(text) < 2000 and  # 最长2000字符
                    not text.startswith('http') and  # 排除链接
                    '评论' not in text[:10] and  # 排除"评论"标题
                    '回复' not in text[:10] and  # 排除"回复"按钮
                    '点赞' not in text[:10] and  # 排除"点赞"按钮
                    not text.isdigit()):  # 排除纯数字
                    
                    seen_texts.add(text)
                    unique_elements.append(element)
            except Exception as e:
                continue
        
        print(f"去重和过滤后有 {len(unique_elements)} 个有效评论元素")
        
        # 解析评论
        for i, element in enumerate(unique_elements):
            try:
                comment_data = self.parse_comment_element(element, i)
                if comment_data and comment_data['content']:
                    self.comments_data.append(comment_data)
            except Exception as e:
                print(f"解析第{i+1}个评论时出错: {e}")
                continue
        
        print(f"✅ 成功解析 {len(self.comments_data)} 条评论")
    
    def parse_comment_element(self, element, index):
        """
        解析单个评论元素
        """
        try:
            # 获取评论文本
            content = element.text.strip()
            if not content:
                return None
            
            # 尝试获取更详细的信息
            comment_data = {
                'comment_id': f"dom_{index}_{int(time.time())}_{hash(content) % 10000}",
                'content': content,
                'create_time': '',
                'like_count': 0,
                'level': 1,
                'parent_id': '',
                'user_id': '',
                'nickname': '',
                'avatar': '',
                'ip_location': '',
                'sub_comment_count': 0,
                'at_users': ''
            }
            
            # 智能解析用户名和评论内容
            lines = content.split('\n')
            cleaned_lines = [line.strip() for line in lines if line.strip()]
            
            if len(cleaned_lines) >= 2:
                # 第一行通常是用户名或包含用户名
                first_line = cleaned_lines[0]
                
                # 如果第一行看起来像用户名（短且不包含标点符号过多）
                if (len(first_line) <= 30 and 
                    first_line.count('。') + first_line.count('！') + first_line.count('？') < 2):
                    comment_data['nickname'] = first_line
                    comment_data['content'] = '\n'.join(cleaned_lines[1:])
                else:
                    # 尝试从行中提取用户名模式
                    for line in cleaned_lines[:3]:  # 只检查前3行
                        # 寻找类似 "用户名：" 或 "用户名 说：" 的模式
                        if '：' in line or ':' in line:
                            parts = re.split('[：:]', line, 1)
                            if len(parts) == 2 and len(parts[0].strip()) <= 20:
                                comment_data['nickname'] = parts[0].strip()
                                remaining_content = parts[1].strip()
                                if remaining_content:
                                    # 将剩余内容和后续行合并
                                    remaining_lines = [remaining_content]
                                    line_index = cleaned_lines.index(line)
                                    remaining_lines.extend(cleaned_lines[line_index + 1:])
                                    comment_data['content'] = '\n'.join(remaining_lines)
                                break
            
            # 提取点赞数
            like_patterns = [
                r'(\d+)\s*赞',
                r'点赞\s*(\d+)',
                r'❤️\s*(\d+)',
                r'👍\s*(\d+)',
                r'(\d+)\s*点赞'
            ]
            
            for pattern in like_patterns:
                match = re.search(pattern, content)
                if match:
                    try:
                        comment_data['like_count'] = int(match.group(1))
                        # 从内容中移除点赞信息
                        comment_data['content'] = re.sub(pattern, '', comment_data['content']).strip()
                        break
                    except:
                        pass
            
            # 提取时间信息
            time_patterns = [
                r'(\d+)天前',
                r'(\d+)小时前',
                r'(\d+)分钟前',
                r'(\d{4}-\d{2}-\d{2})',
                r'(\d{2}-\d{2})',
                r'昨天',
                r'前天'
            ]
            
            for pattern in time_patterns:
                match = re.search(pattern, content)
                if match:
                    comment_data['create_time'] = match.group(0)
                    # 从内容中移除时间信息
                    comment_data['content'] = re.sub(pattern, '', comment_data['content']).strip()
                    break
            
            # 提取地理位置
            location_patterns = [
                r'(\w+省)',
                r'(\w+市)',
                r'(北京|上海|天津|重庆)',
                r'(\w+\d+天前\w+)',  # 可能的地理位置格式
            ]
            
            for pattern in location_patterns:
                match = re.search(pattern, content)
                if match:
                    comment_data['ip_location'] = match.group(1)
                    break
            
            # 清理内容
            comment_data['content'] = re.sub(r'\s+', ' ', comment_data['content']).strip()
            
            # 最终验证
            if not comment_data['content'] or len(comment_data['content']) < 2:
                return None
                
            return comment_data
            
        except Exception as e:
            print(f"解析评论元素出错: {e}")
            return None
    
    def get_comments(self, url, target_count=1083):
        """
        主要的评论获取方法
        """
        try:
            print(f"正在访问页面: {url}")
            self.driver.get(url)
            
            # 等待页面加载
            if not self.wait_for_page_load():
                print("页面加载失败")
                return []
            
            # 检查登录状态
            self.login_check_and_wait()
            
            # 滚动到评论区
            self.scroll_to_comments_section()
            
            # 加载更多评论
            self.load_more_comments(target_count)
            
            # 提取评论数据
            self.extract_comments_from_page()
            
            return self.comments_data
            
        except Exception as e:
            print(f"获取评论时出错: {e}")
            return []
    
    def save_to_excel(self, filename="xiaohongshu_comments_selenium.xlsx"):
        """
        保存数据到Excel文件
        """
        if not self.comments_data:
            print("没有数据可保存")
            return
        
        df = pd.DataFrame(self.comments_data)
        
        # 重新排列列的顺序
        columns_order = [
            'comment_id', 'content', 'level', 'parent_id', 
            'user_id', 'nickname', 'create_time', 'like_count',
            'ip_location', 'at_users', 'sub_comment_count', 'avatar'
        ]
        
        # 确保所有列都存在
        for col in columns_order:
            if col not in df.columns:
                df[col] = ''
        
        df = df[columns_order]
        
        # 保存到Excel
        df.to_excel(filename, index=False, engine='openpyxl')
        print(f"数据已保存到 {filename}")
        
        # 打印统计信息
        level_1_count = len(df[df['level'] == 1])
        level_2_count = len(df[df['level'] == 2])
        print(f"一级评论: {level_1_count} 条")
        print(f"二级评论: {level_2_count} 条")
        print(f"总计: {len(df)} 条")
        
        # 显示部分数据预览
        print("\n数据预览:")
        print(df[['nickname', 'content', 'like_count']].head())
    
    def close(self):
        """
        关闭浏览器
        """
        if hasattr(self, 'driver'):
            self.driver.quit()
            print("浏览器已关闭")

def main():
    """
    主函数
    """
    print("=== 小红书评论爬虫 (Selenium + Edge版本) ===")
    print("此版本使用Microsoft Edge浏览器自动化技术，可以更好地应对反爬虫措施")
    
    # 输入参数
    url = input("请输入小红书笔记URL: ").strip()
    
    # 询问是否使用无头模式
    headless_choice = input("是否使用无头模式？(y/n，建议选择n以便观察和手动登录): ").strip().lower()
    headless = headless_choice == 'y'
    
    # 目标评论数量
    try:
        target_count = int(input("请输入目标评论数量 (默认1083): ").strip() or "1083")
    except ValueError:
        target_count = 1083
    
    crawler = None
    try:
        # 初始化爬虫
        crawler = XiaohongshuSeleniumCrawler(headless=headless)
        
        # 获取评论
        print(f"\n开始爬取评论，目标数量: {target_count}")
        comments = crawler.get_comments(url, target_count)
        
        if comments:
            # 保存到Excel
            note_id = crawler.extract_note_id(url)
            filename = f"xiaohongshu_comments_{note_id}_{int(time.time())}.xlsx"
            crawler.save_to_excel(filename)
            print(f"\n✅ 爬取完成！共获取 {len(comments)} 条评论")
        else:
            print("\n❌ 未获取到评论数据")
            
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
    finally:
        if crawler:
            input("\n按Enter键关闭浏览器...")
            crawler.close()

if __name__ == "__main__":
    main()