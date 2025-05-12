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

    def setup_browser(self):
        """Initialize the browser and navigate to Wikipedia"""
        print("Setting up browser...")
        options = Options()
        options.add_argument("--window-size=1366,768")
        
        self.driver = webdriver.Edge(options=options)
        
        # Navigate to Wikipedia
        print("Navigating to Wikipedia...")
        self.driver.get("https://www.wikipedia.org")
        
        # Wait for page to load
        WebDriverWait(self.driver, 10).until(
            EC.presence_of_element_located((By.ID, "searchInput"))
        )
        
        print("Wikipedia loaded successfully")
        
        # Inject userBehaviour.js
        self.inject_user_behaviour_js()
        
        # Configure and start tracking
        print("Configuring and starting userBehaviour tracking...")
        start_success = self.driver.execute_script("""
            try {
                // Set up error capturing
                window.jsErrors = [];
                window.addEventListener('error', function(e) {
                    console.error('JS error captured:', e.error);
                    window.jsErrors.push({
                        message: e.message,
                        source: e.filename,
                        line: e.lineno,
                        stack: e.error ? e.error.stack : null
                    });
                });
                
                // Configure userBehaviour
                userBehaviour.config({
                    processTime: 5,  // Process data every 5 seconds
                    processData: function(results) {
                        // Store results in a global variable to access from Python
                        window.lastResults = results;
                        console.log("User behaviour data processed");
                    }
                });
                
                // Start tracking
                userBehaviour.start();
                console.log("User behaviour tracking started");
                return true;
            } catch(e) {
                console.error("Error configuring userBehaviour:", e);
                return {error: e.toString()};
            }
        """)
        
        if start_success is True:
            print("User behaviour tracking started successfully")
        else:
            print(f"Failed to start userBehaviour: {start_success}")
            # Check for any JavaScript errors
            js_errors = self.driver.execute_script("return window.jsErrors || [];")
            if js_errors:
                print("JavaScript errors detected:")
                for error in js_errors:
                    print(f"  - {error.get('message')} at {error.get('source')}:{error.get('line')}")
            
            # Check if userBehaviour is defined
            is_defined = self.driver.execute_script("return typeof userBehaviour !== 'undefined';")
            print(f"Is userBehaviour defined: {is_defined}")

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
            
            # Verify if the script was injected properly
            is_defined = self.driver.execute_script("return typeof userBehaviour !== 'undefined';")
            if is_defined:
                print("userBehaviour.js injected successfully")
                
                # Check what properties and methods are available
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
        """Perform various user actions on Wikipedia"""
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
                            self.driver.back()
                            time.sleep(1)
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
        
        print("User actions completed")

    def get_results(self):
        """Get the tracking results from userBehaviour"""
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
                self.results = json.loads(results_json)
                print(f"Retrieved {len(json.dumps(self.results))} characters of tracking data")
            else:
                print("No results data received")
                self.results = {}
                
        except Exception as e:
            print(f"Error getting results: {e}")
            self.results = {"error": str(e)}
        
        return self.results

    def display_results(self):
        """Display the tracking results in a readable format"""
        if not self.results or (isinstance(self.results, dict) and "error" in self.results):
            print("No tracking results available or error occurred")
            if isinstance(self.results, dict) and "error" in self.results:
                print(f"Error: {self.results['error']}")
            return
        
        print("\n=== USER BEHAVIOUR TRACKING RESULTS ===\n")
        
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
        if 'clicks' in self.results:
            print(f"\nCLICKS: {self.results['clicks']['clickCount']}")
            for i, click in enumerate(self.results['clicks']['clickDetails'][:5]):
                print(f"  Click {i+1}: Position ({click[0]}, {click[1]})")
                if len(click) > 2 and click[2]:  # If path exists
                    print(f"    Element path: {click[2]}")
            if len(self.results['clicks']['clickDetails']) > 5:
                print(f"  ...and {len(self.results['clicks']['clickDetails']) - 5} more clicks")
        
        # Navigation History
        if 'navigationHistory' in self.results and self.results['navigationHistory']:
            print("\nNAVIGATION HISTORY:")
            for i, nav in enumerate(self.results['navigationHistory'][:5]):
                print(f"  {i+1}: {nav[0]}")
            if len(self.results['navigationHistory']) > 5:
                print(f"  ...and {len(self.results['navigationHistory']) - 5} more navigation events")
        
        # Mouse Movements
        if 'mouseMovements' in self.results:
            print(f"\nMOUSE MOVEMENTS: {len(self.results['mouseMovements'])} data points")
        
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

    def run_test(self):
        """Run the complete test"""
        try:
            self.setup_browser()
            self.perform_user_actions()  # Re-enable user actions
            results = self.get_results()
            self.display_results()
        except Exception as e:
            print(f"Test failed with error: {e}")
        finally:
            if self.driver:
                print("Closing browser...")
                self.driver.quit()


if __name__ == "__main__":
    print("Starting UserBehaviour.js testing on Wikipedia...")
    tester = UserBehaviourTester()
    tester.run_test()
