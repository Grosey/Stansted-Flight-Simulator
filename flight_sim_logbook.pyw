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
from PIL import Image, ImageDraw, ImageFont
from tkcalendar import DateEntry
import re
import requests.exceptions


def is_valid_time(time_str):
    pattern = re.compile("^(0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]$")
    return bool(pattern.match(time_str))

LATEST_RELEASE_URL = "https://api.github.com/repos/Grosey/Stansted-Flight-Simulator/releases/latest"
def check_for_updates(current_version):
    try:
        response = requests.get(LATEST_RELEASE_URL)
    except requests.exceptions.RequestException:
        messagebox.showwarning("Network Error", "Unable to check for updates. Please check your network connection and try again.")
        return
    latest_release = response.json()
    latest_version = latest_release["tag_name"]
    
    if latest_version > current_version:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showerror(
            "Update Required",
            f"A new version is available: {latest_version}. Please update to the latest version before using the application."
        )
        root.destroy()
        sys.exit(0)

    elif latest_version < current_version:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        messagebox.showerror(
            "This version is not available yet",
            f"This version is not available yet: {current_version}. Please continue to use {latest_version}."
        )
        root.destroy()
        sys.exit(0)
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


def create_certificate(name, font_path="arial.ttf", template_path="certificate blank.jpg"):
    # Open the certificate template
    certificate = Image.open(template_path)

    # Load the font with a size of 60 (or any desired size)
    font = ImageFont.truetype(font_path, 100)

    # Create an ImageDraw object
    draw = ImageDraw.Draw(certificate)

    # Calculate the bounding box of the name text
    text_bbox = draw.textbbox((0, 0), name, font)
    name_width, name_height = text_bbox[2], text_bbox[3]

    # Get the width and height of the certificate
    certificate_width, certificate_height = certificate.size

    # Calculate the position to center the name within the certificate
    x = (certificate_width - name_width) // 2
    y = (certificate_height - name_height) // 2

    # Move the text down as needed
    y = y+40

    # Draw the name on the certificate
    draw.text((x, y), name, font=font, fill=(0, 0, 0))

    # Determine the user's Pictures folder path
    pictures_folder = os.path.expanduser("~/Pictures")

    # Save the certificate with the name in the Pictures folder
    certificate_path = os.path.join(pictures_folder, f"certificate_{name}.png")
    certificate.save(certificate_path)

    # Open the image using the default image viewer, which usually provides a print option
    os.system(f'start {certificate_path}')


class AddLogDialog(tk.Toplevel):
    def __init__(self, parent):
        tk.Toplevel.__init__(self, parent)
        self.title("Add Log")
        self.geometry("500x700")  # Adjust the width and height as needed

        
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

        self.captain_options = ['HG', 'JG']

        for index, (field, label_text) in enumerate(self.fields):
            label = tk.Label(self, text=label_text)
            label.pack(pady=5)
            if field == "date":
                entry = DateEntry(self, date_pattern='dd-mm-yyyy')
            elif field == "captain":
                entry = ttk.Combobox(self, values=self.captain_options, state="readonly")
                entry.set(self.captain_options[0])
            else:
                entry = tk.Entry(self)
            entry.pack(pady=5)
            self.entries[field] = entry


        submit_button = tk.Button(self, text="Submit", command=self.submit)
        submit_button.pack(pady=5)

    def submit(self):
        try:
            for field, entry in self.entries.items():
                if field == "date":
                    self.log_data[field] = entry.get_date().strftime("%d-%m-%Y")
                else:
                    value = entry.get()
                    if field in ["depart", "arrival"]:
                        if not is_valid_time(value):
                            messagebox.showwarning("Invalid Time", f"Please enter a valid time for {field}.")
                            return
                    self.log_data[field] = value
        except ValueError:
            messagebox.showwarning("Invalid Date", "Please enter a valid date.")
            return
        self.destroy()

class EditLogDialog(AddLogDialog):
    def __init__(self, parent, log):
        self.log = log
        super().__init__(parent)
        self.update_fields()


    def submit(self):
        try:
            for field, entry in self.entries.items():
                if field == "date":
                    self.log_data[field] = entry.get_date().strftime("%d-%m-%Y")
                else:
                    value = entry.get()
                    if field in ["depart", "arrival"]:
                        if not is_valid_time(value):
                            messagebox.showwarning("Invalid Time", f"Please enter a valid time for {field}.")
                            return
                    self.log_data[field] = value
        except ValueError:
            messagebox.showwarning("Invalid Date", "Please enter a valid date.")
            return
        self.destroy()

    def update_fields(self):
        for field, entry in self.entries.items():
            if field == "date":
                date_str = self.log[field].strftime("%d-%m-%Y")
                entry.set_date(date_str)
            else:
                entry.delete(0, tk.END)
                entry.insert(0, self.log[field])

        self.title("Edit Log")

    def display(self):
        self.update_fields()
        super().display()


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

        self.edit_button = tk.Button(self.master, text="Edit Log", command=self.edit_log)
        self.edit_button.pack(side=tk.LEFT, padx=5)

        self.delete_button = tk.Button(self.master, text="Delete Log", command=self.delete_log)
        self.delete_button.pack(side=tk.LEFT, padx=5)

        # Add the exit button
        self.exit_button = tk.Button(self.master, text="Exit", command=self.master.destroy)
        self.exit_button.pack(side=tk.RIGHT, padx=5, pady=10)

        self.certificate_button = tk.Button(self.master, text="Create Certificate", command=self.create_certificate_dialog)
        self.certificate_button.pack(side=tk.LEFT, padx=5, pady=10)

    def create_certificate_dialog(self):
        name = simpledialog.askstring("Certificate Name", "Enter the name for the certificate:")
        if name:
            create_certificate(name)

    def load_logs(self):
        try:
            logs_ref = db.reference('/logs')
            logs_data = logs_ref.get()
        except Exception as e:
            messagebox.showwarning("Network Error", "Unable to load logs. Please check your network connection and try again.")
            return
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
            
        try:
            self.logs_ref.set({i: log for i, log in enumerate(logs_to_save)})
        except Exception as e:
            messagebox.showwarning("Network Error", "Unable to save logs. Please check your network connection and try again.")
            return




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

        log_to_edit = self.logs[selected_index[0]]
        edit_log_dialog = EditLogDialog(self.master, log_to_edit)
        self.master.wait_window(edit_log_dialog)

        updated_log_data = edit_log_dialog.log_data
        if all(value for key, value in updated_log_data.items() if key != "remarks"):
            updated_log_data["date"] = datetime.strptime(updated_log_data["date"], "%d-%m-%Y")
            self.logs[selected_index[0]] = updated_log_data
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
    CURRENT_VERSION = "v1.1.0"
    check_for_updates(CURRENT_VERSION)
    
    root = tk.Tk()
    LogBook(root)
    root.mainloop()
