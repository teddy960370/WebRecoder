from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def add_task_dialog(driver):
    """
    在瀏覽器上添加任務說明輸入對話框，讓使用者輸入任務描述。
    返回使用者輸入的任務描述。
    """
    # 插入 HTML 對話框
    script = """
    var overlay = document.createElement('div');
    overlay.id = 'schemind-task-overlay';
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
    overlay.style.zIndex = '10000';
    overlay.style.display = 'flex';
    overlay.style.justifyContent = 'center';
    overlay.style.alignItems = 'center';
    
    var dialog = document.createElement('div');
    dialog.id = 'schemind-task-dialog';
    dialog.style.backgroundColor = 'white';
    dialog.style.padding = '30px';
    dialog.style.borderRadius = '10px';
    dialog.style.boxShadow = '0 4px 8px rgba(0, 0, 0, 0.2)';
    dialog.style.width = '500px';
    dialog.style.maxWidth = '80%';
    dialog.style.display = 'flex';
    dialog.style.flexDirection = 'column';
    dialog.style.gap = '20px';
    
    var title = document.createElement('h2');
    title.textContent = '請輸入任務說明';
    title.style.margin = '0';
    title.style.color = '#333';
    
    var textarea = document.createElement('textarea');
    textarea.id = 'schemind-task-input';
    textarea.placeholder = '請描述您要執行的操作任務...';
    textarea.style.width = '100%';
    textarea.style.height = '100px';
    textarea.style.padding = '10px';
    textarea.style.border = '1px solid #ddd';
    textarea.style.borderRadius = '5px';
    textarea.style.resize = 'vertical';
    textarea.style.boxSizing = 'border-box';
    textarea.style.fontSize = '16px';
    
    var button = document.createElement('button');
    button.id = 'schemind-task-submit';
    button.textContent = '開始操作';
    button.style.padding = '10px 20px';
    button.style.backgroundColor = '#4CAF50';
    button.style.color = 'white';
    button.style.border = 'none';
    button.style.borderRadius = '5px';
    button.style.cursor = 'pointer';
    button.style.fontSize = '16px';
    button.style.alignSelf = 'flex-end';
    
    dialog.appendChild(title);
    dialog.appendChild(textarea);
    dialog.appendChild(button);
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    
    // 自動聚焦到輸入框
    textarea.focus();
    
    window.taskSubmitted = false;
    window.taskDescription = '';
    
    button.addEventListener('click', function() {
        window.taskDescription = document.getElementById('schemind-task-input').value;
        window.taskSubmitted = true;
        document.body.removeChild(overlay);
    });
    """
    driver.execute_script(script)
    
    # 等待使用者輸入並提交任務說明
    wait = WebDriverWait(driver, timeout=300)  # 等待最多5分鐘
    wait.until(lambda d: d.execute_script("return window.taskSubmitted === true;"))
    
    # 獲取使用者輸入的任務描述
    task_description = driver.execute_script("return window.taskDescription;")
    
    return task_description
