import os, sys, pyautogui, time, cv2, threading, keyboard, pygame
import numpy as np
import tkinter as tk
from tkinter import messagebox, simpledialog
from PIL import ImageGrab

pygame.mixer.init()

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def load_images():
    rock_images = []
    for i in range(1, 4):
        filename = resource_path(f'rock{i}.png')
        if os.path.exists(filename):
            rock_image = cv2.imread(filename, cv2.IMREAD_GRAYSCALE)
            rock_images.append(rock_image)
            print(f"Изображение {filename} загружено")
        else:
            print(f"Файл {filename} не найден. Пожалуйста, загрузите изображение.")

    press_image_path = resource_path('press.png')
    if os.path.exists(press_image_path):
        press_image = cv2.imread(press_image_path, cv2.IMREAD_GRAYSCALE)
        print(f"Изображение {press_image_path} загружено")
    else:
        press_image = None
        print(f"Файл {press_image_path} не найден. Пожалуйста, загрузите изображение.")

    success_image_path = resource_path('success.png')
    if os.path.exists(success_image_path):
        success_image = cv2.imread(success_image_path, cv2.IMREAD_GRAYSCALE)
        print(f"Изображение {success_image_path} загружено")
    else:
        success_image = None
        print(f"Файл {success_image_path} не найден. Пожалуйста, загрузите изображение.")

    return rock_images, press_image, success_image

def hold_key(key, hold_time):
    start_time = time.time()
    while time.time() - start_time < hold_time:
        keyboard.press(key)
        time.sleep(0.1)
    keyboard.release(key)

def find_and_click(rock_images, press_image, success_image, running_flag, status_label):
    while running_flag.is_set():
        screenshot = ImageGrab.grab()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_BGR2GRAY)

        for rock_image in rock_images:
            res = cv2.matchTemplate(screenshot, rock_image, cv2.TM_CCOEFF_NORMED)
            threshold = 0.75
            loc = np.where(res >= threshold)

            for pt in zip(*loc[::-1]):
                rock_center = (pt[0] + rock_image.shape[1] // 2, pt[1] + rock_image.shape[0] // 2)

                if not running_flag.is_set():
                    return

                pyautogui.click(rock_center)
                break

        if press_image is not None:
            res = cv2.matchTemplate(screenshot, press_image, cv2.TM_CCOEFF_NORMED)
            threshold = 0.7
            loc = np.where(res >= threshold)
            if len(loc[0]) > 0:
                hold_key('e', 1.1)

        if success_image is not None:
            found_success = False
            for threshold in [0.9, 0.8, 0.7]:  # Try different thresholds
                res = cv2.matchTemplate(screenshot, success_image, cv2.TM_CCOEFF_NORMED)
                loc = np.where(res >= threshold)
                if len(loc[0]) > 0:
                    found_success = True
                    break

            if found_success:
                hold_key('s', 0.95)
                hold_key('w', 0.38)
                time.sleep(1.5)
                
def play_sound():
    pygame.mixer.music.load(resource_path('stop_start.mp3'))
    pygame.mixer.music.play()

def start_script(status_label):
    global running_flag
    if not rock_images:
        messagebox.showerror("Ошибка", "Не удалось загрузить изображения камней!")
        return
    if running_flag.is_set():
        print("Шахтер уже запущен!")
        return
    running_flag.set()
    play_sound()
    threading.Thread(target=find_and_click,
                     args=(rock_images, press_image, success_image, running_flag, status_label)).start()
    status_label.config(text="Сейчас: Старт")

def stop_script(status_label):
    global running_flag
    if not running_flag.is_set():
        print("Шахтер уже остановлен!")
        return
    running_flag.clear()
    play_sound()
    status_label.config(text="Сейчас: Стоп")

def setup_hotkeys(start_key, stop_key, start_label, stop_label):
    keyboard.unhook_all()
    keyboard.add_hotkey(start_key, lambda: start_script(status_label))
    keyboard.add_hotkey(stop_key, lambda: stop_script(status_label))
    current_hotkeys['start'] = start_key
    current_hotkeys['stop'] = stop_key
    update_hotkey_labels(start_label, stop_label)
    print(f"Горячие клавиши назначены: '{start_key}' для старта, '{stop_key}' для остановки")

def ask_hotkey(prompt, parent):
    hotkey = None
    while not hotkey:
        result = simpledialog.askstring("Изменение горячих клавиш", prompt)
        if not result:
            return None
        hotkey = result.strip().lower()
        if not hotkey:
            messagebox.showwarning("Пустой ввод", "Вы не ввели клавишу. Пожалуйста, попробуйте еще раз.")
        elif len(hotkey) > 1:
            messagebox.showwarning("Неверный ввод", "Введите только одну клавишу.")
            hotkey = None
        else:
            confirm = messagebox.askyesno("Подтвердить горячую клавишу", f"Вы выбрали {hotkey}. Подтверждаете?")
            if not confirm:
                hotkey = None
    return hotkey

def change_hotkeys(start_label, stop_label):
    global current_hotkeys
    start_key = ask_hotkey("Нажмите новую горячую клавишу для старта:", root)
    if not start_key:
        return
    stop_key = ask_hotkey("Нажмите новую горячую клавишу для остановки:", root)
    if not stop_key:
        return
    setup_hotkeys(start_key, stop_key, start_label, stop_label)
    update_hotkey_labels(start_label, stop_label)
    messagebox.showinfo("Горячие клавиши обновлены", f"Новые горячие клавиши:\nСтарт: {start_key}\nСтоп: {stop_key}")

def update_hotkey_labels(start_label, stop_label):
    start_label.config(text=f"Старт: {current_hotkeys['start']}")
    stop_label.config(text=f"Стоп: {current_hotkeys['stop']}")

root = tk.Tk()
root.title("Я КАМЕНЩИК")
root.geometry("250x170")
root.configure(bg="#333333")

button_frame = tk.Frame(root, bg="#333333", highlightthickness=0, highlightbackground='white')
button_frame.pack(pady=10)

start_button = tk.Button(button_frame, text="Старт", command=lambda: start_script(status_label), bg="#4CAF50",
                         fg="white", font=("Arial", 12, "bold"))
start_button.pack(side=tk.LEFT, padx=10)

stop_button = tk.Button(button_frame, text="Стоп", command=lambda: stop_script(status_label), bg="#FF5733", fg="white",
                        font=("Arial", 12, "bold"))
stop_button.pack(side=tk.LEFT, padx=10)

menu = tk.Menu(root)
root.config(menu=menu)
settings_menu = tk.Menu(menu, tearoff=0)
menu.add_cascade(label="Настройки", menu=settings_menu)
settings_menu.add_command(label="Изменить горячие клавиши", command=lambda: change_hotkeys(start_label, stop_label))

current_hotkeys = {
    "start": "f",
    "stop": "g"
}

status_label = tk.Label(root, text="Сейчас: Стоп", bg="#333333", fg="white", font=("Arial", 10, "bold"))
status_label.pack(pady=15)

start_label = tk.Label(root, text=f"Старт: {current_hotkeys['start']}", bg="#333333", fg="white",
                       font=("Arial", 10, "bold"))
start_label.pack()

stop_label = tk.Label(root, text=f"Стоп: {current_hotkeys['stop']}", bg="#333333", fg="white",
                      font=("Arial", 10, "bold"))
stop_label.pack()

rock_images, press_image, success_image = load_images()
running_flag = threading.Event()

setup_hotkeys(current_hotkeys['start'], current_hotkeys['stop'], start_label, stop_label)

root.mainloop()

while True:
    if not running_flag.is_set():
        break