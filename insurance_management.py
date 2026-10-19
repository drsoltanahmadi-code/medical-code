import tkinter as tk
from tkinter import ttk, messagebox

class InsuranceManagementWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("مدیریت بیمه")
        self.geometry("400x300")
        tk.Label(self, text="ماژول مدیریت بیمه فعال شد.").pack(pady=20)