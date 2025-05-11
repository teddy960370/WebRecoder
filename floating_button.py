from selenium.webdriver.common.by import By

def add_floating_button(driver, on_click_callback=None):
    """
    在網頁上添加一個懸浮的結束按鈕，點擊時調用回調函數
    """
    # 插入 CSS 樣式和按鈕
    script = """
    var styleElement = document.createElement('style');
    styleElement.textContent = `
    #schemind-end-recording-button {
        position: fixed;
        bottom: 20px;
        right: 20px;
        background-color: #f44336;
        color: white;
        border: none;
        border-radius: 50%;
        width: 60px;
        height: 60px;
        font-size: 16px;
        cursor: pointer;
        z-index: 10000;
        box-shadow: 0 2px 5px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
    }
    
    #schemind-end-recording-button:hover {
        background-color: #d32f2f;
        box-shadow: 0 4px 8px rgba(0,0,0,0.4);
    }
    `;
    document.head.appendChild(styleElement);

    var button = document.createElement('button');
    button.id = 'schemind-end-recording-button';
    button.innerHTML = '結束';
    document.body.appendChild(button);

    // 設置全局變數以追蹤按鈕點擊狀態
    window.scheminEndRecordingClicked = false;

    button.addEventListener('click', function() {
        console.log('結束錄製按鈕被點擊');
        window.scheminEndRecordingClicked = true;
        
        // 禁用按鈕避免重複點擊
        button.disabled = true;
        button.style.backgroundColor = '#888';
        button.style.cursor = 'not-allowed';
    });
    """
    driver.execute_script(script)
    
    # 設置按鈕點擊事件的回調
    if on_click_callback:
        # 當按鈕被點擊時，會執行回調函數
        driver.execute_script("""
        var originalEndRecording = window.scheminEndRecordingClicked;
        
        Object.defineProperty(window, 'scheminEndRecordingClicked', {
            get: function() { 
                return originalEndRecording; 
            },
            set: function(value) {
                originalEndRecording = value;
                if (value === true) {
                    // 按鈕被點擊時，透過 selenium 執行 python 回調
                    console.log('觸發結束事件回調');
                }
            }
        });
        """)
