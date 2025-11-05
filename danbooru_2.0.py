import os
import asyncio
import aiohttp
import requests
import webbrowser
from tkinter import Tk, Label, Entry, Button, filedialog, BooleanVar, StringVar, IntVar, messagebox
from tkinter import DISABLED, NORMAL
from tkinter import ttk
import threading

current_version = 2.0
latest_version_url = 'https://raw.githubusercontent.com/neoluigi4123/Gelbooru-Image-Downloader/main/latest'
github_url = 'https://github.com/neoluigi4123/Gelbooru-Image-Downloader'

stop_event = threading.Event()

# Function to check for updates
def check_for_update():
    try:
        response = requests.get(latest_version_url)
        response.raise_for_status()
        latest_version = float(response.text.strip())
        
        if latest_version > current_version:
            # If a new version is available, show the update button
            update_button.grid(row=10, column=0, padx=10, pady=10, columnspan=3)
    except Exception as e:
        process_var.set(f"Error checking for updates: {e}")

# Function to open the GitHub page
def open_github_page():
    webbrowser.open(github_url)

async def download_file(session, url, save_path):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            with open(save_path, 'wb') as file:
                while chunk := await response.content.read(8192):
                    file.write(chunk)
            process_var.set(f"Downloaded: {save_path}")
    except Exception as e:
        process_var.set(f"Failed to download {url}: {e}")

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
        process_var.set(f"Error fetching images: {e}")
        return []

async def download_images(tags, save_dir, max_images=None):
    os.makedirs(save_dir, exist_ok=True)
    total_downloaded = 0
    page = 1
    seen_posts = set()

    async with aiohttp.ClientSession() as session:
        while not stop_event.is_set() and (max_images is None or total_downloaded < max_images):
            process_var.set(f"Fetching images (page {page})...")
            remaining = (max_images - total_downloaded) if max_images else 200
            posts = await fetch_danbooru_images(tags, page=page, limit=min(remaining, 200))

            if not posts:
                process_var.set("No more images found.")
                break

            tasks = []
            for post in posts:
                if stop_event.is_set() or (max_images is not None and total_downloaded >= max_images):
                    break
                file_url = post.get("file_url")
                if file_url and file_url not in seen_posts:
                    seen_posts.add(file_url)
                    file_name = os.path.join(save_dir, os.path.basename(file_url))
                    tasks.append(download_file(session, file_url, file_name))
                    total_downloaded += 1

            await asyncio.gather(*tasks)
            await asyncio.sleep(0.3 if fast_download_var.get() else 1)
            page += 1

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
    download_thread = threading.Thread(target=lambda: asyncio.run(download_images(','.join(tags), save_dir, max_images)))
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

root = Tk()
root.title("Danbooru Image Downloader")
root.config(bg="#1e1e1e")

tag_var = StringVar()
custom_dir_var = StringVar()
use_custom_dir = BooleanVar()
max_images_checkbox_var = BooleanVar()
max_images_var = IntVar(value=10)
open_dir_var = BooleanVar()
fast_download_var = BooleanVar()
process_var = StringVar()

default_directory = os.getcwd()

# Create UI elements
tag_label = Label(root, text="Tags (comma separated):", bg="#1e1e1e", fg="white")
tag_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")

tag_entry = Entry(root, textvariable=tag_var, width=40, bg="#333333", fg="white")
tag_entry.grid(row=0, column=1, padx=10, pady=10)

custom_dir_check = ttk.Checkbutton(root, text="Use Custom Directory", variable=use_custom_dir)
custom_dir_check.grid(row=1, column=0, padx=10, pady=10, sticky="e")

custom_dir_entry = Entry(root, textvariable=custom_dir_var, width=40, state=DISABLED, bg="#333333", fg="white")
custom_dir_entry.grid(row=1, column=1, padx=10, pady=10)

browse_button = Button(root, text="Browse", command=select_directory, bg="#333333", fg="white")
browse_button.grid(row=1, column=2, padx=10, pady=10)

max_images_check = ttk.Checkbutton(root, text="Limit Max Images", variable=max_images_checkbox_var)
max_images_check.grid(row=2, column=0, padx=10, pady=10, sticky="e")

max_images_entry = Entry(root, textvariable=max_images_var, width=10, state=DISABLED, bg="#333333", fg="white")
max_images_entry.grid(row=2, column=1, padx=10, pady=10, sticky="w")

open_dir_check = ttk.Checkbutton(root, text="Open Directory After Download", variable=open_dir_var)
open_dir_check.grid(row=3, column=0, padx=10, pady=10, columnspan=2)

fast_download_check = ttk.Checkbutton(root, text="Fast Download (Less Delay but more likely to crash)", variable=fast_download_var)
fast_download_check.grid(row=4, column=0, padx=10, pady=10, columnspan=2)

start_button = Button(root, text="Start Download", command=start_download, bg="#333333", fg="white")
start_button.grid(row=5, column=0, padx=10, pady=10, columnspan=2)

stop_button = Button(root, text="Stop Download", command=stop_download, bg="#333333", fg="white")
stop_button.grid(row=5, column=1, padx=10, pady=10, columnspan=2)

process_label = Label(root, textvariable=process_var, bg="#1e1e1e", fg="white")
process_label.grid(row=6, column=0, padx=10, pady=10, columnspan=3)

update_button = Button(root, text="New version available! Click here to get it.", command=open_github_page, bg="#333333", fg="white")
update_button.grid(row=7, column=0, padx=10, pady=10, columnspan=3)
update_button.grid_remove()

use_custom_dir.trace_add("write", toggle_custom_dir)
max_images_checkbox_var.trace_add("write", toggle_max_images_entry)

check_for_update()

root.mainloop()