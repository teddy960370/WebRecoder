import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.events import EventFiringWebDriver, AbstractEventListener

class ActionListener(AbstractEventListener):
    def __init__(self):
        self.actions = []
        self._is_finished = False
    
    def before_click(self, element, driver):
        # 嘗試獲取元素的各種識別屬性，更全面搜集元素描述
        try:
            element_text = element.text.strip() if element.text else None
            element_id = element.get_attribute("id") if element.get_attribute("id") else None
            element_name = element.get_attribute("name") if element.get_attribute("name") else None
            element_class = element.get_attribute("class") if element.get_attribute("class") else None
            element_aria_label = element.get_attribute("aria-label") if element.get_attribute("aria-label") else None
            element_title = element.get_attribute("title") if element.get_attribute("title") else None
            element_alt = element.get_attribute("alt") if element.get_attribute("alt") else None
            element_placeholder = element.get_attribute("placeholder") if element.get_attribute("placeholder") else None
            element_value = element.get_attribute("value") if element.get_attribute("value") else None
            element_type = element.tag_name if hasattr(element, 'tag_name') else None
            
            # 獲取元素的內部文本，包括子元素的文本
            try:
                inner_text = driver.execute_script("""
                    var text = arguments[0].textContent || arguments[0].innerText;
                    return text ? text.trim() : '';
                """, element)
                if not element_text and inner_text:
                    element_text = inner_text
            except:
                pass
            
            # 嘗試獲取圖片或圖標的描述
            if element_type == 'img' or 'icon' in str(element_class).lower():
                # 優先使用 alt 或 title 作為描述
                icon_desc = element_alt or element_title
                if icon_desc:
                    element_text = f"圖標: {icon_desc}"
            
            # 確定元素的描述 (優先順序調整)
            primary_desc = element_text or element_aria_label or element_title or element_alt or element_value or element_placeholder
            secondary_desc = element_id or element_name
            
            description = primary_desc or secondary_desc
            
            if not description:
                # 如果仍然沒有描述，嘗試從類名中提取有意義的部分
                if element_class:
                    class_parts = element_class.split()
                    meaningful_classes = [c for c in class_parts if len(c) > 3 and not c.startswith('_')]
                    if meaningful_classes:
                        description = f"類: {' '.join(meaningful_classes)}"
                    else:
                        description = f"類: {element_class}"
                else:
                    description = f"元素: {element_type or '未知'}"
            
            # 儲存元素的完整詳細信息
            element_details = {
                "text": element_text,
                "id": element_id,
                "name": element_name,
                "class": element_class,
                "type": element_type,
                "aria_label": element_aria_label,
                "title": element_title,
                "alt": element_alt,
                "value": element_value,
                "placeholder": element_placeholder
            }
            
            # 過濾掉 None 值，只保留有實際值的屬性
            element_details = {k: v for k, v in element_details.items() if v}
            
            # 檢查是否為浮動按鈕的點擊
            if element_id == "schemind-end-recording-button":
                self._is_finished = True
                # 不記錄結束按鈕的點擊
                return
                
            # 記錄動作 (增強版)
            action = {
                "type": "Click",
                "target": description,
                "element_text": description,  # 新增: 確保保存元素文本描述供最終輸出使用
                "element_details": element_details,
                "timestamp": time.time()
            }
            
            self.actions.append(action)
            
        except Exception as e:
            # 如果獲取元素描述時出錯，記錄基本信息
            self.actions.append({
                "type": "Click",
                "target": "未能識別的元素",
                "element_text": "未能識別的元素",
                "error": str(e),
                "timestamp": time.time()
            })

    def before_change_value_of(self, element, driver):
        # 記錄輸入動作的起始，改進以捕獲更多資訊
        self.current_element = element
        self.input_start_time = time.time()
        
        # 嘗試獲取元素的更多資訊
        try:
            self.element_id = element.get_attribute("id")
            self.element_name = element.get_attribute("name")
            self.element_placeholder = element.get_attribute("placeholder")
            self.element_aria_label = element.get_attribute("aria-label")
            self.element_class = element.get_attribute("class")
            self.element_tag_name = element.tag_name
            self.element_type = element.get_attribute("type")
            self.original_value = element.get_attribute("value") or ""
        except:
            pass
    
    def after_change_value_of(self, element, driver):
        try:
            # 獲取元素標識，更全面搜集元素描述
            element_id = element.get_attribute("id") if element.get_attribute("id") else None
            element_name = element.get_attribute("name") if element.get_attribute("name") else None
            element_placeholder = element.get_attribute("placeholder") if element.get_attribute("placeholder") else None
            element_aria_label = element.get_attribute("aria-label") if element.get_attribute("aria-label") else None
            element_class = element.get_attribute("class") if element.get_attribute("class") else None
            element_type = element.get_attribute("type") if element.get_attribute("type") else None
            element_tag_name = element.tag_name if hasattr(element, 'tag_name') else None
            
            # 獲取元素描述
            primary_desc = element_placeholder or element_aria_label or element_name
            secondary_desc = element_id or element_class
            
            # 嘗試根據元素類型提供更具描述性的名稱
            element_type_desc = ""
            if element_tag_name == "input":
                if element_type == "text":
                    element_type_desc = "文字輸入框"
                elif element_type == "password":
                    element_type_desc = "密碼輸入框"
                elif element_type == "email":
                    element_type_desc = "電子郵件輸入框"
                elif element_type == "search":
                    element_type_desc = "搜尋框"
                else:
                    element_type_desc = f"{element_type}輸入框"
            elif element_tag_name == "textarea":
                element_type_desc = "文字區域"
            
            description = primary_desc or secondary_desc or element_type_desc or "輸入框"
            
            # 獲取輸入內容
            current_value = element.get_attribute("value") or ""
            
            # 確認值確實已變更
            original_value = getattr(self, 'original_value', "")
            if current_value == original_value:
                return
            
            # 元素詳細資訊
            element_details = {
                "id": element_id,
                "name": element_name,
                "placeholder": element_placeholder,
                "aria_label": element_aria_label,
                "class": element_class,
                "type": element_type,
                "tag": element_tag_name
            }
            
            # 過濾掉 None 值
            element_details = {k: v for k, v in element_details.items() if v}
            
            # 記錄動作 (增強版)
            action = {
                "type": "Type",
                "target": description,
                "element_text": f"{description}: {current_value}",  # 新增: 格式化文本描述包含輸入值
                "value": current_value,
                "element_details": element_details,
                "timestamp": self.input_start_time
            }
            self.actions.append(action)
            
        except Exception as e:
            # 如果獲取元素描述時出錯，記錄基本信息
            self.actions.append({
                "type": "Type",
                "target": "未能識別的輸入框",
                "element_text": "未能識別的輸入框",
                "value": element.get_attribute("value") or "",
                "error": str(e),
                "timestamp": self.input_start_time
            })
        
    def is_finished(self):
        return self._is_finished

class ActionRecorder:
    def __init__(self, driver):
        self.driver = driver
        self.listener = ActionListener()
        self.event_driver = EventFiringWebDriver(driver, self.listener)
        self.is_recording = False
        self.background_thread = None
        self.stop_background_thread = False
        self.last_url = self.event_driver.current_url  # 使用 event_driver 來取得當前 URL
        self.page_elements = {}
        
        # 將原始 driver 的參考替換為 event_driver，確保事件被捕獲
        driver.execute_script("window.originalDriver = window.driver;")
    
    def start_recording(self):
        self.is_recording = True
        # 啟動滑鼠和鍵盤事件監聽
        self._inject_event_listeners()
        # 啟動一個監聽線程來處理滾動和後退操作
        self._start_monitoring()
    
    def stop_recording(self):
        self.stop_background_thread = True
        self.is_recording = False
        # 確保停止監控線程
        if hasattr(self, 'monitor_thread') and self.monitor_thread.is_alive():
            try:
                self.monitor_thread.join(timeout=2.0)
            except:
                pass
    
    # 新增記錄頁面元素資訊的方法
    def record_page_elements(self, page_url, page_title, elements_data):
        """記錄頁面上的互動元素"""
        timestamp = time.time()
        self.page_elements[page_url] = {
            "title": page_title,
            "timestamp": timestamp,
            "elements": elements_data
        }
        
        # 同時將頁面元素記錄添加到操作記錄中
        self.listener.actions.append({
            "type": "PageElements",
            "url": page_url,
            "title": page_title,
            "elements_count": len(elements_data),
            "timestamp": timestamp
        })
    
    # 獲取頁面元素記錄
    def get_page_elements(self):
        return self.page_elements
    
    def _inject_event_listeners(self):
        """注入額外的事件監聽器以補捉標準 Selenium 可能遺漏的事件"""
        js_script = """
        // 增強版點擊事件監聽
        document.addEventListener('click', function(e) {
            var target = e.target;
            console.log('Native click detected:', target);
            
            // 記錄點擊事件到全局變數
            if (!window.scheminClickEvents) {
                window.scheminClickEvents = [];
            }
            
            // 獲取元素相關資訊
            var elementInfo = {
                tagName: target.tagName,
                id: target.id,
                className: target.className,
                textContent: target.textContent && target.textContent.trim(),
                type: target.type,
                value: target.value,
                timestamp: Date.now()
            };
            
            window.scheminClickEvents.push(elementInfo);
        }, true);
        
        // 增強版輸入事件監聽
        document.addEventListener('input', function(e) {
            var target = e.target;
            console.log('Native input detected:', target);
            
            // 記錄輸入事件到全局變數
            if (!window.scheminInputEvents) {
                window.scheminInputEvents = [];
            }
            
            // 獲取元素相關資訊
            var elementInfo = {
                tagName: target.tagName,
                id: target.id,
                className: target.className,
                type: target.type,
                value: target.value,
                timestamp: Date.now()
            };
            
            window.scheminInputEvents.push(elementInfo);
        }, true);
        
        console.log('Enhanced event listeners injected');
        """
        self.driver.execute_script(js_script)
    
    def _start_monitoring(self):
        # 使用增強版的 JavaScript 註冊滾動監聽器
        scroll_script = """
        window.scheminScrollData = {
            lastPosition: window.scrollY,
            lastTime: new Date().getTime(),
            hasNewScroll: false,
            debounceTimer: null,
            scrollEvents: []
        };
        
        window.addEventListener('scroll', function() {
            // 儲存當前滾動位置和時間
            var currentPosition = window.scrollY;
            var currentTime = new Date().getTime();
            
            // 清除之前的定時器
            if (window.scheminScrollData.debounceTimer) {
                clearTimeout(window.scheminScrollData.debounceTimer);
            }
            
            // 設置新的定時器, 在滾動停止300ms後才記錄
            window.scheminScrollData.debounceTimer = setTimeout(function() {
                // 確定滾動方向和滾動距離
                var direction = currentPosition > window.scheminScrollData.lastPosition ? 'down' : 'up';
                var distance = Math.abs(currentPosition - window.scheminScrollData.lastPosition);
                
                // 只記錄顯著的滾動 (大於50px)
                if (distance > 50) {
                    // 收集當前可見的主要元素
                    var visibleElements = [];
                    var elementsToCheck = document.querySelectorAll('h1, h2, h3, a, button, [role="button"], .title, .header');
                    
                    for (var i = 0; i < elementsToCheck.length && visibleElements.length < 5; i++) {
                        var el = elementsToCheck[i];
                        var rect = el.getBoundingClientRect();
                        if (rect.top >= 0 && rect.top <= window.innerHeight) {
                            var elText = el.textContent.trim();
                            if (elText && elText.length > 0 && elText.length < 100) {
                                visibleElements.push({
                                    text: elText,
                                    tag: el.tagName.toLowerCase(),
                                    top: rect.top
                                });
                            }
                        }
                    }
                    
                    window.scheminScrollData.scrollEvents.push({
                        direction: direction,
                        position: currentPosition,
                        prevPosition: window.scheminScrollData.lastPosition,
                        distance: distance,
                        visibleElements: visibleElements,
                        timestamp: currentTime
                    });
                    
                    window.scheminScrollData.lastPosition = currentPosition;
                    window.scheminScrollData.lastTime = currentTime;
                    window.scheminScrollData.hasNewScroll = true;
                }
            }, 300);
        });
        """
        self.driver.execute_script(scroll_script)
        
        # 注入後退操作監聽
        back_script = """
        // 監聽回退操作
        window.scheminBackData = {
            lastUrl: window.location.href,
            hasGoback: false,
            gobackEvents: []
        };
        
        // 覆蓋 history.back 方法
        var originalBack = history.back;
        history.back = function() {
            console.log('偵測到回退操作');
            window.scheminBackData.gobackEvents.push({
                from: window.location.href,
                timestamp: Date.now()
            });
            window.scheminBackData.hasGoback = true;
            return originalBack.apply(this, arguments);
        };
        
        // 監聽 popstate 事件 (瀏覽器後退按鈕)
        window.addEventListener('popstate', function() {
            console.log('偵測到 popstate 事件');
            window.scheminBackData.gobackEvents.push({
                from: window.scheminBackData.lastUrl,
                to: window.location.href,
                timestamp: Date.now()
            });
            window.scheminBackData.lastUrl = window.location.href;
            window.scheminBackData.hasGoback = true;
        });
        """
        self.driver.execute_script(back_script)
        
        # 啟動背景監控
        import threading
        self.monitor_thread = threading.Thread(target=self._monitor_background_events, daemon=True)
        self.monitor_thread.start()
    
    def _monitor_background_events(self):
        """監控背景事件，如頁面滾動、URL 變化以及原生點擊和輸入事件"""
        check_interval = 0.3  # 檢查間隔（秒）
        
        while not self.stop_background_thread:
            time.sleep(check_interval)
            
            if not self.is_recording:
                continue
                
            try:
                # 檢查原生點擊事件
                try:
                    click_events = self.driver.execute_script("""
                        var events = [];
                        if (window.scheminClickEvents && window.scheminClickEvents.length > 0) {
                            events = window.scheminClickEvents;
                            window.scheminClickEvents = [];
                        }
                        return events;
                    """) or []
                    
                    for event in click_events:
                        # 為原生點擊建立較簡單的元素描述
                        tag = event.get("tagName", "").lower()
                        element_id = event.get("id", "")
                        text = event.get("textContent", "")
                        if len(text) > 100:
                            text = text[:97] + "..."
                            
                        description = text or f"{tag} 元素"
                        
                        # 記錄點擊操作
                        self.listener.actions.append({
                            "type": "Click",
                            "target": description,
                            "element_text": description,
                            "element_details": event,
                            "timestamp": event.get("timestamp", time.time()) / 1000.0
                        })
                except:
                    pass
                    
                # 檢查原生輸入事件
                try:
                    input_events = self.driver.execute_script("""
                        var events = [];
                        if (window.scheminInputEvents && window.scheminInputEvents.length > 0) {
                            events = window.scheminInputEvents;
                            window.scheminInputEvents = [];
                        }
                        return events;
                    """) or []
                    
                    for event in input_events:
                        # 為原生輸入建立較簡單的元素描述
                        tag = event.get("tagName", "").lower()
                        element_id = event.get("id", "")
                        element_type = event.get("type", "")
                        value = event.get("value", "")
                        
                        if element_type in ["text", "search", "email", "password"]:
                            type_desc = f"{element_type}輸入框"
                        elif tag == "textarea":
                            type_desc = "文本區域"
                        else:
                            type_desc = "輸入框"
                            
                        description = type_desc or f"{tag} 元素"
                        
                        # 記錄輸入操作
                        self.listener.actions.append({
                            "type": "Type",
                            "target": description,
                            "element_text": f"對'{description}'輸入'{value}'",
                            "value": value,
                            "element_details": event,
                            "timestamp": event.get("timestamp", time.time()) / 1000.0
                        })
                except:
                    pass
                
                # 檢查頁面 URL 是否變化 (新增或改進)
                current_url = self.driver.current_url
                if current_url != self.last_url:
                    try:
                        page_title = self.driver.title
                        
                        # 確定是否為後退操作
                        is_back_navigation = False
                        try:
                            # 檢查瀏覽器歷史記錄和後退數據
                            is_back_navigation = self.driver.execute_script("""
                                try {
                                    // 檢查導航類型
                                    var navType = performance.getEntriesByType('navigation')[0].type === 'back_forward';
                                    // 檢查是否已標記為後退
                                    var hasBackData = window.scheminBackData && window.scheminBackData.hasGoback;
                                    return navType || hasBackData;
                                } catch(e) {
                                    return window.scheminBackData && window.scheminBackData.hasGoback;
                                }
                            """)
                        except:
                            pass
                        
                        # 根據導航類型記錄不同類型的操作
                        if is_back_navigation:
                            # 處理後退事件
                            back_data = self.driver.execute_script("""
                                var events = [];
                                if (window.scheminBackData) {
                                    events = window.scheminBackData.gobackEvents;
                                    window.scheminBackData.gobackEvents = [];
                                    window.scheminBackData.hasGoback = false;
                                }
                                return events;
                            """) or []
                            
                            # 取最後一個後退事件
                            back_event = back_data[-1] if back_data else {}
                            
                            self.listener.actions.append({
                                "type": "Goback",
                                "from": self.last_url,
                                "to": current_url,
                                "to_title": page_title,
                                "element_text": f"後退到 {page_title}",  # 新增: 添加描述文本
                                "timestamp": back_event.get("timestamp", time.time()) / 1000.0
                            })
                        else:
                            # 如果無法確定是否為後退操作，記錄為一般導航
                            self.listener.actions.append({
                                "type": "Navigate",
                                "from": self.last_url,
                                "to": current_url,
                                "to_title": page_title,
                                "element_text": f"導航至 {current_url}",  # 新增: 添加描述文本
                                "timestamp": time.time()
                            })
                        
                        self.last_url = current_url
                    except:
                        pass
                
                # 檢查滾動操作 (增強版)
                try:
                    has_new_scroll = self.driver.execute_script("return window.scheminScrollData && window.scheminScrollData.hasNewScroll")
                    if has_new_scroll:
                        # 獲取所有新滾動事件
                        scroll_events = self.driver.execute_script("""
                            var events = [];
                            if (window.scheminScrollData) {
                                events = window.scheminScrollData.scrollEvents;
                                window.scheminScrollData.scrollEvents = [];
                                window.scheminScrollData.hasNewScroll = false;
                            }
                            return events;
                        """) or []
                        
                        for event in scroll_events:
                            # 取得可見元素描述
                            visible_elements = event.get("visibleElements", [])
                            visible_texts = []
                            
                            for el in visible_elements:
                                if el.get("text"):
                                    visible_texts.append(f"{el.get('tag')}: {el.get('text')}")
                            
                            # 簡化可見元素文本
                            visible_text = ", ".join(visible_texts[:3]) if visible_texts else ""
                            
                            self.listener.actions.append({
                                "type": "Scroll",
                                "direction": event.get("direction", "unknown"),
                                "distance": event.get("distance", 0),
                                "element_text": visible_text,  # 新增: 將可見元素作為滾動描述
                                "timestamp": event.get("timestamp", time.time()) / 1000.0
                            })
                except Exception as e:
                    pass
            except:
                # 忽略監控過程中的錯誤
                pass
            
            # 休息一小段時間，避免過度佔用 CPU
            time.sleep(0.2)
    
    def get_actions(self):
        """獲取記錄的操作，並標準化為五種類型"""
        # 過濾並標準化動作
        standard_actions = []
        
        for action in self.listener.actions:
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
        return self.listener.is_finished()
