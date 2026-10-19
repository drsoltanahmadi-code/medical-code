import tkinter as tk
from tkinter import ttk, messagebox
import database

class ServiceManagementWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("مدیریت خدمات")
        self.geometry("400x300")
        self.conn = database.create_connection()
        tk.Label(self, text="ماژول مدیریت خدمات فعال شد.").pack(pady=20)