import tkinter as tk
from data.data_manager import DataManager

class SubmitDataApp(tk.Tk):
    def __init__(self, reason: str):
        super().__init__()
        self._saved = False

        app_width = 400
        app_height = 200

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = int((screen_width/2) - (app_width/2))
        y = int((screen_height/2) - (app_height/2))
    
        self.geometry(f"{app_width}x{app_height}+{x}+{y}")
        self.title("Inbound Notifier by Pogo")
        self.iconbitmap("src/assets/logo.ico")
        self.resizable(False, False)

        self.label = tk.Label(self, text=reason, wraplength=300, foreground="red")
        self.label.grid(column=0, row=0)

        self.entry = tk.Entry(self, bg="white", width=50)
        self.entry.grid(column=0, row=1, pady=(50,0))

        self.button = tk.Button(self, text="save", width=10, command=self._store_to_db)
        self.button.grid(column=0, row=2, pady=(20,0))

        self.warn_label = tk.Label(self, text="Your cookie will be validated after saving.")
        self.warn_label.grid(column=0, row=3, pady=(10,0))

        self.grid_columnconfigure(0, weight=1)

    def _store_to_db(self):
        DataManager.store_data(key=".ROBLOSECURITY", value=self.entry.get())

        self._saved = True
        self.destroy()

    def enable_app(self) -> bool:
        self.mainloop()

        return self._saved