import time
import os
import json
from selenium.webdriver.common.by import By

class ActionRecorder:
    def __init__(self, driver):
        self.driver = driver
        self.actions = []
        self.is_recording = False
        self.stop_background_thread = False
        self.last_url = self.driver.current_url
        self.page_elements = {}
        self.page_count = 0
        self._is_finished = False

    def start_recording(self):
        """開始記錄用戶行為"""
        self.is_recording = True
        print("開始記錄用戶行為...")
        
        # 注入所有必要的JS
        self.inject_all_scripts()
        
        # 設置定期檢查結果的計時器
        self._start_monitoring()

    def stop_recording(self):
        """停止記錄用戶行為"""
        self.stop_background_thread = True
        self.is_recording = False
        print("停止記錄用戶行為")
        
        # 確保停止監控線程
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            try:
                self.monitor_thread.join(timeout=2.0)
            except:
                pass

    def inject_all_scripts(self):
        """注入所有需要的JS腳本"""
        # 首先注入 userBehaviour.js
        self.inject_user_behaviour_js()
        
        # 然後注入阻止新分頁腳本
        self.inject_prevent_new_tabs_js()
        
        # 添加其他必要的JS腳本注入...
        self.setup_navigation_monitoring()

    def inject_js_file(self, js_filename):
        """通用方法：注入指定的JS文件"""
        try:
            print(f"注入 {js_filename}...")
            
            # 讀取JS文件
            js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), js_filename)
            with open(js_path, "r", encoding="utf-8") as f:
                js_code = f.read()
            
            # 使用script元素方法注入
            self.driver.execute_script(f"""
                try {{
                    var script = document.createElement('script');
                    script.textContent = `{js_code.replace('`', '\\`')}`;
                    document.head.appendChild(script);
                    console.log('{js_filename} injection completed');
                }} catch (e) {{
                    console.error('Error in {js_filename} injection:', e);
                    throw e;
                }}
            """)
            
            print(f"{js_filename} 注入成功")
            return True
        except Exception as e:
            print(f"注入 {js_filename} 時發生錯誤: {e}")
            return False

    def inject_prevent_new_tabs_js(self):
        """注入阻止新分頁開啟的JS腳本"""
        success = self.inject_js_file("prevent_new_tabs.js")
        
        # 額外處理框架
        if success:
            try:
                self.driver.execute_script("""
                try {
                    // 處理所有的 iframe
                    var iframes = document.getElementsByTagName('iframe');
                    for (var i = 0; i < iframes.length; i++) {
                        try {
                            var iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                            
                            // 在 iframe 中執行相同腳本
                            var scriptContent = document.querySelector('script[src*="prevent_new_tabs.js"]')?.textContent;
                            if (scriptContent) {
                                var script = iframeDoc.createElement('script');
                                script.textContent = scriptContent;
                                iframeDoc.body.appendChild(script);
                            }
                        } catch (e) {
                            console.log("無法訪問 iframe:", e);
                        }
                    }
                } catch (e) {
                    console.log("iframe 處理錯誤:", e);
                }
                """)
            except Exception as e:
                print(f"處理iframe時發生錯誤: {e}")

    def inject_user_behaviour_js(self):
        """注入 userBehaviour.js 到頁面中"""
        if self.inject_js_file("userBehaviour.js"):
            # 驗證腳本是否成功注入
            is_defined = self.driver.execute_script("return typeof userBehaviour !== 'undefined';")
            if is_defined:
                # 配置 userBehaviour
                self.driver.execute_script("""
                    try {
                        // 設置錯誤捕獲
                        window.jsErrors = window.jsErrors || [];
                        window.addEventListener('error', function(e) {
                            console.error('JS error captured:', e.error);
                            window.jsErrors.push({
                                message: e.message,
                                source: e.filename,
                                line: e.lineno,
                                stack: e.error ? e.error.stack : null
                            });
                        });
                        
                        // 配置 userBehaviour
                        userBehaviour.config({
                            processTime: 2,  // 每2秒處理一次數據
                            processData: function(results) {
                                // 將結果存儲在全局變量中以便 Python 訪問
                                window.lastResults = results;
                                console.log("User behaviour data processed");
                            }
                        });
                        
                        // 開始跟踪
                        userBehaviour.start();
                        console.log("User behaviour tracking started on page " + window.location.href);
                    } catch(e) {
                        console.error("Error configuring userBehaviour:", e);
                    }
                """)
                
                # 檢查可用方法
                props = self.driver.execute_script("""
                    var props = [];
                    for (var prop in userBehaviour) {
                        props.push(prop);
                    }
                    return props;
                """)
                print(f"userBehaviour 可用方法: {props}")
                
                # 檢查 localStorage 中是否已有數據
                has_data = self.driver.execute_script("""
                    try {
                        return localStorage.getItem('userBehaviourData') !== null;
                    } catch(e) {
                        return false;
                    }
                """)
                
                if has_data:
                    print("在 localStorage 中找到現有的用戶行為數據")
                else:
                    print("localStorage 中沒有找到現有數據")
            else:
                print("警告: 注入後 userBehaviour 對象未定義")
    
    def setup_navigation_monitoring(self):
        """設置導航監聽器以便在頁面變化時重新注入"""
        self.driver.execute_script("""
            if (!window._navigationMonitorSet) {
                window._navigationMonitorSet = true;
                window._lastUrl = location.href;
                
                // 定期檢查URL是否變化
                setInterval(function() {
                    if (window._lastUrl !== location.href) {
                        console.log('Navigation detected from ' + window._lastUrl + ' to ' + location.href);
                        window._lastUrl = location.href;
                        
                        // 觸發自定義事件，Python可以監聽
                        var event = new CustomEvent('urlChanged', {detail: {url: location.href}});
                        document.dispatchEvent(event);
                        
                        // 保存注入狀態供檢查
                        window._needReinjection = true;
                    }
                }, 1000);
            }
            
            window._checkForNavigation = function() {
                return window._needReinjection === true;
            };
            
            window._resetNavigationFlag = function() {
                window._needReinjection = false;
            };
            
            // 更可靠的頁面變化偵測
            window.scheminMonitorPageChanges = function() {
                // 檢查 URL 變化
                if (window.location.href !== window._lastUrl) {
                    console.log('偵測到 URL 變化: ' + window._lastUrl + ' -> ' + window.location.href);
                    window._lastUrl = window.location.href;
                    window._needReinjection = true;
                }
                
                // 仍需保留這個監控函數運行
                setTimeout(window.scheminMonitorPageChanges, 300);
            };
            
            // 註冊頁面事件監聽器
            window.addEventListener('popstate', function() {
                console.log('偵測到 popstate 事件');
                window._needReinjection = true;
            });
            
            window.addEventListener('hashchange', function() {
                console.log('偵測到 hashchange 事件');
                window._needReinjection = true;
            });
            
            // 攔截 history API
            var originalPushState = history.pushState;
            history.pushState = function() {
                var result = originalPushState.apply(this, arguments);
                console.log('偵測到 pushState 調用');
                window._needReinjection = true;
                return result;
            };
            
            var originalReplaceState = history.replaceState;
            history.replaceState = function() {
                var result = originalReplaceState.apply(this, arguments);
                console.log('偵測到 replaceState 調用');
                window._needReinjection = true;
                return result;
            };
            
            // 啟動監控
            window.scheminMonitorPageChanges();
        """)

    def check_and_reinject(self):
        """檢查是否需要重新注入JS"""
        try:
            needs_injection = self.driver.execute_script("return window._checkForNavigation ? window._checkForNavigation() : true;")
            current_url = self.driver.current_url
            
            # 如果URL變化或需要重新注入標記為true
            if needs_injection or current_url != self.last_url:
                if current_url != self.last_url:
                    print(f"檢測到URL變化: {self.last_url} -> {current_url}")
                else:
                    print("檢測到需要重新注入標記")
                
                self.page_count += 1
                
                # 重新注入所有JS - 會從localStorage加載之前的數據
                self.inject_all_scripts()
                self.driver.execute_script("if (window._resetNavigationFlag) window._resetNavigationFlag();")
                self.last_url = current_url
                return True
            return False
        except Exception as e:
            print(f"檢查導航時發生錯誤: {e}")
            return True  # 出錯時假設需要重新注入

    def _start_monitoring(self):
        """啟動監控線程來定期檢索用戶行為數據"""
        import threading
        self.monitor_thread = threading.Thread(target=self._monitor_background_events, daemon=True)
        self.monitor_thread.start()

    def _monitor_background_events(self):
        """監控背景事件，從 userBehaviour.js 獲取行為數據"""
        check_interval = 1.0  # 每秒檢查一次
        
        while not self.stop_background_thread:
            time.sleep(check_interval)
            
            if not self.is_recording:
                continue
                
            try:
                # 檢查頁面導航並重新注入
                self.check_and_reinject()
                
                # 獲取 userBehaviour 處理的結果
                try:
                    # 強制處理結果
                    self.driver.execute_script("userBehaviour.processResults();")
                    
                    # 從 localStorage 獲取結果
                    results_json = self.driver.execute_script("""
                        try {
                            // 從 localStorage 獲取數據
                            var data = localStorage.getItem('userBehaviourData');
                            if (data) {
                                return data;  // 直接返回 JSON 字符串
                            } else {
                                // 如果沒有，嘗試從 window.lastResults 獲取
                                return JSON.stringify(window.lastResults || {});
                            }
                        } catch(e) {
                            console.error("Error getting results from localStorage:", e);
                            return JSON.stringify({error: e.toString()});
                        }
                    """)
                    
                    if results_json:
                        current_results = json.loads(results_json)
                        
                        # 處理點擊事件
                        self._process_click_events(current_results)
                        
                        # 處理鍵盤事件
                        self._process_keyboard_events(current_results)
                        
                        # 處理滾動事件
                        self._process_scroll_events(current_results)
                        
                        # 處理導航事件
                        self._process_navigation_events(current_results)
                except Exception as e:
                    print(f"處理 userBehaviour 結果時出錯: {e}")
                
                # 檢查結束標誌
                try:
                    end_clicked = self.driver.execute_script("return window.scheminEndRecordingClicked === true;")
                    if end_clicked:
                        print("檢測到結束按鈕點擊")
                        self._is_finished = True
                        break
                except:
                    pass
                    
            except Exception as e:
                print(f"監控背景事件時出錯: {e}")
                
            # 短暫休息以避免過度占用 CPU
            time.sleep(0.2)

    def _process_click_events(self, results):
        """處理點擊事件"""
        if 'clicks' not in results or 'clickDetails' not in results['clicks']:
            return
        
        # 獲取新的點擊事件 (與已處理事件數量比較)
        click_count = results['clicks']['clickCount']
        click_details = results['clicks']['clickDetails']
        
        # 記錄已處理的點擊數量
        processed_clicks = getattr(self, '_processed_clicks', 0)
        
        # 如果有新點擊
        if click_count > processed_clicks and len(click_details) > processed_clicks:
            # 處理新點擊
            for i in range(processed_clicks, len(click_details)):
                if i < len(click_details):
                    click = click_details[i]
                    
                    # 解析點擊數據
                    position = click[0] if len(click) > 0 else "未知位置"
                    element_path = click[1] if len(click) > 1 else ""
                    timestamp = click[2] if len(click) > 2 else time.time() * 1000
                    
                    # 轉換為時間戳
                    timestamp_sec = timestamp / 1000 if timestamp > 1000000 else timestamp
                    
                    # 使用元素路徑作為描述
                    description = element_path if element_path else "元素"
                    
                    # 記錄點擊動作
                    self.actions.append({
                        "type": "Click",
                        "target": description,
                        "element_text": description,
                        "timestamp": timestamp_sec
                    })
            
            # 更新已處理點擊數量
            self._processed_clicks = len(click_details)

    def _process_keyboard_events(self, results):
        """處理鍵盤事件"""
        if 'keyboardActivities' not in results:
            return
        
        # 獲取鍵盤事件
        keyboard_activities = results['keyboardActivities']
        
        # 記錄已處理的鍵盤事件數量
        processed_keyboard = getattr(self, '_processed_keyboard', 0)
        
        # 如果有新的鍵盤事件
        if len(keyboard_activities) > processed_keyboard:
            # 處理新的鍵盤事件
            for i in range(processed_keyboard, len(keyboard_activities)):
                if i < len(keyboard_activities):
                    key_event = keyboard_activities[i]
                    
                    # 解析鍵盤事件數據
                    input_data = key_event[0] if len(key_event) > 0 else "未知輸入"
                    timestamp = key_event[1] if len(key_event) > 1 else time.time() * 1000
                    
                    # 分割類型和值
                    parts = input_data.split(":", 1)
                    input_type = parts[0] if len(parts) > 0 else "text"
                    input_value = parts[1] if len(parts) > 1 else input_data
                    
                    # 轉換為時間戳
                    timestamp_sec = timestamp / 1000 if timestamp > 1000000 else timestamp
                    
                    # 記錄輸入動作
                    self.actions.append({
                        "type": "Type",
                        "target": f"{input_type} 輸入",
                        "element_text": f"{input_type} 輸入: {input_value}",
                        "value": input_value,
                        "timestamp": timestamp_sec
                    })
            
            # 更新已處理鍵盤事件數量
            self._processed_keyboard = len(keyboard_activities)

    def _process_scroll_events(self, results):
        """處理滾動事件"""
        if 'mouseScroll' not in results:
            return
        
        # 獲取滾動事件
        scroll_events = results['mouseScroll']
        
        # 記錄已處理的滾動事件數量
        processed_scroll = getattr(self, '_processed_scroll', 0)
        
        # 如果有新的滾動事件
        if len(scroll_events) > processed_scroll:
            # 處理新的滾動事件
            for i in range(processed_scroll, len(scroll_events)):
                if i < len(scroll_events):
                    scroll = scroll_events[i]
                    
                    # 解析滾動事件數據
                    position = scroll[0] if len(scroll) > 0 else "未知位置"
                    timestamp = scroll[1] if len(scroll) > 1 else time.time() * 1000
                    
                    # 轉換為時間戳
                    timestamp_sec = timestamp / 1000 if timestamp > 1000000 else timestamp
                    
                    # 解析方向
                    direction = "未知"
                    if "(" in position and "," in position and ")" in position:
                        try:
                            coords = position.replace("(", "").replace(")", "").split(",")
                            if len(coords) == 2:
                                x = int(coords[0])
                                y = int(coords[1])
                                direction = "下" if y > 0 else "上" if y < 0 else "水平"
                        except:
                            pass
                    
                    # 記錄滾動動作
                    self.actions.append({
                        "type": "Scroll",
                        "direction": direction,
                        "element_text": f"向{direction}滾動到 {position}",
                        "timestamp": timestamp_sec
                    })
            
            # 更新已處理滾動事件數量
            self._processed_scroll = len(scroll_events)

    def _process_navigation_events(self, results):
        """處理導航事件"""
        if 'navigationHistory' not in results:
            return
        
        # 獲取導航事件
        navigation_events = results['navigationHistory']
        
        # 記錄已處理的導航事件數量
        processed_navigation = getattr(self, '_processed_navigation', 0)
        
        # 如果有新的導航事件
        if len(navigation_events) > processed_navigation:
            # 處理新的導航事件
            for i in range(processed_navigation, len(navigation_events)):
                if i < len(navigation_events):
                    nav = navigation_events[i]
                    
                    # 解析導航事件數據
                    url = nav[0] if len(nav) > 0 else "未知URL"
                    timestamp = nav[1] if len(nav) > 1 else time.time() * 1000
                    
                    # 轉換為時間戳
                    timestamp_sec = timestamp / 1000 if timestamp > 1000000 else timestamp
                    
                    # 取得頁面標題
                    try:
                        page_title = self.driver.title
                    except:
                        page_title = "未知標題"
                    
                    # 判斷是否為返回操作
                    is_back = False
                    try:
                        # 檢查瀏覽器歷史記錄和後退數據
                        is_back = self.driver.execute_script("""
                            try {
                                return window.scheminBackData && window.scheminBackData.hasGoback;
                            } catch(e) {
                                return false;
                            }
                        """)
                    except:
                        pass
                    
                    # 記錄導航/返回動作
                    if is_back:
                        self.actions.append({
                            "type": "Goback",
                            "to": url,
                            "to_title": page_title,
                            "element_text": f"返回至 {page_title}",
                            "timestamp": timestamp_sec
                        })
                    else:
                        self.actions.append({
                            "type": "Navigate",
                            "to": url,
                            "to_title": page_title,
                            "element_text": f"導航至 {url}",
                            "timestamp": timestamp_sec
                        })
            
            # 更新已處理導航事件數量
            self._processed_navigation = len(navigation_events)

    def record_page_elements(self, page_url, page_title, elements_data):
        """記錄頁面上的互動元素"""
        timestamp = time.time()
        self.page_elements[page_url] = {
            "title": page_title,
            "timestamp": timestamp,
            "elements": elements_data
        }
        
        # 同時將頁面元素記錄添加到操作記錄中
        self.actions.append({
            "type": "PageElements",
            "url": page_url,
            "title": page_title,
            "elements_count": len(elements_data),
            "timestamp": timestamp
        })
    
    def get_page_elements(self):
        """獲取頁面元素記錄"""
        return self.page_elements

    def get_actions(self):
        """獲取記錄的操作，並標準化為五種類型"""
        # 過濾並標準化動作
        standard_actions = []
        
        for action in self.actions:
            action_type = action.get("type", "")
            
            # 標準化類型
            if action_type.lower() in ["click", "mousedown", "mouseup"]:
                action["type"] = "Click"
                standard_actions.append(action)
            elif action_type.lower() in ["type", "input", "change"]:
                action["type"] = "Type"
                standard_actions.append(action)
            elif action_type.lower() in ["scroll"]:
                action["type"] = "Scroll"
                standard_actions.append(action)
            elif action_type.lower() in ["goback", "back"]:
                action["type"] = "Goback"
                standard_actions.append(action)
            elif action_type.lower() in ["navigate"]:
                action["type"] = "Navigate"
                standard_actions.append(action)
            # 忽略其他類型的操作如 PageElements
        
        return standard_actions
    
    def is_finished(self):
        """檢查錄製是否已完成"""
        return self._is_finished
