import tkinter as tk
from tkinter import ttk, messagebox
import database

class PatientManagementWindow(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.title("مدیریت بیماران")
        self.geometry("600x400")
        self.conn = database.create_connection()
        tk.Label(self, text="ماژول مدیریت بیماران فعال شد.").pack(pady=20)