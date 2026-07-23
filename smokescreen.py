#Copyright (C) 2026  bellocado
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import json
import time
import psutil
import win32gui
import win32con
import win32process
import threading
import sys
import tkinter as tk
from tkinter import filedialog
import customtkinter as ctk
import keyboard
from PIL import Image
import pystray

COLOR_BG = "#1A1A1A"
COLOR_FRAME = "#282828"
COLOR_BTN = "#3A3A3A"
COLOR_BTN_HOVER = "#4A4A4A"
COLOR_BORDER = "#5A5A5A"
COLOR_TEXT = "#E0E0E0"
COLOR_GREEN = "#00FF66"
COLOR_RED = "#FF3333"

ctk.set_appearance_mode("Dark")

CONFIG_FILE = "panic_config.json"

class PanicButtonApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("SmokeScreen v1.0.2")
        self.geometry("460x370")
        self.resizable(False, False)
        self.configure(fg_color=COLOR_BG)
        
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(base_path, "icon.ico")
        
        try:
            self.iconbitmap(icon_path)
        except Exception as e:
            print(f"Could not load titlebar icon: {e}")

        self.game_path = tk.StringVar(value="Not Selected")
        self.study_path = tk.StringVar(value="Not Selected")
        self.panic_hotkey = "pause"
        self.restore_hotkey = "ctrl+shift+u"
        self.hidden_hwnd = None
        
        self.last_action_time = 0
        self.cooldown_delay = 1.0 

        self.tray_icon = None

        self.load_config()
        self.create_ui()
        self.start_hotkey_listeners()
        
        self.protocol('WM_DELETE_WINDOW', self.on_exit)

    def create_ui(self):
        font_title = ctk.CTkFont(family="Tahoma", size=14, weight="bold")
        font_regular = ctk.CTkFont(family="Tahoma", size=11)
        font_italic = ctk.CTkFont(family="Tahoma", size=10, slant="italic")

        title_label = ctk.CTkLabel(self, text="[ SmokeScreen - UTILITY CONSOLE ]", font=font_title, text_color=COLOR_TEXT)
        title_label.pack(pady=(8, 4))

        game_frame = ctk.CTkFrame(self, fg_color=COLOR_FRAME, border_color=COLOR_BORDER, border_width=1, corner_radius=0)
        game_frame.pack(pady=3, padx=10, fill="x")
        
        game_label = ctk.CTkLabel(game_frame, text="Target Game:", width=90, anchor="w", font=font_regular, text_color=COLOR_TEXT)
        game_label.pack(side="left", padx=6, pady=4)
        
        self.running_apps_dropdown = ctk.CTkComboBox(
            game_frame, values=["Scanning apps..."], width=210, font=font_regular,
            corner_radius=0, fg_color=COLOR_BG, border_color=COLOR_BORDER, border_width=1,
            button_color=COLOR_BTN, button_hover_color=COLOR_BTN_HOVER,
            command=self.on_game_dropdown_select
        )
        self.running_apps_dropdown.pack(side="left", padx=2)
        
        refresh_game_btn = ctk.CTkButton(
            game_frame, text="...", width=25, font=font_regular, command=self.populate_running_apps,
            corner_radius=0, fg_color=COLOR_BTN, hover_color=COLOR_BTN_HOVER, border_color=COLOR_BORDER, border_width=1
        )
        refresh_game_btn.pack(side="left", padx=1)

        browse_game_btn = ctk.CTkButton(
            game_frame, text="Browse", width=50, font=font_regular, command=self.browse_game,
            corner_radius=0, fg_color=COLOR_BTN, hover_color=COLOR_BTN_HOVER, border_color=COLOR_BORDER, border_width=1
        )
        browse_game_btn.pack(side="left", padx=2)

        study_frame = ctk.CTkFrame(self, fg_color=COLOR_FRAME, border_color=COLOR_BORDER, border_width=1, corner_radius=0)
        study_frame.pack(pady=3, padx=10, fill="x")
        
        study_label = ctk.CTkLabel(study_frame, text="Cover App:", width=90, anchor="w", font=font_regular, text_color=COLOR_TEXT)
        study_label.pack(side="left", padx=6, pady=4)
        
        self.cover_apps_dropdown = ctk.CTkComboBox(
            study_frame, values=["Scanning apps..."], width=210, font=font_regular,
            corner_radius=0, fg_color=COLOR_BG, border_color=COLOR_BORDER, border_width=1,
            button_color=COLOR_BTN, button_hover_color=COLOR_BTN_HOVER,
            command=self.on_cover_dropdown_select
        )
        self.cover_apps_dropdown.pack(side="left", padx=2)
        
        refresh_cover_btn = ctk.CTkButton(
            study_frame, text="...", width=25, font=font_regular, command=self.populate_running_apps,
            corner_radius=0, fg_color=COLOR_BTN, hover_color=COLOR_BTN_HOVER, border_color=COLOR_BORDER, border_width=1
        )
        refresh_cover_btn.pack(side="left", padx=1)
        
        study_btn = ctk.CTkButton(
            study_frame, text="Browse", width=50, font=font_regular, command=self.browse_study,
            corner_radius=0, fg_color=COLOR_BTN, hover_color=COLOR_BTN_HOVER, border_color=COLOR_BORDER, border_width=1
        )
        study_btn.pack(side="left", padx=2)

        self.selection_display = ctk.CTkLabel(self, text=f"Target: {os.path.basename(self.game_path.get())}", font=font_italic, text_color="#8A8A8A")
        self.selection_display.pack(pady=1)

        self.cover_display = ctk.CTkLabel(self, text=f"Cover: {os.path.basename(self.study_path.get())}", font=font_italic, text_color="#8A8A8A")
        self.cover_display.pack(pady=1)

        self.status_label = ctk.CTkLabel(self, text="SYSTEM STATUS: MONITORING...", font=font_regular, text_color=COLOR_GREEN)
        self.status_label.pack(pady=4)

        hide_tray_btn = ctk.CTkButton(
            self, text="HIDE TO SYSTEM TRAY", height=28, font=font_regular, command=self.hide_to_tray,
            corner_radius=0, fg_color="#1F4E43", hover_color="#2A6B5C", border_color=COLOR_BORDER, border_width=1
        )
        hide_tray_btn.pack(pady=2, fill="x", padx=40)

        save_btn = ctk.CTkButton(
            self, text="SAVE CONFIGURATION", height=28, font=font_regular, command=self.save_config,
            corner_radius=0, fg_color=COLOR_BTN, hover_color=COLOR_BTN_HOVER, border_color=COLOR_BORDER, border_width=1
        )
        save_btn.pack(pady=2, fill="x", padx=40)
        
        restore_info = ctk.CTkLabel(self, text="SECRET RECOVERY TRIGGER: CTRL + SHIFT + U", font=font_italic, text_color="#7A7A7A")
        restore_info.pack(pady=(4, 8))
        
        self.populate_running_apps()

    def populate_running_apps(self):
        app_list = []
        def enum_windows_proc(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    if proc.name().lower() not in ["explorer.exe", "svchost.exe", "taskmgr.exe"] and pid != os.getpid():
                        display_string = f"{proc.name()} ({win32gui.GetWindowText(hwnd)[:30]})"
                        if display_string not in app_list:
                            app_list.append(display_string)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass

        win32gui.EnumWindows(enum_windows_proc, None)
        sorted_apps = sorted(app_list, key=lambda s: s.lower())
        
        if sorted_apps:
            self.running_apps_dropdown.configure(values=sorted_apps)
            self.cover_apps_dropdown.configure(values=sorted_apps)
        else:
            self.running_apps_dropdown.configure(values=["No apps detected"])
            self.cover_apps_dropdown.configure(values=["No apps detected"])

    def on_game_dropdown_select(self, choice):
        if "(" in choice:
            exe_name = choice.split(" (")[0]
            self.game_path.set(exe_name)
            self.selection_display.configure(text=f"Target: {exe_name}")

    def on_cover_dropdown_select(self, choice):
        if "(" in choice:
            exe_name = choice.split(" (")[0]
            full_path = exe_name
            for proc in psutil.process_iter(['name', 'exe']):
                if proc.info['name'] and proc.info['name'].lower() == exe_name.lower() and proc.info['exe']:
                    full_path = proc.info['exe']
                    break
            self.study_path.set(full_path)
            self.cover_display.configure(text=f"Cover: {exe_name}")

    def browse_game(self):
        filename = filedialog.askopenfilename(title="Select Game Executable", filetypes=[("Executable Files", "*.exe")])
        if filename: 
            self.game_path.set(filename)
            self.selection_display.configure(text=f"Target: {os.path.basename(filename)}")

    def browse_study(self):
        filename = filedialog.askopenfilename(title="Select cover app", filetypes=[("All Files", "*.*")])
        if filename: 
            self.study_path.set(filename)
            self.cover_display.configure(text=f"Cover: {os.path.basename(filename)}")

    def save_config(self):
        config = {"game_path": self.game_path.get(), "study_path": self.study_path.get()}
        with open(CONFIG_FILE, "w") as f: json.dump(config, f)
        self.status_label.configure(text="SETTINGS SAVED SUCCESSFUL", text_color=COLOR_GREEN)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    g_path = config.get("game_path", "Not Selected")
                    s_path = config.get("study_path", "Not Selected")
                    self.game_path.set(g_path)
                    self.study_path.set(s_path)

                    self.selection_display.configure(text=f"Target: {os.path.basename(g_path)}")
                    self.cover_display.configure(text=f"Cover: {os.path.basename(s_path)}")
            except Exception: pass

    def find_specific_game_hwnd(self, target_exe):
        target_hwnds = []
        def enum_cb(hwnd, extra):
            if win32gui.IsWindowVisible(hwnd):
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                try:
                    proc = psutil.Process(pid)
                    if proc.name().lower() == target_exe.lower():
                        target_hwnds.append(hwnd)
                except:
                    pass
        win32gui.EnumWindows(enum_cb, None)
        return target_hwnds[0] if target_hwnds else None

    def panic_action(self):
        current_time = time.time()
        if current_time - self.last_action_time < self.cooldown_delay:
            return
        
        game_target = os.path.basename(self.game_path.get()).lower()
        study_exe = self.study_path.get()

        if game_target != "not selected":
            target_hwnd = self.find_specific_game_hwnd(game_target)
            
            if target_hwnd and target_hwnd != self.winfo_id():
                try:
                    self.hidden_hwnd = target_hwnd
                    
                    win32gui.ShowWindow(self.hidden_hwnd, win32con.SW_SHOWMINNOACTIVE)
                    win32gui.ShowWindow(self.hidden_hwnd, win32con.SW_HIDE)
                    
                    style = win32gui.GetWindowLong(self.hidden_hwnd, win32con.GWL_EXSTYLE)
                    style = style & ~win32con.WS_EX_APPWINDOW
                    style = style | win32con.WS_EX_TOOLWINDOW
                    win32gui.SetWindowLong(self.hidden_hwnd, win32con.GWL_EXSTYLE, style)
                    
                    self.status_label.configure(text="ALERT: TARGET APP CONCEALED", text_color=COLOR_RED)
                    self.last_action_time = current_time
                except Exception as e:
                    print(f"Error hiding game: {e}")

        if study_exe != "Not Selected":
            try:
                exe_name = os.path.basename(study_exe)
                def find_and_focus_cover(hwnd, extra):
                    if win32gui.IsWindowVisible(hwnd):
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        try:
                            proc = psutil.Process(pid)
                            if proc.name().lower() == exe_name.lower():
                                if win32gui.IsIconic(hwnd):
                                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                                win32gui.SetForegroundWindow(hwnd)
                        except: pass
                
                win32gui.EnumWindows(find_and_focus_cover, None)
                os.startfile(study_exe)
            except Exception:
                pass

    def restore_action(self):
        current_time = time.time()
        if current_time - self.last_action_time < self.cooldown_delay:
            return

        if self.hidden_hwnd and win32gui.IsWindow(self.hidden_hwnd):
            try:
                style = win32gui.GetWindowLong(self.hidden_hwnd, win32con.GWL_EXSTYLE)
                style = style | win32con.WS_EX_APPWINDOW
                style = style & ~win32con.WS_EX_TOOLWINDOW
                win32gui.SetWindowLong(self.hidden_hwnd, win32con.GWL_EXSTYLE, style)

                win32gui.ShowWindow(self.hidden_hwnd, win32con.SW_SHOW)
                win32gui.ShowWindow(self.hidden_hwnd, win32con.SW_RESTORE)

                keyboard.send("alt")
                win32gui.SetActiveWindow(self.hidden_hwnd)
                win32gui.SetForegroundWindow(self.hidden_hwnd)
                
                self.hidden_hwnd = None
                self.status_label.configure(text="SYSTEM STATUS: MONITORING...", text_color=COLOR_GREEN)
                self.last_action_time = current_time
                
            except Exception as e:
                print(f"Error restoring game: {e}")
                self.hidden_hwnd = None

    def start_hotkey_listeners(self):
        def listen():
            keyboard.add_hotkey(self.panic_hotkey, self.panic_action)
            keyboard.add_hotkey(self.restore_hotkey, self.restore_action)
            keyboard.wait()

        thread = threading.Thread(target=listen, daemon=True)
        thread.start()

    def generate_tray_image(self):
        base_path = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
        
        for img_name in ["medium.png", "icon.ico"]:
            try:
                return Image.open(os.path.join(base_path, img_name))
            except Exception:
                continue
                
        return Image.new('RGB', (64, 64), color='#1F4E43')

    def show_window(self):
        if self.tray_icon:
            self.tray_icon.stop()
            self.tray_icon = None
        self.deiconify()

    def hide_to_tray(self):
        self.withdraw()
        menu = (
            pystray.MenuItem('DECONCEAL CONSOLE', self.show_window, default=True),
            pystray.MenuItem('KILL PROCESS', self.on_exit)
        )
        self.tray_icon = pystray.Icon("SmokeScreen", self.generate_tray_image(), "SmokeScreen OS", menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def on_exit(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()

if __name__ == "__main__":
    import ctypes
    try:
        myappid = 'smokescreen.utility.stealthconsole.v1'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = PanicButtonApp()
    app.mainloop()
