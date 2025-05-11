# WebRecorder - 網頁操作錄製工具

這是一個基於 Selenium 的網頁操作錄製工具，能夠記錄使用者在瀏覽器中的各種操作，如點擊、輸入、滾動等，並將其保存為 JSON 格式的記錄檔。

## 功能特點

- 自動記錄使用者的點擊、輸入、滾動和頁面導航操作
- 防止頁面在新分頁中開啟，確保記錄的連續性
- 提供懸浮結束按鈕，方便結束錄製
- 記錄完整的元素描述資訊
- 儲存格式為結構化的 JSON 檔案

## 安裝方式

1. 確保已安裝 Python 3.7 或更新版本
2. 安裝依賴套件：`pip install -r requirements.txt`

## 使用方法

1. 執行主程式：`python web_action_recorder.py`
2. 在彈出的對話框中輸入任務描述
3. 開始在瀏覽器中進行操作
4. 點擊右下角的紅色「結束」按鈕完成錄製
5. 錄製的操作將被保存到 `./data` 目錄中

## 檔案結構

- `web_action_recorder.py`: 主程式檔案
- `action_recorder.py`: 操作記錄器實現
- `floating_button.py`: 懸浮結束按鈕實現
- `task_dialog.py`: 任務描述對話框實現
- `data/`: 保存錄製結果的目錄

## 錄製結果格式

```json
{
  "task_description": "使用者輸入的任務描述",
  "timestamp": "記錄時間",
  "actions": [
    {
      "type": "Click",
      "target": "點擊的元素描述",
      "element_details": {
        "詳細的元素屬性..."
      },
      "timestamp": 1686123456.789
    },
    // 其他操作...
  ]
}
```
