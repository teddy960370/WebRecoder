from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def add_task_dialog(driver , url=None , task_description=None):
    """
    在瀏覽器上添加任務說明輸入對話框，讓使用者輸入任務描述和網址。
    返回元組 (任務描述, 任務網址)。
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
    
    // 創建網址輸入欄位
    var urlLabel = document.createElement('label');
    urlLabel.textContent = '任務網址 (選填)';
    urlLabel.style.fontWeight = 'bold';
    urlLabel.style.marginBottom = '5px';
    urlLabel.style.color = '#333';
    
    var urlInput = document.createElement('input');
    urlInput.id = 'schemind-task-url';
    urlInput.type = 'url';
    urlInput.value = {MyUrl};
    urlInput.placeholder = '請輸入要瀏覽的網址 (例如: https://example.com)';
    urlInput.style.width = '100%';
    urlInput.style.padding = '10px';
    urlInput.style.border = '1px solid #ddd';
    urlInput.style.borderRadius = '5px';
    urlInput.style.boxSizing = 'border-box';
    urlInput.style.fontSize = '16px';
    urlInput.style.marginBottom = '15px';
    
    var textareaLabel = document.createElement('label');
    textareaLabel.textContent = '任務描述';
    textareaLabel.style.fontWeight = 'bold';
    textareaLabel.style.marginBottom = '5px';
    textareaLabel.style.color = '#333';
    
    var textarea = document.createElement('textarea');
    textarea.id = 'schemind-task-input';
    textarea.placeholder = '請描述您要執行的操作任務...';
    textarea.value = {MyTaskDescription};
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
    dialog.appendChild(urlLabel);
    dialog.appendChild(urlInput);
    dialog.appendChild(textareaLabel);
    dialog.appendChild(textarea);
    dialog.appendChild(button);
    overlay.appendChild(dialog);
    document.body.appendChild(overlay);
    
    // 自動聚焦到網址輸入框
    urlInput.focus();
    
    window.taskSubmitted = false;
    window.taskDescription = '';
    window.taskUrl = '';
    
    button.addEventListener('click', function() {
        window.taskDescription = document.getElementById('schemind-task-input').value;
        window.taskUrl = document.getElementById('schemind-task-url').value;
        window.taskSubmitted = true;
        document.body.removeChild(overlay);
    });
    """
    script = script.replace("{MyUrl}", f'"{url}"' if url else '""')
    script = script.replace("{MyTaskDescription}", f'"{task_description}"' if task_description else '""')
    driver.execute_script(script)
    
    # 等待使用者輸入並提交任務說明
    wait = WebDriverWait(driver, timeout=300)  # 等待最多5分鐘
    wait.until(lambda d: d.execute_script("return window.taskSubmitted === true;"))
    
    # 獲取使用者輸入的任務描述和網址
    task_description = driver.execute_script("return window.taskDescription;")
    task_url = driver.execute_script("return window.taskUrl;")
    
    # 返回任務描述和網址
    return task_description, task_url
