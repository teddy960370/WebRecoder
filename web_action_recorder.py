import json
import os
import time
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
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
                        bottom: bb.bottom + window.pageYOffset,
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
                    text: element.textContent.trim().replace(/\s{2,}/g, ' ')
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
        return markPage(arguments[0]);"""
        
    rects, items_raw = browser.execute_script(js_script, mark_elements)

    format_ele_text = []
    for web_ele_id in range(len(items_raw)):
        label_text = items_raw[web_ele_id]['text']
        ele_tag_name = items_raw[web_ele_id]['element'].tag_name
        ele_type = items_raw[web_ele_id]['element'].get_attribute("type")
        ele_aria_label = items_raw[web_ele_id]['element'].get_attribute("aria-label")
        ele_name = items_raw[web_ele_id]['element'].get_attribute("name")
        input_attr_types = ['text', 'search', 'password', 'email', 'tel','checkbox','radio']

        if not label_text:
            if (ele_tag_name.lower() == 'input' and ele_type in input_attr_types) or ele_tag_name.lower() == 'textarea' or (ele_tag_name.lower() == 'button' and ele_type in ['submit', 'button']):
                visibility = "(visible)" if items_raw[web_ele_id]['isVisible'] else "(not visible)"
                if ele_aria_label:
                    format_ele_text.append(f"[{web_ele_id}] {visibility}: <{ele_tag_name}> \"{ele_aria_label}\";")
                elif ele_name:
                    format_ele_text.append(f"[{web_ele_id}] {visibility}: <{ele_tag_name}> \"{ele_name}\";")
                else:
                    format_ele_text.append(f"[{web_ele_id}] {visibility}: <{ele_tag_name}> \"{label_text}\";" )

        elif label_text and len(label_text) < 200:
            if not ("<img" in label_text and "src=" in label_text):
                visibility = "(visible)" if items_raw[web_ele_id]['isVisible'] else "(not visible)"
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



    format_ele_text = '\t'.join(format_ele_text)
    return rects, [web_ele['element'] for web_ele in items_raw], format_ele_text

# 注入阻止新分頁開啟的腳本並添加浮動按鈕
def inject_scripts(driver, recorder, task_description):
    # 等待頁面加載完成
    WebDriverWait(driver, 10).until(
        lambda d: d.execute_script('return document.readyState') == 'complete'
    )
    
    # 注入阻止新分頁開啟的JavaScript - 使用更強力的方式
    prevent_new_tab_script = """
    (function() {
        // 保存原始的 window.open 方法
        var originalWindowOpen = window.open;
        
        // 覆蓋 window.open 方法
        window.open = function(url, name, specs, replace) {
            console.log("攔截到 window.open 調用:", url);
            // 在當前窗口打開，而不是新窗口
            if (url) {
                window.location.href = url;
            }
            // 返回當前窗口引用，讓原始腳本可以繼續運行
            return window;
        };
        
        // 攔截所有鏈接的點擊事件
        document.addEventListener('click', function(e) {
            var target = e.target;
            
            // 循環向上查找 A 標籤（處理點擊在 A 標籤內部的元素的情況）
            while (target && target.tagName !== 'A' && target.parentElement) {
                target = target.parentElement;
            }
            
            if (target && target.tagName === 'A') {
                // 檢查是否會開啟新分頁
                if (target.target === '_blank' || target.getAttribute('rel') === 'noopener' || 
                    e.ctrlKey || e.metaKey || e.shiftKey) {
                    e.preventDefault();
                    e.stopPropagation();
                    
                    var href = target.href;
                    if (href && !href.startsWith('javascript:') && href !== '#') {
                        console.log("攔截到新分頁連結點擊:", href);
                        window.location.href = href;
                    }
                    return false;
                }
            }
        }, true); // true 表示在捕獲階段處理，先於其他事件監聽器
        
        // 強制修改所有連結，取消 target="_blank"
        function processLinks() {
            var allLinks = document.getElementsByTagName('a');
            for (var i = 0; i < allLinks.length; i++) {
                if (allLinks[i].target === '_blank') {
                    allLinks[i].target = '_self';
                    // 添加攔截器
                    allLinks[i].addEventListener('click', function(e) {
                        e.preventDefault();
                        window.location.href = this.href;
                    });
                }
                
                // 移除可能導致新分頁的屬性
                allLinks[i].removeAttribute('rel');
            }
        }
        
        // 初始處理
        processLinks();
        
        // 覆蓋 window.open 和 showModalDialog 方法在所有框架中
        function applyToFrames(win) {
            try {
                win.open = window.open;
                
                // 遍歷子框架
                if (win.frames && win.frames.length) {
                    for (var i = 0; i < win.frames.length; i++) {
                        try {
                            applyToFrames(win.frames[i]);
                        } catch (e) {
                            console.log("無法訪問框架:", e);
                        }
                    }
                }
            } catch (e) {
                console.log("無法修改框架:", e);
            }
        }
        
        // 應用到所有框架
        try {
            applyToFrames(window);
        } catch (e) {
            console.log("框架處理錯誤:", e);
        }
        
        // 監視 DOM 變化，處理動態添加的連結
        var observer = new MutationObserver(function(mutations) {
            processLinks();
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['target', 'href', 'rel']
        });
        
        // 覆蓋各種可能導致新分頁的事件
        ['mousedown', 'mouseup', 'click', 'dblclick', 'auxclick'].forEach(function(eventType) {
            document.addEventListener(eventType, function(e) {
                if (e.button === 1) { // 中鍵點擊
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }
            }, true);
        });
        
        // 覆蓋 HTMLAnchorElement.prototype.click 方法
        var originalAnchorClick = HTMLAnchorElement.prototype.click;
        HTMLAnchorElement.prototype.click = function() {
            if (this.target === '_blank') {
                this.target = '_self';
            }
            return originalAnchorClick.apply(this, arguments);
        };
        
        console.log("已注入新分頁攔截器");
    })();
    """
    driver.execute_script(prevent_new_tab_script)
    
    # 額外處理框架
    driver.execute_script("""
    try {
        // 處理所有的 iframe
        var iframes = document.getElementsByTagName('iframe');
        for (var i = 0; i < iframes.length; i++) {
            try {
                var iframeDoc = iframes[i].contentDocument || iframes[i].contentWindow.document;
                
                // 在 iframe 中注入相同的腳本
                var script = iframeDoc.createElement('script');
                script.textContent = arguments[0];
                iframeDoc.body.appendChild(script);
            } catch (e) {
                console.log("無法訪問 iframe:", e);
            }
        }
    } catch (e) {
        console.log("iframe 處理錯誤:", e);
    }
    """, prevent_new_tab_script)
    
    # 添加懸浮結束按鈕
    add_floating_button(driver, on_click_callback=lambda: save_and_quit(driver, recorder, task_description))

def main():
    print("=== WebRecorder 啟動中... ===")
    # 確保 Data 資料夾存在
    os.makedirs("./data", exist_ok=True)
    
    # 設置 Chrome 選項
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_experimental_option("detach", False)
    chrome_options.add_experimental_option(
        "prefs", {
            "plugins.always_open_pdf_externally": True
        }
    )
    # 禁止開啟新分頁
    chrome_options.add_argument("--disable-popup-blocking")
    chrome_options.add_experimental_option("prefs", {
        "plugins.always_open_pdf_externally": True,
        "profile.default_content_settings.popups": 0,
        "profile.default_content_setting_values.notifications": 2
    })
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    chrome_options.add_argument("disable-blink-features=AutomationControlled")
    
    # 初始化 WebDriver
    driver = webdriver.Chrome(options=chrome_options)

    # 設定瀏覽器頁面
    driver.set_window_size(1024, 720)

    # 打開 Google 首頁
    print("載入初始頁面：Google 搜尋")
    driver.get("https://www.google.com")
    
    # 顯示任務描述對話框
    print("等待使用者輸入任務描述...")
    task_description = add_task_dialog(driver)
    print(f"任務描述: {task_description}")
    
    # 初始化操作記錄器
    recorder = ActionRecorder(driver)
    recorder.start_recording()
    
    # 初次注入腳本
    inject_scripts(driver, recorder, task_description)
    
    # 改進頁面變化檢測和腳本注入邏輯
    driver.execute_script("""
        // 設置全局變數追蹤頁面狀態
        window.scheminLastUrl = window.location.href;
        window.scheminNeedsReinjection = false;
        
        // 更可靠的頁面變化偵測
        window.scheminMonitorPageChanges = function() {
            // 檢查 URL 變化
            if (window.location.href !== window.scheminLastUrl) {
                console.log('偵測到 URL 變化: ' + window.scheminLastUrl + ' -> ' + window.location.href);
                window.scheminLastUrl = window.location.href;
                window.scheminNeedsReinjection = true;
            }
            
            // 仍需保留這個監控函數運行
            setTimeout(window.scheminMonitorPageChanges, 300);
        };
        
        // 註冊頁面事件監聽器
        window.addEventListener('popstate', function() {
            console.log('偵測到 popstate 事件');
            window.scheminNeedsReinjection = true;
        });
        
        window.addEventListener('hashchange', function() {
            console.log('偵測到 hashchange 事件');
            window.scheminNeedsReinjection = true;
        });
        
        // 攔截 history API
        var originalPushState = history.pushState;
        history.pushState = function() {
            var result = originalPushState.apply(this, arguments);
            console.log('偵測到 pushState 調用');
            window.scheminNeedsReinjection = true;
            return result;
        };
        
        var originalReplaceState = history.replaceState;
        history.replaceState = function() {
            var result = originalReplaceState.apply(this, arguments);
            console.log('偵測到 replaceState 調用');
            window.scheminNeedsReinjection = true;
            return result;
        };
        
        // 啟動監控
        window.scheminMonitorPageChanges();
    """)
    
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
                is_loading = driver.execute_script("return document.readyState !== 'complete';");
            except:
                is_loading = False
            
            # 如果 URL 變化或腳本偵測到變化，且頁面已載入完成，則重新注入腳本
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
                    # 重新注入腳本
                    inject_scripts(driver, recorder, task_description)
                    # 重置重注入標記
                    driver.execute_script("window.scheminNeedsReinjection = false;")
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
        actions = recorder.get_actions()
        
        # 準備要保存的數據
        data = {
            "task_description": task_description,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "actions": actions
        }
        
        # 產生檔案名稱 (使用時間戳)
        filename = f"./data/web_actions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # 保存為 JSON 檔
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"操作記錄已保存至 {filename}")
    except Exception as e:
        print(f"儲存操作記錄時發生錯誤: {str(e)}")
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
