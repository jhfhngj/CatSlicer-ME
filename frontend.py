import flet as ft
import subprocess, shutil, os
import tkinter as tk
from tkinter import filedialog
from flet_video import *
import threading
BASE = os.path.dirname(os.path.abspath(__file__))
root = tk.Tk()
root.withdraw()
root.destroy()

def slce(page: ft.Page):
    def worker():
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        try:
            shutil.copyfile(file_path, "./temp.stl")
        except Exception as e:
            page.dialog = ft.AlertDialog(
                title=ft.Text("An error has occurred!"),
                content=ft.Text(str(e)),
                open=True,
            )
            page.update()
            return

        notification(page, "Slicing...")
        subprocess.run(["python3", os.path.join(BASE, "slice.py")])
        os.remove("./temp.stl")
        notification(page, "Sliced!")

        page.add(ft.Text("Copy this then flash it to the Arduino:", size=15, color=current["text"]))
        with open("flashme.ino") as f:
            page.add(ft.TextField(f.read().strip(), multiline=True, height=2**9, width=2**20, read_only=True))
        page.update()

        with open("temp.txt") as f:
            page.add(ft.Text(f"Time: {f.read()}", size=15, color=current["text"]))
        os.remove("./temp.txt")
        page.update()

        notification(page, "Rendering preview...")
        subprocess.run(["python3", os.path.join(BASE, "render.py")])
        notification(page, "Rendered!")

        video_path = os.path.join(BASE, "render.mp4")
        page.add(Video([VideoMedia(video_path)], "Rendered Movie", expand=True))
        page.update()

    threading.Thread(target=worker, daemon=True).start()

def notification(page:ft.Page,text:str):
    page.add(ft.Text(text, size=15, color=current["text"]))
    page.update()
light = {"text": "blue", "bg": "white"}
current = light

def main(page: ft.Page):
    page.title = "CatSlicer"
    page.add(ft.Text("CatSlicer 1.0.1", size=30, color=current["text"]))
    page.add(ft.Text("Hello!", size=15, color=current["text"]))
    page.add(ft.Text("Ready to slice an object?", size=15, color=current["text"]))
    page.add(ft.TextButton("Slice",on_click=lambda _: slce(page)))

ft.run(main=main)
