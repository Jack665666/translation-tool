import tkinter as tk
from PIL import Image, ImageGrab, ImageEnhance, ImageFilter
import pytesseract
from deep_translator import GoogleTranslator
import pyautogui
import os

# 設定 Tesseract-OCR 的路徑
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

# 建立翻譯器（繁體中文）
try:
    translator = GoogleTranslator(source='auto', target='zh-TW')
except Exception as e:
    print(f"翻譯器初始化失敗: {str(e)}")
    exit(1)

# 滑鼠框選變數
start_x, start_y = None, None
drawing = False
rect = None
selection_mode = False

# 建立 GUI
root = tk.Tk()
root.title("日文框選翻譯工具")
root.geometry("450x350")

# 建立透明框選視窗
overlay = tk.Toplevel(root)
overlay.attributes("-fullscreen", True)
overlay.attributes("-alpha", 0.3)
overlay.attributes("-topmost", True)
canvas = tk.Canvas(overlay, bg="gray", highlightthickness=0)
canvas.pack(fill="both", expand=True)
overlay.withdraw()

# 啟動框選模式
def start_selection_mode():
    global selection_mode
    if not selection_mode:
        selection_mode = True
        status_label.config(text="請框選要識別的文字區域")
        overlay.deiconify()
        overlay.bind("<Button-1>", start_drawing)
        overlay.bind("<B1-Motion>", update_selection)
        overlay.bind("<ButtonRelease-1>", end_drawing)

# 開始框選
def start_drawing(event):
    global start_x, start_y, drawing, rect
    start_x, start_y = pyautogui.position()
    drawing = True
    if rect:
        canvas.delete(rect)
    rect = None

# 更新框選範圍
def update_selection(event):
    global rect
    current_x, current_y = pyautogui.position()
    if rect:
        canvas.delete(rect)
    rect = canvas.create_rectangle(start_x, start_y, current_x, current_y, outline="red", width=2)

# 結束框選
def end_drawing(event):
    global start_x, start_y, selection_mode
    end_x, end_y = pyautogui.position()
    selection_mode = False
    overlay.withdraw()
    if rect:
        canvas.delete(rect)
    capture_text(start_x, start_y, end_x, end_y)

# **標點修正函數**
def clean_text(text):
    replacements = {
        '"': '「',   # 修正英文雙引號
        "'": "’",    # 修正單引號
        "`": "‘",    # 修正反引號
        ".": "。",   # 修正句號
        ",": "、",   # 修正逗號
        "!": "！",   # 修正驚嘆號
        "?": "？"    # 修正問號
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

# 影像處理與 OCR
def capture_text(x1, y1, x2, y2):
    left, top = min(x1, x2), min(y1, y2)
    right, bottom = max(x1, x2), max(y1, y2)

    # 防止選擇範圍過小
    if right - left < 10 or bottom - top < 10:
        status_label.config(text="框選範圍太小，請重新框選")
        return

    try:
        screenshot = ImageGrab.grab(bbox=(left, top, right, bottom))
        
        # **增強影像處理**
        screenshot = screenshot.resize((screenshot.width * 2, screenshot.height * 2), Image.LANCZOS)  # 放大影像提高解析度
        screenshot = screenshot.convert("L")  # 灰階
        enhancer = ImageEnhance.Contrast(screenshot)
        screenshot = enhancer.enhance(2.0)  # 增強對比度
        screenshot = screenshot.point(lambda x: 0 if x < 150 else 255)  # 二值化

        # **嘗試 OCR 文字識別**
        text = ""
        for psm_mode in [6, 11]:  # 6: 段落，11: 單行
            try:
                temp_text = pytesseract.image_to_string(screenshot, lang="jpn", config=f"--psm {psm_mode}")
                if temp_text.strip():
                    text = temp_text
                    break
            except Exception as e:
                print(f"OCR 失敗: {str(e)}")

        if not text.strip():
            status_label.config(text="無法識別文字，請選擇更清晰的範圍")
            return

        # **合併多行文字成一整句**
        lines = text.strip().split("\n")
        formatted_text = "".join([line.strip() for line in lines])  # **去掉換行，讓日文變成完整句子**
        
        # **修正標點**
        formatted_text = clean_text(formatted_text)

        # 顯示 OCR 結果
        if hasattr(root, 'text_display'):
            root.text_display.delete(1.0, tk.END)
        else:
            root.text_display = tk.Text(root, height=10, width=40, bg="white", font=("Arial", 12))
            root.text_display.pack(pady=10)
        root.text_display.insert(tk.END, f"提取的日文:\n{formatted_text}\n")

        # **一次性翻譯整句**
        try:
            translated_text = translator.translate(formatted_text)
            result_label.config(text=f"翻譯結果：\n{translated_text}")
        except Exception as e:
            result_label.config(text=f"翻譯失敗: {str(e)}")

    except Exception as e:
        status_label.config(text=f"發生錯誤: {str(e)}")

# **建立 UI 元件**
start_button = tk.Button(root, text="開始框選", command=start_selection_mode)
start_button.pack(pady=10)

status_label = tk.Label(root, text="請框選要識別的文字區域")
status_label.pack(pady=10)

result_label = tk.Label(root, text="翻譯結果會顯示在這裡")
result_label.pack(pady=10)

# **啟動主迴圈**
try:
    root.mainloop()
except Exception as e:
    print(f"主迴圈失敗: {str(e)}")
