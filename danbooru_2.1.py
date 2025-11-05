import os
import asyncio
import aiohttp
import requests
import webbrowser
from tkinter import Tk, Label, Entry, Button, filedialog, BooleanVar, StringVar, IntVar, messagebox, Frame
from tkinter import DISABLED, NORMAL
from tkinter import ttk
import threading

current_version = 2.1
latest_version_url = 'https://raw.githubusercontent.com/neoluigi4123/Gelbooru-Image-Downloader/main/latest'
github_url = 'https://github.com/neoluigi4123/Gelbooru-Image-Downloader'

stop_event = threading.Event()

def check_for_update():
    try:
        response = requests.get(latest_version_url)
        response.raise_for_status()
        latest_version = float(response.text.strip())
        
        if latest_version > current_version:
            update_button.grid(row=10, column=0, padx=20, pady=10, columnspan=3, sticky="ew")
    except Exception as e:
        process_var.set(f"Error checking for updates: {e}")

def open_github_page():
    webbrowser.open(github_url)

async def download_file(session, url, save_path):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            with open(save_path, 'wb') as file:
                while chunk := await response.content.read(8192):
                    if stop_event.is_set():
                        return False
                    file.write(chunk)

            filename = os.path.basename(save_path)
            if len(filename) > 40:
                filename = filename[:37] + "..."
            process_var.set(f"Downloaded: {filename}")
            return True
    except Exception as e:
        process_var.set(f"Failed to download: {str(e)[:50]}...")
        return False

async def fetch_danbooru_images(tags, page=1, limit=100):
    url = "https://danbooru.donmai.us/posts.json"
    params = {
        "tags": tags,
        "limit": min(limit, 200),
        "page": page
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()
                return await response.json()
    except Exception as e:
        process_var.set(f"Error fetching images: {str(e)[:50]}...")
        return []

async def download_images(tags, save_dir, max_images=None):
    os.makedirs(save_dir, exist_ok=True)
    total_downloaded = 0
    page = 1
    seen_posts = set()

    async with aiohttp.ClientSession() as session:
        while not stop_event.is_set() and (max_images is None or total_downloaded < max_images):
            if stop_event.is_set():
                break
                
            process_var.set(f"Fetching images (page {page})...")
            remaining = (max_images - total_downloaded) if max_images else 200
            posts = await fetch_danbooru_images(tags, page=page, limit=min(remaining, 200))

            if not posts:
                process_var.set("No more images found.")
                break

            for post in posts:
                if stop_event.is_set():
                    break
                    
                if max_images is not None and total_downloaded >= max_images:
                    break
                    
                file_url = post.get("file_url")
                if file_url and file_url not in seen_posts:
                    seen_posts.add(file_url)
                    file_name = os.path.join(save_dir, os.path.basename(file_url))
                    success = await download_file(session, file_url, file_name)
                    if success:
                        total_downloaded += 1
                    
                    if stop_event.is_set():
                        break
                    
                    await asyncio.sleep(0.1 if fast_download_var.get() else 0.3)

            if stop_event.is_set():
                break

            await asyncio.sleep(0.3 if fast_download_var.get() else 1)
            page += 1

    if stop_event.is_set():
        process_var.set(f"Download stopped. Images downloaded: {total_downloaded}")
    else:
        if open_dir_var.get():
            open_directory(save_dir)
        process_var.set(f"Download complete. Total images downloaded: {total_downloaded}")

def format_tags(raw_tags):
    return [tag.strip().replace(' ', '_') for tag in raw_tags.split(',')]

def start_download():
    stop_event.clear()
    directory = custom_dir_var.get() if use_custom_dir.get() else default_directory
    raw_tags = tag_entry.get()

    if not raw_tags:
        messagebox.showwarning("Input Error", "Please enter tags.")
        return

    tags = format_tags(raw_tags)
    save_dir = os.path.join(directory, '_'.join(tags))
    os.makedirs(save_dir, exist_ok=True)

    max_images = max_images_var.get() if max_images_checkbox_var.get() else None

    process_var.set("Starting download...")
    download_thread = threading.Thread(target=lambda: asyncio.run(download_images(' '.join(tags), save_dir, max_images)), daemon=True)
    download_thread.start()

def select_directory():
    directory = filedialog.askdirectory()
    if directory:
        custom_dir_var.set(directory)

def toggle_custom_dir(*args):
    custom_dir_entry.config(state=NORMAL if use_custom_dir.get() else DISABLED)

def stop_download():
    stop_event.set()
    process_var.set("Stopping download...")

def toggle_max_images_entry(*args):
    max_images_entry.config(state=NORMAL if max_images_checkbox_var.get() else DISABLED)

def open_directory(directory):
    if os.name == 'nt':
        os.startfile(directory)

BG_COLOR = "#0f0f0f"
CARD_BG = "#1a1a1a"
INPUT_BG = "#252525"
INPUT_FG = "#e0e0e0"
ACCENT_COLOR = "#4a9eff"
ACCENT_HOVER = "#6bb0ff"
TEXT_COLOR = "#ffffff"
SECONDARY_TEXT = "#a0a0a0"
BUTTON_BG = "#2d2d2d"

root = Tk()
root.title("Danbooru Image Downloader")
root.config(bg=BG_COLOR, padx=20, pady=20)
root.resizable(False, False)

# Configure modern style for ttk widgets
style = ttk.Style()
style.theme_use('clam')
style.configure('Modern.TCheckbutton', 
                background=CARD_BG, 
                foreground=TEXT_COLOR,
                font=('Segoe UI', 10),
                borderwidth=0)
style.map('Modern.TCheckbutton',
          background=[('active', CARD_BG)],
          foreground=[('active', ACCENT_COLOR)])

tag_var = StringVar()
custom_dir_var = StringVar()
use_custom_dir = BooleanVar()
max_images_checkbox_var = BooleanVar()
max_images_var = IntVar(value=10)
open_dir_var = BooleanVar()
fast_download_var = BooleanVar()
process_var = StringVar()

default_directory = os.getcwd()

# Main container frame
main_frame = Frame(root, bg=CARD_BG, relief="flat", bd=0)
main_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)

# Title
title_label = Label(main_frame, text="DANBOORU DOWNLOADER", 
                    bg=CARD_BG, fg=TEXT_COLOR, 
                    font=('Segoe UI', 18, 'bold'),
                    pady=15)
title_label.grid(row=0, column=0, columnspan=3, sticky="ew", padx=20)

# Tags section
tag_label = Label(main_frame, text="TAGS", 
                 bg=CARD_BG, fg=SECONDARY_TEXT, 
                 font=('Segoe UI', 9, 'bold'),
                 anchor="w")
tag_label.grid(row=1, column=0, padx=20, pady=(20, 5), sticky="w", columnspan=3)

tag_entry = Entry(main_frame, textvariable=tag_var, 
                 width=50, bg=INPUT_BG, fg=INPUT_FG,
                 font=('Segoe UI', 11),
                 relief="flat", bd=0,
                 insertbackground=TEXT_COLOR,
                 highlightthickness=2,
                 highlightbackground=INPUT_BG,
                 highlightcolor=ACCENT_COLOR)
tag_entry.grid(row=2, column=0, padx=20, pady=(0, 15), columnspan=3, sticky="ew", ipady=8)

# Directory section
custom_dir_check = ttk.Checkbutton(main_frame, text="Custom Directory", 
                                  variable=use_custom_dir,
                                  style='Modern.TCheckbutton')
custom_dir_check.grid(row=3, column=0, padx=20, pady=(10, 5), sticky="w", columnspan=3)

dir_frame = Frame(main_frame, bg=CARD_BG)
dir_frame.grid(row=4, column=0, padx=20, pady=(0, 15), columnspan=3, sticky="ew")

custom_dir_entry = Entry(dir_frame, textvariable=custom_dir_var, 
                         state=DISABLED, bg=INPUT_BG, fg=INPUT_FG,
                         font=('Segoe UI', 10),
                         relief="flat", bd=0,
                         insertbackground=TEXT_COLOR,
                         highlightthickness=2,
                         highlightbackground=INPUT_BG,
                         highlightcolor=ACCENT_COLOR)
custom_dir_entry.pack(side="left", fill="x", expand=True, ipady=6)

browse_button = Button(dir_frame, text="BROWSE", command=select_directory, 
                      bg=BUTTON_BG, fg=TEXT_COLOR,
                      font=('Segoe UI', 9, 'bold'),
                      relief="flat", bd=0,
                      cursor="hand2",
                      activebackground=ACCENT_COLOR,
                      activeforeground=TEXT_COLOR,
                      padx=20, pady=8)
browse_button.pack(side="right", padx=(10, 0))

# Options section
options_frame = Frame(main_frame, bg=CARD_BG)
options_frame.grid(row=5, column=0, padx=20, pady=10, columnspan=3, sticky="w")

max_images_check = ttk.Checkbutton(options_frame, text="Limit Images", 
                                  variable=max_images_checkbox_var,
                                  style='Modern.TCheckbutton')
max_images_check.grid(row=0, column=0, sticky="w", pady=5)

max_images_entry = Entry(options_frame, textvariable=max_images_var, 
                        width=10, state=DISABLED, bg=INPUT_BG, fg=INPUT_FG,
                        font=('Segoe UI', 10),
                        relief="flat", bd=0,
                        insertbackground=TEXT_COLOR,
                        highlightthickness=2,
                        highlightbackground=INPUT_BG,
                        highlightcolor=ACCENT_COLOR)
max_images_entry.grid(row=0, column=1, padx=10, sticky="w", ipady=4)

open_dir_check = ttk.Checkbutton(options_frame, text="Open Directory After Download", 
                                variable=open_dir_var,
                                style='Modern.TCheckbutton')
open_dir_check.grid(row=1, column=0, sticky="w", pady=5, columnspan=2)

fast_download_check = ttk.Checkbutton(options_frame, text="Fast Download (Less stable)", 
                                     variable=fast_download_var,
                                     style='Modern.TCheckbutton')
fast_download_check.grid(row=2, column=0, sticky="w", pady=5, columnspan=2)

# Action buttons
button_frame = Frame(main_frame, bg=CARD_BG)
button_frame.grid(row=6, column=0, padx=20, pady=20, columnspan=3, sticky="ew")

start_button = Button(button_frame, text="START DOWNLOAD", command=start_download, 
                     bg=ACCENT_COLOR, fg=TEXT_COLOR,
                     font=('Segoe UI', 11, 'bold'),
                     relief="flat", bd=0,
                     cursor="hand2",
                     activebackground=ACCENT_HOVER,
                     activeforeground=TEXT_COLOR,
                     padx=30, pady=12)
start_button.pack(side="left", expand=True, fill="x", padx=(0, 5))

stop_button = Button(button_frame, text="STOP", command=stop_download, 
                    bg=BUTTON_BG, fg=TEXT_COLOR,
                    font=('Segoe UI', 11, 'bold'),
                    relief="flat", bd=0,
                    cursor="hand2",
                    activebackground="#ff4444",
                    activeforeground=TEXT_COLOR,
                    padx=30, pady=12)
stop_button.pack(side="right", expand=True, fill="x", padx=(5, 0))

# Status section
status_frame = Frame(main_frame, bg=INPUT_BG, relief="flat", bd=0)
status_frame.grid(row=7, column=0, padx=20, pady=(0, 20), columnspan=3, sticky="ew")

process_label = Label(status_frame, textvariable=process_var, 
                     bg=INPUT_BG, fg=SECONDARY_TEXT,
                     font=('Segoe UI', 9),
                     anchor="w", padx=15, pady=12,
                     width=60)  # Fixed width to prevent resizing
process_label.pack(fill="x")

# Update button
update_button = Button(main_frame, text="🔄 NEW VERSION AVAILABLE - CLICK TO UPDATE", 
                      command=open_github_page, 
                      bg="#ff9500", fg=TEXT_COLOR,
                      font=('Segoe UI', 10, 'bold'),
                      relief="flat", bd=0,
                      cursor="hand2",
                      activebackground="#ffaa00",
                      activeforeground=TEXT_COLOR,
                      pady=12)
update_button.grid(row=8, column=0, padx=20, pady=(0, 20), columnspan=3, sticky="ew")
update_button.grid_remove()

# Configure grid weights
main_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(0, weight=1)
button_frame.columnconfigure(1, weight=1)

use_custom_dir.trace_add("write", toggle_custom_dir)
max_images_checkbox_var.trace_add("write", toggle_max_images_entry)

check_for_update()

root.mainloop()