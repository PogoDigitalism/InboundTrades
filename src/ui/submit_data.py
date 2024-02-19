import tkinter as tk

class SubmitDataApp(tk.Tk):
    def __init__(self, reason: str):
        super().__init__()

        self.title("Submit Cookie Interface")
        self.geometry("300x50")
        self.resizable(False, False)

        self.label = tk.Label(self, text=reason)
        self.label.place(relheight=0.33, relwidth=0.33, relx=0.5, rely=0, anchor="n")

    def enable_app(self):
        self.mainloop()

