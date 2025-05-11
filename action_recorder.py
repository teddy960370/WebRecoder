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
                "element_details": element_details,
                "timestamp": time.time()
            }
            
            self.actions.append(action)
            
        except Exception as e:
            # 如果獲取元素描述時出錯，記錄基本信息
            self.actions.append({
                "type": "Click",
                "target": "未能識別的元素",
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
        self.last_url = driver.current_url
        self.last_scroll_position = 0
        self.is_recording = False
    
    def start_recording(self):
        self.is_recording = True
        # 啟動一個監聽線程來處理滾動和後退操作
        self._start_monitoring()
    
    def stop_recording(self):
        self.is_recording = False
    
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
                    window.scheminScrollData.scrollEvents.push({
                        direction: direction,
                        position: currentPosition,
                        prevPosition: window.scheminScrollData.lastPosition,
                        distance: distance,
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
        
        # 啟動背景監控
        import threading
        self.monitor_thread = threading.Thread(target=self._monitor_background_events, daemon=True)
        self.monitor_thread.start()
    
    def _monitor_background_events(self):
        while self.is_recording:
            try:
                current_url = self.driver.current_url
                
                # 檢查是否有後退或網址變更操作
                if current_url != self.last_url:
                    # 獲取頁面標題
                    try:
                        page_title = self.driver.title
                    except:
                        page_title = ""
                    
                    # 檢查是否為後退操作
                    try:
                        # 記錄動作
                        self.listener.actions.append({
                            "type": "Navigate",
                            "from": self.last_url,
                            "from_title": self.driver.execute_script("return document.referrer ? document.title : ''"),
                            "to": current_url,
                            "to_title": page_title,
                            "timestamp": time.time()
                        })
                    except Exception as e:
                        # 如果無法確定是否為後退操作，記錄為一般導航
                        self.listener.actions.append({
                            "type": "Navigate",
                            "from": self.last_url,
                            "to": current_url,
                            "to_title": page_title,
                            "timestamp": time.time()
                        })
                        
                    self.last_url = current_url
                
                # 檢查滾動操作 (增強版)
                try:
                    has_new_scroll = self.driver.execute_script("return window.scheminScrollData.hasNewScroll")
                    if has_new_scroll:
                        # 獲取所有新滾動事件
                        scroll_events = self.driver.execute_script("var events = window.scheminScrollData.scrollEvents; window.scheminScrollData.scrollEvents = []; return events;")
                        
                        for event in scroll_events:
                            # 獲取可見元素的描述
                            try:
                                visible_elements_script = """
                                function getVisibleElements() {
                                    var elements = [];
                                    var visibleElements = document.querySelectorAll('h1, h2, h3, h4, h5, h6, button, a, [role="button"]');
                                    
                                    for (var i = 0; i < visibleElements.length; i++) {
                                        var el = visibleElements[i];
                                        var rect = el.getBoundingClientRect();
                                        // 只記錄當前視窗中可見的元素
                                        if (rect.top >= 0 && rect.top <= window.innerHeight) {
                                            var text = el.textContent.trim();
                                            var tagName = el.tagName.toLowerCase();
                                            var id = el.id;
                                            var className = el.className;
                                            var ariaLabel = el.getAttribute('aria-label');
                                            var title = el.getAttribute('title');
                                            
                                            if (text || id || className || ariaLabel || title) {
                                                elements.push({
                                                    text: text,
                                                    tag: tagName,
                                                    id: id,
                                                    className: className,
                                                    ariaLabel: ariaLabel,
                                                    title: title,
                                                    top: rect.top
                                                });
                                            }
                                        }
                                    }
                                    return elements;
                                }
                                return getVisibleElements();
                                """
                                visible_elements = self.driver.execute_script(visible_elements_script)
                                
                                # 取前5個顯著的可見元素
                                visible_elements = visible_elements[:5]
                                visible_descriptions = []
                                
                                for el in visible_elements:
                                    desc = el.get("text") or el.get("ariaLabel") or el.get("title") or el.get("id")
                                    if desc:
                                        visible_descriptions.append(f"{el.get('tag', '')}: {desc}")
                            except:
                                visible_descriptions = []
                            
                            self.listener.actions.append({
                                "type": "Scroll",
                                "direction": event.get("direction"),
                                "from_position": event.get("prevPosition"),
                                "to_position": event.get("position"),
                                "distance": event.get("distance"),
                                "visible_elements": visible_descriptions,
                                "timestamp": event.get("timestamp") / 1000.0
                            })
                        
                        # 重置滾動標誌
                        self.driver.execute_script("window.scheminScrollData.hasNewScroll = false;")
                except:
                    pass
            except:
                # 忽略監控過程中的錯誤
                pass
            
            # 休息一小段時間，避免過度佔用 CPU
            time.sleep(0.2)
    
    def get_actions(self):
        return self.listener.actions
    
    def is_finished(self):
        return self.listener.is_finished()
