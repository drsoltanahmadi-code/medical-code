import tkinter as tk
from tkinter import ttk, messagebox

class SettingWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("تنظیمات برنامه")
        self.geometry("400x300")
        tk.Label(self, text="ماژول تنظیمات فعال شد.").pack(pady=20)