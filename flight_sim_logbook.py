import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import pickle
from datetime import datetime, timedelta
import firebase_admin
from firebase_admin import credentials, initialize_app, db
import os
import requests
import zipfile
import io
import shutil
import sys

LATEST_RELEASE_URL = "https://api.github.com/repos/Grosey/Stansted-Flight-Simulator/releases/latest"
def check_for_updates(current_version):
    response = requests.get(LATEST_RELEASE_URL)
    latest_release = response.json()
    latest_version = latest_release["tag_name"]
    
    if latest_version > current_version:
        print("New version available:", latest_version)
        
        download_url = latest_release["zipball_url"]
        download_and_replace(download_url)
    else:
        print("No updates available")



def download_and_replace(url):
    response = requests.get(url)
    with zipfile.ZipFile(io.BytesIO(response.content)) as zfile:
        zfile.extractall("update_folder")

    # Get the current directory and its parent directory
    current_directory = os.path.dirname(os.path.abspath(sys.argv[0]))
    parent_directory = os.path.dirname(current_directory)

    # Replace the current files with the updated files
    for root, dirs, files in os.walk("update_folder"):
        for file in files:
            updated_file_path = os.path.join(root, file)
            current_file_path = os.path.abspath(updated_file_path.replace("update_folder", current_directory).lstrip(os.path.sep))
            
            # Check if the current file path exists, then remove it
            if os.path.exists(current_file_path):
                os.remove(current_file_path)
            
            # Create directories if they don't exist
            os.makedirs(os.path.dirname(current_file_path), exist_ok=True)
            
            # Move the updated file to the current file path
            shutil.move(updated_file_path, current_file_path)
    
    # Remove the update_folder after updating
    shutil.rmtree("update_folder")

    # Get the latest version number from the GitHub API
    response = requests.get(LATEST_RELEASE_URL)
    latest_release = response.json()
    latest_version = latest_release["tag_name"]

    # Rename the current folder to the latest version
    new_directory = os.path.join(parent_directory, f"Stansted-Flight-Simulator-{latest_version}")
    os.rename(current_directory, new_directory)

    print("Update completed")

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

cred = credentials.Certificate('stansted-flight-simulator-log-firebase-adminsdk-jxh61-4fb61497f6.json')  # Replace with the path to your JSON file
firebase_admin.initialize_app(cred, {
    'databaseURL': 'https://stansted-flight-simulator-log-default-rtdb.europe-west1.firebasedatabase.app/'  # Use your Realtime Database URL
})

class AddLogDialog(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.title("Add Log")
        
        self.log_data = {}

        self.fields = [
            ("date", "Select Date (DD-MM-YYYY):"),
            ("captain", "Enter Captain Name:"),
            ("journey_from", "Enter Departure Location:"),
            ("journey_to", "Enter Arrival Location:"),
            ("depart", "Enter Departure Time (HH:MM):"),
            ("arrival", "Enter Arrival Time (HH:MM):"),
            ("total_time", "Enter Total Time (HH:MM):"),
            ("remarks", "Enter Remarks:"),
        ]

        self.entries = {}

        for field, label_text in self.fields:
            label = tk.Label(self, text=label_text)
            label.pack(pady=5)
            entry = tk.Entry(self)
            entry.pack(pady=5)
            self.entries[field] = entry

        submit_button = tk.Button(self, text="Submit", command=self.submit)
        submit_button.pack(pady=5)

    def submit(self):
        for field, entry in self.entries.items():
            self.log_data[field] = entry.get()
        self.destroy()

class LogBook:
    def __init__(self, master):
        
        # Get a reference to the logs in the Firebase Realtime Database
        self.logs_ref = db.reference('logs')
        
        self.master = master
        self.master.title("Stansted Flight Simulator Log Book - Version " + CURRENT_VERSION)
        self.master.iconbitmap('thumbnail_cf23fcb6.ico')
        self.logs = []
        self.load_logs()

        self.log_listbox = tk.Listbox(self.master, width=150, height=20)
        self.log_listbox.pack(padx=10, pady=10)

        self.update_listbox()

        self.add_button = tk.Button(self.master, text="Add Log", command=self.add_log)
        self.add_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(self.master, text="Delete Log", command=self.delete_log)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # Add the exit button
        self.exit_button = tk.Button(self.master, text="Exit", command=self.master.destroy)
        self.exit_button.pack(side=tk.RIGHT, padx=5, pady=10)

        

    def load_logs(self):
        logs_ref = db.reference('/logs')
        logs_data = logs_ref.get()
        if logs_data:
            self.logs = []
            for log in logs_data:
                log["date"] = datetime.strptime(log["date"], "%d-%m-%Y")
                self.logs.append(log)
        else:
            self.logs = []



    def save_logs(self):
        logs_to_save = []
        for log in self.logs:
            new_log = log.copy()
            new_log["date"] = log["date"].strftime("%d-%m-%Y")
            logs_to_save.append(new_log)
            
        self.logs_ref.set({i: log for i, log in enumerate(logs_to_save)})



    def update_listbox(self):
        self.log_listbox.delete(0, tk.END)
        for log in self.logs:
            formatted_date = log["date"].strftime("%d-%m-%Y")
            log_text = f"Date: {formatted_date} | Captain: {log['captain']} | Journey: {log['journey_from']} to {log['journey_to']} | Depart: {log['depart']} | Arrival: {log['arrival']} | Total Time: {log['total_time']} | Remarks: {log['remarks']}"
            self.log_listbox.insert(tk.END, log_text)





    def add_log(self):
        add_log_dialog = AddLogDialog(self.master)
        self.master.wait_window(add_log_dialog)

        log_data = add_log_dialog.log_data
        if all(value for key, value in log_data.items() if key != "remarks"):
            log_data["date"] = datetime.strptime(log_data["date"], "%d-%m-%Y")
            self.logs.append(log_data)
            self.update_listbox()
            self.save_logs()

    def edit_log(self):
        selected_index = self.log_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Warning", "Please select a log to edit.")
            return

        old_log = self.logs[selected_index[0]]
        for key, value in old_log.items():
            new_value = tk.simpledialog.askstring("Edit Log", f"Edit {key}:", initialvalue=value)
            if new_value:
                old_log[key] = new_value
            else:
                return

        self.update_listbox()
        self.save_logs()

    def delete_log(self):
        selected_index = self.log_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Warning", "Please select a log to delete.")
            return

        self.logs.pop(selected_index[0])
        self.update_listbox()
        self.save_logs()

if __name__ == "__main__":
    CURRENT_VERSION = "v1.0.5"
    check_for_updates(CURRENT_VERSION)
    
    root = tk.Tk()
    LogBook(root)
    root.mainloop()
