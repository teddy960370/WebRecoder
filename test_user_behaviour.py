import time
import json
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class UserBehaviourTester:
    def __init__(self):
        self.driver = None
        self.results = {}
        self.all_results = []  # 存儲所有頁面的結果
        self.page_count = 0    # 跟踪頁面計數

    def setup_browser(self):
        """Initialize the browser and navigate to Wikipedia"""
        print("Setting up browser...")
        options = Options()
        options.add_argument("--window-size=1366,768")
        
        self.driver = webdriver.Edge(options=options)
        
        # 監聽頁面變化事件
        self.driver.execute_script("""
            window.addEventListener('beforeunload', function() {
                // 在頁面卸載前觸發結果處理
                if (typeof userBehaviour !== 'undefined') {
                    try {
                        userBehaviour.processResults();
                    } catch(e) {
                        console.error("Error processing results before unload:", e);
                    }
                }
            });
        """)
        
        # Navigate to Wikipedia
        print("Navigating to Wikipedia...")
        self.driver.get("https://www.wikipedia.org")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchInput"))
        )
        
        print("Wikipedia loaded successfully")
        self.page_count += 1
        
        # 設置導航監聽器以便在頁面變化時重新注入
        self._setup_navigation_monitoring()
        
        # 初始注入
        self.inject_user_behaviour_js()

    def _setup_navigation_monitoring(self):
        """設置監聽器，在頁面跳轉後重新注入JS"""
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
        """)
        
        # 添加一個在Python中的檢查機制
        self.driver.execute_script("""
            window._checkForNavigation = function() {
                return window._needReinjection === true;
            };
            
            window._resetNavigationFlag = function() {
                window._needReinjection = false;
            };
        """)

    def check_and_reinject(self):
        """檢查是否需要重新注入JS"""
        try:
            needs_injection = self.driver.execute_script("return window._checkForNavigation ? window._checkForNavigation() : true;")
            if needs_injection:
                print("Navigation detected - reinjecting userBehaviour.js")
                self.page_count += 1
                
                # 在注入前先獲取當前頁面的結果
                self.save_current_results()
                
                # 重新注入JS
                self.inject_user_behaviour_js()
                self.driver.execute_script("if (window._resetNavigationFlag) window._resetNavigationFlag();")
                return True
            return False
        except Exception as e:
            print(f"Error checking navigation: {e}")
            return True  # 出錯時假設需要重新注入

    def save_current_results(self):
        """保存當前頁面的結果"""
        try:
            results = self.get_results(save_only=True)
            if results and not isinstance(results, dict) or not results.get('error'):
                self.all_results.append({
                    'page_number': self.page_count,
                    'url': self.driver.current_url,
                    'results': results
                })
                print(f"Saved results from page {self.page_count}: {self.driver.current_url}")
        except Exception as e:
            print(f"Error saving current page results: {e}")

    def inject_user_behaviour_js(self):
        """Inject the userBehaviour.js code into the page using script element approach"""
        try:
            print("Injecting userBehaviour.js using script element method...")
            
            # Read the userBehaviour.js file
            user_behaviour_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "userBehaviour.js")
            with open(user_behaviour_path, "r", encoding="utf-8") as f:
                js_code = f.read()
            
            # Using Method 3: Create a script element approach (confirmed working)
            self.driver.execute_script(f"""
                try {{
                    var script = document.createElement('script');
                    script.textContent = `{js_code.replace('`', '\\`')}`;
                    document.head.appendChild(script);
                    console.log('Script element injection completed');
                }} catch (e) {{
                    console.error('Error in script element injection:', e);
                    throw e;
                }}
            """)
            
            # 驗證腳本是否成功注入
            is_defined = self.driver.execute_script("return typeof userBehaviour !== 'undefined';")
            if is_defined:
                print("userBehaviour.js injected successfully")
                
                # 為注入後的userBehaviour配置設置
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
                        
                        // 配置userBehaviour
                        userBehaviour.config({
                            processTime: 5,  // 每5秒處理一次數據
                            processData: function(results) {
                                // 將結果存儲在全局變量中以便Python訪問
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
                print(f"userBehaviour available methods: {props}")
            else:
                print("WARNING: userBehaviour object is not defined after injection")
        except Exception as e:
            print(f"Error injecting userBehaviour.js: {e}")
            raise

    def perform_user_actions(self):
        """Perform various user actions on Wikipedia with reinjection on navigation"""
        print("Performing user actions on Wikipedia...")
        
        try:
            # Search for something
            search_input = self.driver.find_element(By.ID, "searchInput")
            search_input.click()
            search_input.clear()
            search_input.send_keys("Artificial Intelligence")
            time.sleep(1)
            
            # Go to English Wikipedia
            english_link = self.driver.find_element(By.CSS_SELECTOR, "a[title='English — Wikipedia — The Free Encyclopedia']")
            english_link.click()
            time.sleep(3)
            
            # 檢查頁面跳轉並重新注入
            self.check_and_reinject()
            
            # Wait for the Wikipedia page to load
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.ID, "firstHeading"))
            )
            
            # Search for AI on English Wikipedia
            search_input = self.driver.find_element(By.NAME, "search")
            search_input.click()
            search_input.clear()
            search_input.send_keys("Artificial Intelligence")
            search_input.send_keys(Keys.RETURN)
            time.sleep(3)
            
            # 檢查頁面跳轉並重新注入
            self.check_and_reinject()
            
            # Click on headings and links
            try:
                headings = self.driver.find_elements(By.CSS_SELECTOR, ".mw-headline")
                if headings:
                    # Click on a few headings
                    for i in range(min(3, len(headings))):
                        try:
                            ActionChains(self.driver).move_to_element(headings[i]).perform()
                            time.sleep(0.5)
                        except:
                            pass
                
                # Find and click some links
                links = self.driver.find_elements(By.CSS_SELECTOR, "p a[href^='/wiki/']")
                if links:
                    # Click on a link
                    for i in range(min(2, len(links))):
                        try:
                            ActionChains(self.driver).move_to_element(links[i]).perform()
                            time.sleep(0.5)
                            links[i].click()
                            time.sleep(2)
                            
                            # 檢查頁面跳轉並重新注入
                            self.check_and_reinject()
                            
                            self.driver.back()
                            time.sleep(1)
                            
                            # 檢查頁面跳轉並重新注入
                            self.check_and_reinject()
                        except:
                            pass
            except Exception as e:
                print(f"Error during interaction: {e}")
            
            # Scroll page
            self.driver.execute_script("window.scrollBy(0, 500);")
            time.sleep(1)
            self.driver.execute_script("window.scrollBy(0, 300);")
            time.sleep(1)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(1)
            
            # Allow time for tracking to register
            time.sleep(5)
            
        except Exception as e:
            print(f"Error during user actions: {e}")
        
        # 最終保存當前頁面結果
        self.save_current_results()
        print("User actions completed")

    def get_results(self, save_only=False):
        """Get the tracking results from userBehaviour"""
        if not save_only:
            print("Getting tracking results...")
        
        try:
            # Force processing of results
            self.driver.execute_script("userBehaviour.processResults();")
            
            # Get results from the global variable
            results_json = self.driver.execute_script("""
                try {
                    return JSON.stringify(window.lastResults || {});
                } catch(e) {
                    console.error("Error stringifying results:", e);
                    return JSON.stringify({error: e.toString()});
                }
            """)
            
            if results_json:
                current_results = json.loads(results_json)
                if not save_only:
                    self.results = current_results
                    print(f"Retrieved {len(results_json)} characters of tracking data")
                return current_results
            else:
                if not save_only:
                    print("No results data received")
                    self.results = {}
                return {}
                
        except Exception as e:
            if not save_only:
                print(f"Error getting results: {e}")
                self.results = {"error": str(e)}
            return {"error": str(e)}
        
        return self.results if not save_only else None

    def combine_all_results(self):
        """合併所有頁面的結果"""
        if not self.all_results:
            return self.results  # 如果沒有保存的結果，則返回當前結果
        
        combined_results = {
            'userInfo': self.results.get('userInfo', {}),
            'time': {
                'startTime': min([r['results'].get('time', {}).get('startTime', float('inf')) 
                                for r in self.all_results if 'results' in r] + 
                                [self.results.get('time', {}).get('startTime', float('inf'))]),
                'currentTime': max([r['results'].get('time', {}).get('currentTime', 0) 
                                  for r in self.all_results if 'results' in r] + 
                                  [self.results.get('time', {}).get('currentTime', 0)]),
                'stopTime': self.results.get('time', {}).get('stopTime', 0)
            },
            'clicks': {
                'clickCount': sum([r['results'].get('clicks', {}).get('clickCount', 0) 
                                 for r in self.all_results if 'results' in r] + 
                                 [self.results.get('clicks', {}).get('clickCount', 0)]),
                'clickDetails': []
            },
            'mouseMovements': [],
            'mouseScroll': [],
            'keyboardActivities': [],
            'navigationHistory': [],
            'formInteractions': [],
            'touchEvents': [],
            'mediaInteractions': [],
            'windowSizes': [],
            'visibilitychanges': [],
        }
        
        # 合併所有頁面的詳細結果
        for r in self.all_results:
            if 'results' not in r:
                continue
            page_results = r['results']
            
            # 合併點擊詳情
            if 'clicks' in page_results and 'clickDetails' in page_results['clicks']:
                combined_results['clicks']['clickDetails'].extend(page_results['clicks']['clickDetails'])
            
            # 合併鼠標移動
            if 'mouseMovements' in page_results:
                combined_results['mouseMovements'].extend(page_results['mouseMovements'])
            
            # 合併滾動
            if 'mouseScroll' in page_results:
                combined_results['mouseScroll'].extend(page_results['mouseScroll'])
            
            # 合併其他事件
            for event_type in ['keyboardActivities', 'navigationHistory', 'formInteractions', 
                             'touchEvents', 'mediaInteractions', 'windowSizes', 'visibilitychanges']:
                if event_type in page_results and isinstance(page_results[event_type], list):
                    combined_results[event_type].extend(page_results[event_type])
        
        # 加入當前頁面結果
        if self.results:
            if 'clicks' in self.results and 'clickDetails' in self.results['clicks']:
                combined_results['clicks']['clickDetails'].extend(self.results['clicks']['clickDetails'])
            
            for event_type in ['mouseMovements', 'mouseScroll', 'keyboardActivities', 'navigationHistory', 
                             'formInteractions', 'touchEvents', 'mediaInteractions', 'windowSizes', 'visibilitychanges']:
                if event_type in self.results and isinstance(self.results[event_type], list):
                    combined_results[event_type].extend(self.results[event_type])
        
        return combined_results

    def display_results(self):
        """Display the tracking results in a readable format"""
        # 合併所有頁面結果
        combined_results = self.combine_all_results()
        
        if not combined_results or (isinstance(combined_results, dict) and "error" in combined_results):
            print("No tracking results available or error occurred")
            if isinstance(combined_results, dict) and "error" in combined_results:
                print(f"Error: {combined_results['error']}")
            return
        
        print("\n=== COMBINED USER BEHAVIOUR TRACKING RESULTS ===\n")
        print(f"Data collected across {self.page_count} pages\n")
        
        # User Info
        if 'userInfo' in self.results:
            print("USER INFO:")
            print(f"  Window Size: {self.results['userInfo']['windowSize']}")
            print(f"  Platform: {self.results['userInfo']['platform']}")
            print(f"  User Agent: {self.results['userInfo']['userAgent'][:50]}..." if len(self.results['userInfo']['userAgent']) > 50 else self.results['userInfo']['userAgent'])
            
        # Time Info
        if 'time' in self.results:
            time_spent = (self.results['time']['currentTime'] - self.results['time']['startTime']) / 1000
            print(f"\nTIME SPENT: {time_spent:.2f} seconds")
        
        # Clicks
        if 'clicks' in combined_results:
            print(f"\nCLICKS: {combined_results['clicks']['clickCount']}")
            for i, click in enumerate(combined_results['clicks']['clickDetails'][:5]):
                print(f"  Click {i+1}: Position ({click[0]}, {click[1]})")
                if len(click) > 2 and click[2]:  # If path exists
                    print(f"    Element path: {click[2]}")
            if len(combined_results['clicks']['clickDetails']) > 5:
                print(f"  ...and {len(combined_results['clicks']['clickDetails']) - 5} more clicks")
        
        # Navigation History - 特別重要，顯示頁面跳轉情況
        if 'navigationHistory' in combined_results and combined_results['navigationHistory']:
            print("\nNAVIGATION HISTORY:")
            for i, nav in enumerate(combined_results['navigationHistory'][:10]):
                print(f"  {i+1}: {nav[0]}")
            if len(combined_results['navigationHistory']) > 10:
                print(f"  ...and {len(combined_results['navigationHistory']) - 10} more navigation events")
        
        # Mouse Movements
        if 'mouseMovements' in combined_results:
            print(f"\nMOUSE MOVEMENTS: {len(combined_results['mouseMovements'])} data points")
        
        # Keyboard Activities
        if 'keyboardActivities' in self.results and self.results['keyboardActivities']:
            print(f"\nKEYBOARD EVENTS: {len(self.results['keyboardActivities'])}")
            for i, key in enumerate(self.results['keyboardActivities'][:5]):
                print(f"  Key {i+1}: {key[0]}")
            if len(self.results['keyboardActivities']) > 5:
                print(f"  ...and {len(self.results['keyboardActivities']) - 5} more key events")
        
        # Mouse Scroll
        if 'mouseScroll' in self.results and self.results['mouseScroll']:
            print(f"\nSCROLL EVENTS: {len(self.results['mouseScroll'])}")
            for i, scroll in enumerate(self.results['mouseScroll'][:3]):
                print(f"  Scroll {i+1}: X={scroll[0]}, Y={scroll[1]}")
            if len(self.results['mouseScroll']) > 3:
                print(f"  ...and {len(self.results['mouseScroll']) - 3} more scroll events")
        
        # Window Resize
        if 'windowSizes' in self.results and self.results['windowSizes']:
            print(f"\nWINDOW RESIZE EVENTS: {len(self.results['windowSizes'])}")
        
        # Visibility Changes
        if 'visibilitychanges' in self.results and self.results['visibilitychanges']:
            print(f"\nVISIBILITY CHANGES: {len(self.results['visibilitychanges'])}")
            for i, change in enumerate(self.results['visibilitychanges']):
                print(f"  Change {i+1}: {change[0]}")
        
        # 頁面數據摘要
        print("\nPAGE NAVIGATION SUMMARY:")
        for i, page_data in enumerate(self.all_results):
            print(f"  Page {page_data['page_number']}: {page_data['url']}")
            if 'results' in page_data:
                events_count = sum([
                    len(page_data['results'].get(event_type, [])) 
                    for event_type in ['mouseMovements', 'clicks', 'mouseScroll', 'keyboardActivities']
                    if event_type in page_data['results'] and hasattr(page_data['results'][event_type], '__len__')
                ])
                print(f"    Events tracked: {events_count}")

    def run_test(self):
        """Run the complete test"""
        try:
            self.setup_browser()
            self.perform_user_actions()
            results = self.get_results()
            self.display_results()
        except Exception as e:
            print(f"Test failed with error: {e}")
            import traceback
            traceback.print_exc()
        finally:
            if self.driver:
                print("Closing browser...")
                self.driver.quit()


if __name__ == "__main__":
    print("Starting UserBehaviour.js testing on Wikipedia...")
    tester = UserBehaviourTester()
    tester.run_test()
