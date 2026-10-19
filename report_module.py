import tkinter as tk
from tkinter import ttk, messagebox
import database

class ReportWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("گزارشات برنامه")
        self.geometry("600x400")
        tk.Label(self, text="ماژول گزارشات فعال شد.").pack(pady=20)