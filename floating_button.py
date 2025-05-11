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
    }
    
    #schemind-saving-message {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0,0,0,0.7);
        color: white;
        padding: 20px;
        border-radius: 5px;
        z-index: 10001;
        font-size: 18px;
        display: none;
    }
    `;
    document.head.appendChild(styleElement);
    
    // 添加儲存中訊息
    var savingMsg = document.createElement('div');
    savingMsg.id = 'schemind-saving-message';
    savingMsg.textContent = '正在儲存操作記錄...';
    document.body.appendChild(savingMsg);
    
    var button = document.createElement('button');
    button.id = 'schemind-end-recording-button';
    button.textContent = '結束';
    document.body.appendChild(button);
    
    // 添加點擊事件
    button.addEventListener('click', function() {
        // 設置一個標記，讓 Python 代碼知道按鈕被點擊了
        window.scheminEndRecordingClicked = true;
        
        // 顯示儲存中訊息
        document.getElementById('schemind-saving-message').style.display = 'block';
        
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
        # ActionRecorder 會監聽並檢查結束按鈕的點擊事件
        pass
