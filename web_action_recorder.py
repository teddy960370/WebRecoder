import json
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
#from selenium.webdriver.chrome.options import Options
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from action_recorder import ActionRecorder
from floating_button import add_floating_button
from task_dialog import add_task_dialog


def get_web_element_rect(browser, mark_elements=True):

    remove_SoM_js = """
        function removeMarks() {
            // 查找所有可能的標記元素
            const markedElements = document.querySelectorAll("div[style*='z-index: 2147483647']");
            
            markedElements.forEach(element => {
                if (element.style.position === "absolute" && element.style.pointerEvents === "none") {
                    element.remove();
                }
            });
        }

        return removeMarks();
    """
    browser.execute_script(remove_SoM_js)

    js_script = """
        function markPage(shouldMarkElements) {
            // 在函數開始就初始化 labels 陣列，確保無論是否標記元素都會返回
            let labels = [];
            var bodyRect = document.body.getBoundingClientRect();

            var items = Array.prototype.slice.call(
                document.querySelectorAll('*')
            ).map(function(element) {
                var vw = Math.max(document.documentElement.clientWidth || 0, window.innerWidth || 0);
                var vh = Math.max(document.documentElement.clientHeight || 0, window.innerHeight || 0);
                var bodyRect = document.body.getBoundingClientRect();
                var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                
                var rects = [...element.getClientRects()].map(bb => {
                    const rect = {
                        left: bb.left + window.pageXOffset,
                        top: bb.top + window.pageYOffset,
                        right: bb.right + window.pageXOffset,
                        bottom: bb.bottom + window.pageXOffset,
                        width: bb.width,
                        height: bb.height
                    };
                    
                    // 檢查元素是否在當前視窗中可見
                    const isVisible = (
                        rect.top < (window.innerHeight + scrollTop) &&
                        rect.bottom > scrollTop &&
                        rect.left < (window.innerWidth + window.pageXOffset) &&
                        rect.right > window.pageXOffset
                    );
                    
                    return {
                        ...rect,
                        isVisible
                    }
                });

                var area = rects.reduce((acc, rect) => acc + rect.width * rect.height, 0);
                var isAnyVisible = rects.some(rect => rect.isVisible);

                return {
                    element: element,
                    include: 
                        (element.tagName === "INPUT" || element.tagName === "TEXTAREA" || element.tagName === "SELECT") ||
                        (element.tagName === "BUTTON" || element.tagName === "A" || (element.onclick != null) || window.getComputedStyle(element).cursor == "pointer") ||
                        (element.tagName === "IFRAME" || element.tagName === "VIDEO" || element.tagName === "LI" || element.tagName === "TD" || element.tagName === "OPTION")
                    ,
                    area,
                    rects,
                    isVisible: isAnyVisible,
                    text: element.textContent.trim().replace(/\s{2,}/g, ' '),
                    // 先收集元素的所有屬性，避免後續需要再次訪問元素
                    tagName: element.tagName,
                    type: element.getAttribute("type"),
                    ariaLabel: element.getAttribute("aria-label"),
                    name: element.getAttribute("name"),
                    id: element.getAttribute("id"),
                    className: element.className
                };
            }).filter(item =>
                item.include && (item.area >= 20)
            );

            // Only keep inner clickable items
            // first delete button inner clickable items
            const buttons = Array.from(document.querySelectorAll('button, a, input[type="button"], div[role="button"]'));

            //items = items.filter(x => !buttons.some(y => y.contains(x.element) && !(x.element === y) ));
            items = items.filter(x => !buttons.some(y => items.some(z => z.element === y) && y.contains(x.element) && !(x.element === y) ));
            items = items.filter(x => 
                !(x.element.parentNode && 
                x.element.parentNode.tagName === 'SPAN' && 
                x.element.parentNode.children.length === 1 && 
                x.element.parentNode.getAttribute('role') &&
                items.some(y => y.element === x.element.parentNode)));

            items = items.filter(x => !items.some(y => x.element.contains(y.element) && !(x == y)))

            // 總是創建視覺元素，但根據 shouldMarkElements 決定是否顯示
            // Function to generate random colors
            function getRandomColor(index) {
                var letters = '0123456789ABCDEF';
                var color = '#';
                for (var i = 0; i < 6; i++) {
                color += letters[Math.floor(Math.random() * 16)];
                }
                return color;
            }
         
            // Lets create a floating border on top of these elements that will always be visible
            items.forEach(function(item, index) {
                item.rects.forEach((bbox) => {
                const container = document.createElement("div");
                container.style.position = "absolute";
                container.style.top = "0";
                container.style.left = "0";
                container.style.width = "0";
                container.style.height = "0";
                container.style.overflow = "visible";
                
                // 只有在 shouldMarkElements 為 true 時才添加到 DOM
                if (shouldMarkElements) {
                    document.body.appendChild(container);
                }

                newElement = document.createElement("div");
                var borderColor = getRandomColor(index);
                newElement.style.outline = `2px dashed ${borderColor}`;
                newElement.style.position = "absolute";
                newElement.style.left = bbox.left + "px";
                newElement.style.top = bbox.top + "px";
                newElement.style.width = bbox.width + "px";
                newElement.style.height = bbox.height + "px";
                newElement.style.pointerEvents = "none";
                newElement.style.boxSizing = "border-box";
                newElement.style.zIndex = 2147483647;
                
                // Add floating label at the corner
                var label = document.createElement("span");
                label.textContent = index;
                label.style.position = "absolute";
                // 修正標籤位置計算，不再考慮 window.pageYOffset
                label.style.top = Math.max(-19, -bbox.top + bbox.top) + "px";
                label.style.left = Math.min(Math.floor(bbox.width / 5), 2) + "px";
                label.style.background = borderColor;
                label.style.color = "white";
                label.style.padding = "2px 4px";
                label.style.fontSize = "12px";
                label.style.borderRadius = "2px";
                newElement.appendChild(label);
                
                container.appendChild(newElement);
                
                // 無論是否顯示，都將容器添加到 labels 陣列中
                labels.push(container);
                });
            });

            return [labels, items]
        }
        return markPage(mark_elements);""".replace("mark_elements", str(mark_elements).lower())
        
    rects, items_raw = browser.execute_script(js_script)

    format_ele_text = []
    elements_data = []
    
    # 安全地處理元素，避免 StaleElementReferenceException
    for web_ele_id in range(len(items_raw)):
        try:
            # 從 JavaScript 中已收集的數據中獲取資訊，而不是再次訪問 DOM
            item = items_raw[web_ele_id]
            label_text = item['text']
            ele_tag_name = item['tagName'].lower()
            ele_type = item['type']
            ele_aria_label = item['ariaLabel']
            ele_name = item['name']
            is_visible = item['isVisible']
            
            input_attr_types = ['text', 'search', 'password', 'email', 'tel','checkbox','radio']
            
            # 構建元素描述文本
            visibility = "(visible)" if is_visible else "(not visible)"
            
            if not label_text:
                if (ele_tag_name == 'input' and ele_type in input_attr_types) or ele_tag_name == 'textarea' or (ele_tag_name == 'button' and ele_type in ['submit', 'button']):
                    if ele_aria_label:
                        format_ele_text.append(f"[{web_ele_id}] {visibility}: <{ele_tag_name}> \"{ele_aria_label}\";")
                    elif ele_name:
                        format_ele_text.append(f"[{web_ele_id}] {visibility}: <{ele_tag_name}> \"{ele_name}\";")
                    else:
                        format_ele_text.append(f"[{web_ele_id}] {visibility}: <{ele_tag_name}> \"{label_text}\";")

            elif label_text and len(label_text) < 200:
                if not ("<img" in label_text and "src=" in label_text):
                    if ele_tag_name in ["button", "input", "textarea"]:
                        if ele_aria_label and (ele_aria_label != label_text):
                            format_ele_text.append(f"[{web_ele_id}] {visibility}: <{ele_tag_name}> \"{label_text}\", \"{ele_aria_label}\";")
                        else:
                            format_ele_text.append(f"[{web_ele_id}] {visibility}: <{ele_tag_name}> \"{label_text}\";")
                    else:
                        if ele_aria_label and (ele_aria_label != label_text):
                            format_ele_text.append(f"[{web_ele_id}] {visibility}: \"{label_text}\", \"{ele_aria_label}\";")
                        else:
                            format_ele_text.append(f"[{web_ele_id}] {visibility}: \"{label_text}\";")
            
            # 構建元素詳細資訊，用於 JSON
            element_data = {
                "id": web_ele_id,
                "text": label_text,
                "tag_name": ele_tag_name,
                "type": ele_type,
                "aria_label": ele_aria_label,
                "name": ele_name,
                "is_visible": is_visible,
                "id_attribute": item['id'],
                "class_name": item['className'],
                "rectangles": []
            }

            # 添加元素的位置信息
            for rect in item['rects']:
                element_data["rectangles"].append({
                    "left": rect['left'],
                    "top": rect['top'],
                    "right": rect['right'],
                    "bottom": rect['bottom'],
                    "width": rect['width'],
                    "height": rect['height'],
                    "is_visible": rect['isVisible']
                })

            elements_data.append(element_data)
        
        except Exception as e:
            print(f"處理元素 {web_ele_id} 時發生錯誤: {str(e)}")
            # 如果處理元素出錯，添加一個基本的佔位符
            elements_data.append({
                "id": web_ele_id,
                "error": str(e),
                "is_error": True
            })

    format_ele_text = '\t'.join(format_ele_text)
    
    return rects, [web_ele for web_ele in items_raw], format_ele_text, elements_data

# 注入阻止新分頁開啟的腳本並添加浮動按鈕
def inject_scripts(driver, recorder, task_description):
    # 等待頁面加載完成
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )
    
    # 添加懸浮結束按鈕
    add_floating_button(driver, on_click_callback=lambda: save_and_quit(driver, recorder, task_description))
    
    # 偵測並記錄頁面元素資訊 - 添加重試機制和錯誤處理
    max_retries = 3
    retry_count = 0
    success = False
    
    # 確保頁面完全載入
    try:
        WebDriverWait(driver, 5).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )
    except:
        print("等待頁面載入完成超時")
    
    # 短暫等待讓頁面渲染穩定
    time.sleep(1)
    
    while not success and retry_count < max_retries:
        try:
            # 移除之前可能存在的標記
            driver.execute_script("""
                try {
                    const markedElements = document.querySelectorAll("div[style*='z-index: 2147483647']");
                    markedElements.forEach(element => {
                        if (element.style.position === "absolute" && element.style.pointerEvents === "none") {
                            element.remove();
                        }
                    });
                    return true;
                } catch(e) {
                    console.error("移除標記失敗:", e);
                    return false;
                }
            """)
            
            # 使用更簡化的 JavaScript 來獲取元素，避免複雜的參數傳遞
            elements_data = driver.execute_script("""
                try {
                    var items = [];
                    var bodyRect = document.body.getBoundingClientRect();
                    var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
                    
                    // 選擇可互動元素
                    var clickableElements = document.querySelectorAll('button, a, input, textarea, select, [role="button"], iframe, video, li, td, option');
                    
                    // 將 NodeList 轉換為陣列並處理每個元素
                    Array.from(clickableElements).forEach(function(element, index) {
                        // 獲取元素屬性
                        var text = element.textContent.trim().replace(/\\s{2,}/g, ' ');
                        var tagName = element.tagName;
                        var type = element.getAttribute('type');
                        var ariaLabel = element.getAttribute('aria-label');
                        var name = element.getAttribute('name');
                        var id = element.getAttribute('id');
                        var className = element.className;
                        
                        // 獲取元素位置
                        var rect = element.getBoundingClientRect();
                        var isVisible = (
                            rect.top < window.innerHeight &&
                            rect.bottom > 0 &&
                            rect.left < window.innerWidth &&
                            rect.right > 0 &&
                            getComputedStyle(element).display !== 'none' &&
                            getComputedStyle(element).visibility !== 'hidden'
                        );
                        
                        // 只記錄大小合理且可能可見的元素
                        if ((rect.width * rect.height) >= 20) {
                            items.push({
                                id: index,
                                text: text,
                                tagName: tagName,
                                type: type,
                                ariaLabel: ariaLabel,
                                name: name,
                                id_attribute: id,
                                className: className,
                                isVisible: isVisible,
                                rect: {
                                    left: rect.left + window.pageXOffset,
                                    top: rect.top + window.pageYOffset,
                                    right: rect.right + window.pageXOffset,
                                    bottom: rect.bottom + window.pageYOffset,
                                    width: rect.width,
                                    height: rect.height
                                }
                            });
                        }
                    });
                    
                    return items;
                } catch(e) {
                    console.error("獲取頁面元素失敗:", e);
                    return [];
                }
            """)
            
            if elements_data and len(elements_data) > 0:
                # 處理元素數據，保存到記錄器
                formatted_elements = []
                
                for item in elements_data:
                    formatted_element = {
                        "id": item.get("id", 0),
                        "text": item.get("text", ""),
                        "tag_name": item.get("tagName", "").lower() if item.get("tagName") else "",
                        "type": item.get("type", ""),
                        "aria_label": item.get("ariaLabel", ""),
                        "name": item.get("name", ""),
                        "is_visible": item.get("isVisible", False),
                        "id_attribute": item.get("id_attribute", ""),
                        "class_name": item.get("className", ""),
                        "rectangles": [
                            {
                                "left": item.get("rect", {}).get("left", 0),
                                "top": item.get("rect", {}).get("top", 0),
                                "right": item.get("rect", {}).get("right", 0),
                                "bottom": item.get("rect", {}).get("bottom", 0),
                                "width": item.get("rect", {}).get("width", 0),
                                "height": item.get("rect", {}).get("height", 0),
                                "is_visible": item.get("isVisible", False)
                            }
                        ]
                    }
                    formatted_elements.append(formatted_element)
                
                # 記錄頁面元素
                page_url = driver.current_url
                page_title = driver.title
                recorder.record_page_elements(page_url, page_title, formatted_elements)
                print(f"已記錄頁面 '{page_title}' 的 {len(formatted_elements)} 個互動元素")
                success = True
            else:
                retry_count += 1
                print(f"頁面元素為空，重試中 ({retry_count}/{max_retries})...")
                time.sleep(1)
        except Exception as e:
            retry_count += 1
            print(f"記錄頁面元素時發生錯誤 (嘗試 {retry_count}/{max_retries}): {str(e)}")
            time.sleep(1)
    
    # 如果所有嘗試都失敗，記錄一個空的元素集
    if not success:
        try:
            print("無法獲取頁面元素，記錄空元素集")
            recorder.record_page_elements(driver.current_url, driver.title, [])
        except Exception as e:
            print(f"記錄空元素集時發生錯誤: {str(e)}")

def enhance_scroll_detection(driver):
    """增強滾動偵測功能"""
    scroll_script = """
    // 初始化滾動追蹤
    window.scheminScrollData = {
        lastPosition: window.scrollY,
        lastTime: Date.now(),
        scrollEvents: [],
        hasNewScroll: false
    };
    
    // 監聽滾動事件
    window.addEventListener('scroll', function() {
        var currentPosition = window.scrollY;
        var currentTime = Date.now();
        
        // 避免記錄過於頻繁的微小滾動
        if (currentTime - window.scheminScrollData.lastTime < 300) {
            return;
        }
        
        // 確定滾動方向和距離
        var direction = currentPosition > window.scheminScrollData.lastPosition ? 'down' : 'up';
        var distance = Math.abs(currentPosition - window.scheminScrollData.lastPosition);
        
        // 只記錄顯著的滾動 (大於50px)
        if (distance > 50) {
            // 紀錄可見元素
            var visibleElements = [];
            var elements = document.querySelectorAll('h1, h2, h3, button, a[role="button"], a');
            
            for (var i = 0; i < elements.length && visibleElements.length < 5; i++) {
                var el = elements[i];
                var rect = el.getBoundingClientRect();
                
                if (rect.top >= 0 && rect.top <= window.innerHeight && el.textContent.trim()) {
                    visibleElements.push({
                        text: el.textContent.trim(),
                        tag: el.tagName.toLowerCase()
                    });
                }
            }
            
            window.scheminScrollData.scrollEvents.push({
                direction: direction,
                position: currentPosition,
                prevPosition: window.scheminScrollData.lastPosition,
                distance: distance,
                visibleElements: visibleElements,
                timestamp: Date.now()
            });
            
            window.scheminScrollData.lastPosition = currentPosition;
            window.scheminScrollData.lastTime = currentTime;
            window.scheminScrollData.hasNewScroll = true;
        }
    });
    
    // 監聽回退操作
    window.scheminBackData = {
        lastUrl: window.location.href,
        gobackEvents: [],
        hasGoback: false
    };
    
    // 覆蓋history.back方法
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
    
    // 監聽popstate事件(瀏覽器後退按鈕)
    window.addEventListener('popstate', function() {
        console.log('偵測到popstate事件');
        window.scheminBackData.gobackEvents.push({
            from: window.scheminBackData.lastUrl,
            to: window.location.href,
            timestamp: Date.now()
        });
        window.scheminBackData.lastUrl = window.location.href;
        window.scheminBackData.hasGoback = true;
    });
    
    console.log('已啟用增強型滾動和回退偵測');
    """
    driver.execute_script(scroll_script)

def modify_action_recorder(recorder):
    """增強ActionRecorder功能以支援標準化的操作類型"""
    original_stop_recording = recorder.stop_recording
    
    def enhanced_stop_recording():
        """增強版的stop_recording，標準化操作類型"""
        result = original_stop_recording()
        
        # 標準化所有操作為四種類型
        standardized_actions = []
        for action in recorder.actions:
            action_type = action.get("type", "")
            
            # 統一操作類型
            if "click" in action_type.lower():
                action["type"] = "Click"
            elif "type" in action_type.lower() or "input" in action_type.lower() or "change" in action_type.lower():
                action["type"] = "Type"
            elif "scroll" in action_type.lower():
                action["type"] = "Scroll"
            elif "back" in action_type.lower() or "popstate" in action_type.lower():
                action["type"] = "Goback"
            elif "navigate" in action_type.lower():
                action["type"] = "Navigate"
            
            standardized_actions.append(action)
        
        recorder.actions = standardized_actions
        return result
    
    # 替換原方法
    recorder.stop_recording = enhanced_stop_recording
    
    # 添加檢查滾動和回退的定時任務
    original_monitor = recorder._monitor_background_events
    
    def enhanced_monitor():
        original_monitor()
        
        # 檢查滾動事件
        try:
            driver = recorder.driver
            has_scroll = driver.execute_script("return window.scheminScrollData && window.scheminScrollData.hasNewScroll")
            if has_scroll:
                scroll_events = driver.execute_script("""
                    var events = window.scheminScrollData.scrollEvents;
                    window.scheminScrollData.scrollEvents = [];
                    window.scheminScrollData.hasNewScroll = false;
                    return events;
                """)
                
                for event in scroll_events:
                    # 獲取可見元素文本
                    visible_texts = []
                    if "visibleElements" in event and event["visibleElements"]:
                        for el in event["visibleElements"]:
                            if el.get("text"):
                                visible_texts.append(el.get("text"))
                    
                    # 記錄滾動操作
                    recorder.listener.actions.append({
                        "type": "Scroll",
                        "direction": event.get("direction", "unknown"),
                        "distance": event.get("distance", 0),
                        "visible_elements": visible_texts,
                        "timestamp": event.get("timestamp", time.time())
                    })
            
            # 檢查回退事件
            has_back = driver.execute_script("return window.scheminBackData && window.scheminBackData.hasGoback")
            if has_back:
                back_events = driver.execute_script("""
                    var events = window.scheminBackData.gobackEvents;
                    window.scheminBackData.gobackEvents = [];
                    window.scheminBackData.hasGoback = false;
                    return events;
                """)
                
                for event in back_events:
                    recorder.listener.actions.append({
                        "type": "Goback",
                        "from": event.get("from", ""),
                        "to": event.get("to", driver.current_url),
                        "timestamp": event.get("timestamp", time.time())
                    })
        except Exception as e:
            print(f"監控背景事件時發生錯誤: {str(e)}")
    
    # 替換監控方法
    recorder._monitor_background_events = enhanced_monitor
    
    return recorder

def handle_ssl_error(driver, url):
    """處理SSL錯誤，嘗試繼續訪問網站"""
    try:
        # 嘗試導航到URL
        driver.get(url)
        
        # 檢查是否有安全警告頁面
        if "此網站的安全憑證" in driver.page_source or "certificate" in driver.page_source.lower():
            # 在不同瀏覽器中處理SSL錯誤頁面的方法
            try:
                # 尋找「進階」或類似按鈕
                advanced_buttons = driver.find_elements(By.ID, "details-button")
                if advanced_buttons:
                    advanced_buttons[0].click()
                    time.sleep(0.5)
                    
                # 尋找「繼續前往」或類似按鈕
                proceed_buttons = driver.find_elements(By.ID, "proceed-link")
                if proceed_buttons:
                    proceed_buttons[0].click()
                    return True
            except Exception as e:
                print(f"無法繞過SSL錯誤: {e}")
    except Exception as e:
        print(f"處理SSL錯誤時發生問題: {e}")
    
    return False

def main():
    print("=== WebRecorder 啟動中... ===")
    # 確保 Data 資料夾存在
    os.makedirs("./data", exist_ok=True)
    
    # 設置 Edge 選項
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("detach", False)
    
    # 新增：減少SSL錯誤日誌
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--ignore-ssl-errors")
    chrome_options.add_argument("--log-level=3")  # 只顯示致命錯誤
    
    chrome_options.add_experimental_option(
        "prefs", {
            "plugins.always_open_pdf_externally": True,
            "profile.default_content_settings.popups": 0,
            "profile.default_content_setting_values.notifications": 2
        }
    )
    # 禁止開啟新分頁
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    chrome_options.add_argument("disable-blink-features=AutomationControlled")
    
    # 初始化 WebDriver
    #driver = webdriver.Chrome(options=chrome_options)
    driver = webdriver.Edge(options=chrome_options)

    # 設定瀏覽器頁面
    driver.set_window_size(1024, 720)

    # 打開 Google 首頁
    url = "https://www.google.com"
    print(f"載入初始頁面：{url}")
    
    try:
        driver.get(url)
    except Exception as e:
        print(f"載入頁面失敗，嘗試處理SSL錯誤: {e}")
        handle_ssl_error(driver, url)
    
    # 顯示任務描述對話框
    print("等待使用者輸入任務描述...")
    task_description = add_task_dialog(driver)
    print(f"任務描述: {task_description}")
    
    # 增強滾動偵測
    #enhance_scroll_detection(driver)
    
    # 初始化操作記錄器
    recorder = ActionRecorder(driver)
    # 開始記錄 - 這將同時注入所有必要的JS
    recorder.start_recording()
    
    # 初次注入腳本
    #inject_scripts(driver, recorder, task_description)
    
    # 主迴圈改進：添加重試機制和更可靠的檢測
    print("開始錄製網頁操作...")
    last_url = driver.current_url
    retry_count = 0
    max_retries = 3
    injection_pending = False
    
    try:
        while not recorder.is_finished():
            # 檢查結束按鈕是否被點擊
            try:
                button_clicked = driver.execute_script("return window.scheminEndRecordingClicked === true;")
                if (button_clicked):
                    print("偵測到結束按鈕點擊")
                    break  # 立即跳出循環，開始保存過程
            except:
                pass  # 忽略執行錯誤

            current_url = driver.current_url
            
            # 檢查 URL 是否變化
            url_changed = current_url != last_url
            
            # 檢查 JS 偵測到的頁面變化
            try:
                needs_reinjection = driver.execute_script("return window.scheminNeedsReinjection === true;")
            except:
                # 如果執行腳本失敗，可能頁面已經變化
                needs_reinjection = True
            
            # 檢查頁面是否處於載入中
            try:
                is_loading = driver.execute_script("return document.readyState !== 'complete';")
            except:
                is_loading = False
            
            # 如果 URL 變化或腳本偵測到變化，且頁面已載入完成，則通知 recorder 檢查和重新注入
            if (url_changed or needs_reinjection) and not is_loading:
                # 如果之前有注入失敗，增加重試計數
                if injection_pending:
                    retry_count += 1
                else:
                    retry_count = 0
                    injection_pending = True
                
                print(f"偵測到頁面變化: {last_url} -> {current_url}")
                print(f"正在重新注入腳本 (嘗試 {retry_count+1}/{max_retries})")
                
                try:
                    # 使用 recorder 的方法檢查並重新注入
                    if recorder.check_and_reinject():
                        # 重新注入成功，再次注入網頁元素檢測腳本
                        add_floating_button(driver, on_click_callback=lambda: save_and_quit(driver, recorder, task_description))
                        #inject_scripts(driver, recorder, task_description)
                    
                    last_url = current_url
                    injection_pending = False
                    retry_count = 0
                    print("腳本注入成功")
                except Exception as e:
                    print(f"腳本注入失敗: {str(e)}")
                    # 如果重試次數用完，就放棄這次注入
                    if retry_count >= max_retries:
                        injection_pending = False
                        retry_count = 0
                        last_url = current_url
                        print("重試次數已達上限，跳過此次注入")
            
            time.sleep(0.3)
        
        # 無論是通過結束按鈕還是recorder.is_finished()結束，都執行保存
        print("錄製結束，開始保存...")
        save_and_quit(driver, recorder, task_description)
        
    except KeyboardInterrupt:
        # 允許用戶通過 Ctrl+C 強制結束
        print("偵測到使用者中斷 (Ctrl+C)，正在結束程式...")
        save_and_quit(driver, recorder, task_description)
    except Exception as e:
        print(f"執行過程中發生錯誤: {str(e)}")
        save_and_quit(driver, recorder, task_description)

def save_and_quit(driver, recorder, task_description):
    # 顯示提示訊息到控制台
    print("儲存操作記錄中...")
    
    try:
        # 停止記錄
        recorder.stop_recording()
        
        # 獲取記錄的操作
        raw_actions = recorder.get_actions()
        # 獲取記錄的頁面元素
        page_elements = recorder.get_page_elements()
        
        # 防抖動處理：合併一定時間內對同一元素的連續輸入事件
        debounced_actions = []
        type_events_by_element = {}  # 按元素標識分組的輸入事件
        non_type_events = []  # 非輸入事件
        
        # 防抖動時間閾值(毫秒)
        debounce_threshold = 1500
        
        # 步驟1：將輸入事件按元素分組，非輸入事件直接保留
        for action in raw_actions:
            if action.get("type") in ("Type","Scroll"):
                # 嘗試獲取元素標識
                element_details = action.get("element_details", {})
                element_type = action.get("type", "")
                element_id = element_details.get("id", "")
                element_name = element_details.get("name", "")
                element_class = element_details.get("class", "")
                
                # 創建元素標識符
                element_key = f"{element_type}_{element_id}_{element_name}_{element_class}"
                
                if element_key not in type_events_by_element:
                    type_events_by_element[element_key] = []
                
                type_events_by_element[element_key].append(action)
            else:
                non_type_events.append(action)
        
        # 步驟2：對每組輸入事件進行防抖動處理
        for element_key, events in type_events_by_element.items():
            if not events:
                continue
                
            # 按時間戳排序
            events.sort(key=lambda x: x.get("timestamp", 0))
            
            # 初始化結果列表和上次事件時間
            debounced_element_events = []
            last_event_time = 0
            
            for event in events:
                current_time = event.get("timestamp", 0) # 毫秒
                
                # 如果是該元素的第一個事件或與上一事件間隔超過閥值
                if not debounced_element_events或 (current_time - last_event_time) > debounce_threshold:
                    debounced_element_events.append(event)
                else:
                    # 更新最後一個事件的值和文本描述
                    last_event = debounced_element_events[-1]
                    last_event["value"] = event.get("value", "")
                    last_event["element_text"] = event.get("element_text", "")
                
                last_event_time = current_time
            
            # 將處理後的事件添加到結果中
            debounced_actions.extend(debounced_element_events)
        
        # 將非輸入事件添加回結果
        debounced_actions.extend(non_type_events)
        
        # 按時間戳重新排序所有事件
        debounced_actions.sort(key=lambda x: x.get("timestamp", 0))
        
        # 將合併後的操作轉換為新格式 
        formatted_actions = []
        action_idx = 1
        
        for action in debounced_actions:
            action_type = action.get("type", "")
            
            # 只處理標準類型的操作
            if action_type not in ["Click", "Type", "Scroll", "Goback", "Navigate"]:
                continue
                
            # 尋找該操作發生時的頁面 URL 和標題
            action_time = action.get("timestamp", 0)
            url = action.get("url", 0)
            page_title = action.get("title", 0)
            
            # 為每個頁面找到最接近的操作時間
            for page_url, page_data in page_elements.items():
                page_time = page_data.get("timestamp", 0)
                # 如果頁面記錄時間早於或等於操作時間，且比之前找到的更近
                if page_time <= action_time:
                    url = page_url
                    page_title = page_data.get("title", "")
            
            # 從操作中獲取元素文本描述
            elements_text = action.get("element_text", "")
            
            # 建立新格式的操作記錄
            formatted_action = {
                "order": action_idx,
                "url": url,
                "page_title": page_title,
                "type": action_type,
                "elements_text": elements_text,
                "timestamp": datetime.fromtimestamp(action_time/1000).strftime('%H:%M:%S'),
                "element" : action.get("element", ""),
            }
            
            formatted_actions.append(formatted_action)
            action_idx += 1
        
        # 在最後添加一個 answer 類型的結束節點
        answer_action = {
            "order": action_idx,
            "url": driver.current_url,
            "page_title": driver.title,
            "type": "answer",
            "timestamp": datetime.now().strftime('%H:%M:%S'),
            "elements_text": "任務完成"
        }
        
        # 添加到操作列表中
        formatted_actions.append(answer_action)
        
        # 準備要保存的數據
        data = {
            "task_description": task_description,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "actions": formatted_actions
        }
        
        # 產生檔案名稱 (使用時間戳)
        filename = f"./data/web_actions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 保存為 JSON 檔
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"操作記錄已保存至 {filename}")
    except Exception as e:
        print(f"儲存操作記錄時發生錯誤: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # 確保瀏覽器關閉，即使保存過程中發生錯誤
        try:
            # 使用更強力的方式關閉瀏覽器
            print("正在關閉瀏覽器...")
            driver.quit()
            print("瀏覽器已關閉")
        except Exception as e:
            print(f"關閉瀏覽器時發生錯誤: {str(e)}")
            # 嘗試強制關閉
            try:
                import psutil
                # 獲取 Chrome 進程並終止
                for proc in psutil.process_iter():
                    try:
                        if 'chrome' in proc.name().lower():
                            proc.terminate();
                    except:
                        pass
                print("已嘗試強制關閉 Chrome 進程")
            except:
                print("無法強制關閉 Chrome 進程，請手動關閉瀏覽器")

if __name__ == "__main__":
    try:
        main()
        print("=== WebRecorder 已正常結束 ===")
    except Exception as e:
        print(f"=== WebRecorder 發生未處理的錯誤: {str(e)} ===")
        import traceback
        traceback.print_exc()
