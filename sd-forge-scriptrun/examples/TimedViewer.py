import os
import sys
import time
import csv
import argparse
import gc
import random
import platform
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

CHECK_INTERVAL = 3
TRANSITION_DURATION = 3
IMAGE_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.bmp', '.gif']
PROTOCOL_FILE = 'displayed_images.csv'
VERSION_INFO = (
    "TimedViewer v1.0\n"
    "An open-source project from https://github.com/zeittresor/timedviewer\n"
    "Licensed under MIT License."
)

selected_directory = os.getcwd()
use_protocol = True
initialize_all = False
ignore_protocol = False
close_viewer_on_left_click = True
selected_effect = 'Fade'
waiting_for_new_images_message = True
check_interval_var = CHECK_INTERVAL
transition_duration_var = TRANSITION_DURATION
any_image_displayed = False
show_starfield = True
VIEWPATH_FILE = "viewpath.txt"

def get_image_files(directory):
    image_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if os.path.splitext(file)[1].lower() in IMAGE_EXTENSIONS:
                full_path = os.path.abspath(os.path.join(root, file))
                image_files.append(full_path)
    image_files.sort(key=lambda x: os.path.getmtime(x))
    return image_files

def load_displayed_images(protocol_path):
    displayed = set()
    if os.path.exists(protocol_path):
        try:
            with open(protocol_path, 'r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    if row:
                        displayed.add(row[0])
        except:
            pass
    return displayed

def save_displayed_image(protocol_path, image_path):
    try:
        with open(protocol_path, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([image_path])
    except:
        pass

def parse_arguments():
    parser = argparse.ArgumentParser(description='TimedViewer: Image display with logging.')
    parser.add_argument('-noprotocol', action='store_true')
    parser.add_argument('-allprotocol', action='store_true')
    parser.add_argument('-version', action='store_true')
    parser.add_argument('-gui', action='store_true')
    parser.add_argument('-noclick', action='store_true')
    parser.add_argument('-showconsole', action='store_true')
    return parser.parse_args()

def initialize_protocol(directory, protocol_path, use_protocol, initialize_all):
    displayed_images = set()
    if use_protocol:
        if initialize_all:
            all_images = get_image_files(directory)
            try:
                with open(protocol_path, 'w', newline='', encoding='utf-8') as csvfile:
                    writer = csv.writer(csvfile)
                    for image_path in all_images:
                        writer.writerow([image_path])
                        displayed_images.add(image_path)
            except:
                pass
        else:
            displayed_images = load_displayed_images(protocol_path)
    return displayed_images

def display_version_info():
    print(VERSION_INFO)
    sys.exit(0)

def delete_protocol(protocol_path):
    if os.path.exists(protocol_path):
        try:
            os.remove(protocol_path)
        except:
            pass

class ViewerApp:
    def __init__(self, root):
        self.root = root
        self.fullscreen = True
        self.root.attributes("-fullscreen", True)
        self.root.configure(background='black')
        self.root.bind("<Escape>", self.on_escape)
        if close_viewer_on_left_click:
            self.root.bind("<Button-1>", self.on_click)
        self.canvas = tk.Canvas(self.root, bg="black", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.protocol_path = os.path.join(selected_directory, PROTOCOL_FILE)
        self.displayed_images = initialize_protocol(selected_directory, self.protocol_path, not ignore_protocol, initialize_all)
        self.current_image_path = None
        self.current_image_obj = None
        self.last_check_time = time.time()
        self.check_for_new_image()
        
    def on_escape(self, event=None):
        self.root.destroy()
        
    def on_click(self, event=None):
        self.root.destroy()
        
    def show_waiting_message(self):
        self.canvas.delete("all")
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        self.canvas.create_text(w//2, h//2, text="Waiting for new images...", fill="white", font=("Arial", 30))

    def show_image(self, path):
        self.canvas.delete("all")
        try:
            # Nur PNG/GIF sicher mit PhotoImage
            ext = os.path.splitext(path)[1].lower()
            if ext not in ['.png', '.gif']:
                # Kein komplexes Laden, einfach überspringen
                return
            img = tk.PhotoImage(file=path)
            # Skalierung nicht umgesetzt (nur Bild anzeigen)
            w = self.root.winfo_width()
            h = self.root.winfo_height()
            iw = img.width()
            ih = img.height()
            scale = min(w/iw, h/ih)
            if scale < 1:
                # Simple Skalierung über sub-sampling wenn GIF
                # Für PNG geht das nicht so einfach ohne PIL
                # Wir zeigen das Bild einfach in Originalgröße an
                pass
            self.canvas.create_image(w//2, h//2, image=img)
            self.current_image_obj = img
        except:
            pass

    def check_for_new_image(self):
        now = time.time()
        if now - self.last_check_time >= check_interval_var:
            self.last_check_time = now
            images = get_image_files(selected_directory)
            new_image = None
            for im in images:
                if im not in self.displayed_images:
                    new_image = im
                    break
            if new_image:
                self.show_image(new_image)
                if not ignore_protocol:
                    save_displayed_image(self.protocol_path, new_image)
                self.displayed_images.add(new_image)
            else:
                if not any_image_displayed and waiting_for_new_images_message and not self.current_image_obj:
                    self.show_waiting_message()
        self.root.after(100, self.check_for_new_image)

def start_viewer_from_gui(root):
    root.withdraw()
    top = tk.Toplevel(root)
    top.attributes("-fullscreen", True)
    app = ViewerApp(top)

def select_directory():
    global selected_directory
    dir_path = filedialog.askdirectory(initialdir=selected_directory)
    if dir_path:
        selected_directory = dir_path
        with open(VIEWPATH_FILE, 'w', encoding='utf-8') as f:
            f.write(selected_directory)

def delete_protocol_gui():
    delete_protocol(os.path.join(selected_directory, PROTOCOL_FILE))
    messagebox.showinfo("Info", "Protocol file deleted.")

def on_start(root, interval_entry, transition_entry, noprotocol_var, allprotocol_var, closeleft_var, starfield_var, effect_var):
    global ignore_protocol, initialize_all, close_viewer_on_left_click, selected_effect, check_interval_var, transition_duration_var, show_starfield
    try:
        ci = float(interval_entry.get())
    except:
        ci = CHECK_INTERVAL
    try:
        td = float(transition_entry.get())
    except:
        td = TRANSITION_DURATION
    check_interval_var = ci
    transition_duration_var = td
    ignore_protocol = noprotocol_var.get()
    initialize_all = allprotocol_var.get()
    close_viewer_on_left_click = closeleft_var.get()
    selected_effect = effect_var.get()
    show_starfield = starfield_var.get()
    with open(VIEWPATH_FILE, 'w', encoding='utf-8') as f:
        f.write(selected_directory)
    root.withdraw()
    top = tk.Toplevel(root)
    top.attributes("-fullscreen", True)
    ViewerApp(top)

def build_gui(noclick_forced_off):
    root = tk.Tk()
    root.title("TimedViewer Configuration")
    root.geometry("460x300")
    root.resizable(False, False)

    main_frame = tk.Frame(root)
    main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    left_frame = tk.Frame(main_frame)
    right_frame = tk.Frame(main_frame)
    left_frame.grid(row=0, column=0, sticky="nw")
    right_frame.grid(row=0, column=1, sticky="ne", padx=20)
    bottom_frame = tk.Frame(root)
    bottom_frame.pack(side=tk.BOTTOM, pady=5)

    tk.Label(left_frame, text="Select directory:").grid(row=0, column=0, sticky="w", pady=(0,5))
    tk.Button(left_frame, text="Browse...", command=select_directory).grid(row=1, column=0, sticky="w", pady=(0,5))
    selected_dir_var = tk.StringVar(value=selected_directory)
    tk.Label(left_frame, textvariable=selected_dir_var, wraplength=250).grid(row=2, column=0, sticky="w", pady=(0,15))

    tk.Label(left_frame, text="Check Interval (sec):").grid(row=3, column=0, sticky="w", pady=(0,5))
    interval_entry = tk.Entry(left_frame, width=10)
    interval_entry.insert(0, str(check_interval_var))
    interval_entry.grid(row=4, column=0, sticky="w", pady=(0,15))

    tk.Label(left_frame, text="Transition Duration (sec):").grid(row=5, column=0, sticky="w", pady=(0,5))
    transition_entry = tk.Entry(left_frame, width=10)
    transition_entry.insert(0, str(transition_duration_var))
    transition_entry.grid(row=6, column=0, sticky="w")

    tk.Label(right_frame, text="Transition Effect:").grid(row=0, column=0, sticky="w", pady=(0,5))
    effect_var = tk.StringVar(value=selected_effect)
    effect_options = ["Fade", "Dissolve", "Paint", "Roll", "Random"]
    effect_dropdown = ttk.Combobox(right_frame, textvariable=effect_var, values=effect_options, state='readonly', width=15)
    effect_dropdown.set(selected_effect)
    effect_dropdown.grid(row=1, column=0, sticky="w", pady=(0,10))

    noprotocol_var = tk.BooleanVar(value=ignore_protocol)
    tk.Checkbutton(right_frame, text="Ignore protocol", variable=noprotocol_var).grid(row=2, column=0, sticky="w", pady=(0,5))
    allprotocol_var = tk.BooleanVar(value=initialize_all)
    tk.Checkbutton(right_frame, text="Use allprotocol", variable=allprotocol_var).grid(row=3, column=0, sticky="w", pady=(0,5))

    closeleft_var = tk.BooleanVar(value=close_viewer_on_left_click and not noclick_forced_off)
    cb = tk.Checkbutton(right_frame, text="Close viewer with left click", variable=closeleft_var)
    cb.grid(row=4, column=0, sticky="w", pady=(0,5))
    if noclick_forced_off:
        cb.config(state=tk.DISABLED)

    starfield_var = tk.BooleanVar(value=show_starfield)
    tk.Checkbutton(right_frame, text="Starfield background", variable=starfield_var).grid(row=5, column=0, sticky="w", pady=(0,15))

    tk.Button(right_frame, text="Delete Protocol", command=delete_protocol_gui).grid(row=6, column=0, sticky="w", pady=(0,5))

    tk.Button(bottom_frame, text="Start", command=lambda: on_start(root, interval_entry, transition_entry, noprotocol_var, allprotocol_var, closeleft_var, starfield_var, effect_var), font=("Arial", 14, "bold")).pack()

    return root

def hide_console_window():
    if platform.system() == "Windows":
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

def run_viewer():
    root = tk.Tk()
    root.withdraw()
    ViewerApp(root)
    root.mainloop()

def main():
    args = parse_arguments()
    if args.version:
        display_version_info()

    global selected_directory, ignore_protocol, initialize_all, use_protocol, close_viewer_on_left_click
    global check_interval_var, transition_duration_var, show_starfield, selected_effect

    if os.path.exists(VIEWPATH_FILE):
        try:
            with open(VIEWPATH_FILE, 'r', encoding='utf-8') as f:
                line = f.readline().strip()
                if line and os.path.isdir(line):
                    selected_directory = line
                else:
                    with open(VIEWPATH_FILE, 'w', encoding='utf-8') as fw:
                        fw.write(os.getcwd())
                    selected_directory = os.getcwd()
        except:
            selected_directory = os.getcwd()
            with open(VIEWPATH_FILE, 'w', encoding='utf-8') as fw:
                fw.write(selected_directory)
    else:
        with open(VIEWPATH_FILE, 'w', encoding='utf-8') as f:
            f.write(selected_directory)

    noclick_forced_off = False
    if args.noclick:
        noclick_forced_off = True

    use_protocol = not args.noprotocol
    initialize_all = args.allprotocol
    ignore_protocol = args.noprotocol

    if args.gui and not args.showconsole and platform.system() == "Windows":
        hide_console_window()

    if args.gui:
        gui_root = build_gui(noclick_forced_off)
        gui_root.mainloop()
    else:
        if noclick_forced_off:
            close_viewer_on_left_click = False
        run_viewer()

if __name__ == "__main__":
    main()
