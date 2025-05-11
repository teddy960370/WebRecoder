import os
import time
import json
import logging
from datetime import datetime

# 設置日誌格式
def setup_logging():
    """設置日誌記錄器"""
    log_dir = "./logs"
    os.makedirs(log_dir, exist_ok=True)
    
    log_filename = f"webrecorder_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    log_path = os.path.join(log_dir, log_filename)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_path, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger('webrecorder')

# 保存JSON資料到檔案
def save_json_data(data, filename):
    """將資料儲存為JSON檔案"""
    try:
        directory = os.path.dirname(filename)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
            
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"無法保存JSON檔案: {str(e)}")
        return False

# 輔助函數：嘗試獲取元素的可讀描述
def get_element_description(element, driver):
    """嘗試獲取元素的可讀描述"""
    try:
        # 嘗試不同的屬性以獲取最佳描述
        text = element.text.strip() if element.text else None
        aria_label = element.get_attribute("aria-label")
        title = element.get_attribute("title")
        alt = element.get_attribute("alt")
        placeholder = element.get_attribute("placeholder")
        
        # 返回第一個非空值
        for value in [text, aria_label, title, alt, placeholder]:
            if value:
                return value
                
        # 如果沒有找到描述性文字，使用標籤+類別或ID
        tag_name = element.tag_name
        element_id = element.get_attribute("id")
        element_class = element.get_attribute("class")
        
        if element_id:
            return f"{tag_name}#{element_id}"
        elif element_class:
            return f"{tag_name}.{element_class}"
        else:
            return f"{tag_name}-element"
            
    except:
        return "未知元素"

# 檢測瀏覽器是否仍在運行
def is_browser_alive(driver):
    """檢查瀏覽器是否仍在運行"""
    try:
        # 簡單的檢查方法是嘗試獲取當前URL
        _ = driver.current_url
        return True
    except:
        return False
