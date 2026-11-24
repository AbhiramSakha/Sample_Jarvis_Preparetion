import platform
import shutil
import subprocess
import webbrowser
from datetime import datetime

import psutil

from tools.registry import registry


@registry.register("get_time", "Get the current local date and time.")
def get_time():
    return datetime.now().strftime("%A, %d %B %Y, %I:%M %p")


@registry.register(
    "open_app",
    "Open an application on the computer by name, e.g. 'notepad', 'Spotify', 'calculator'.",
    {"name": {"type": "string", "description": "Application name"}},
    ["name"],
)
def open_app(name: str):
    system = platform.system()
    if system == "Windows":
        subprocess.Popen(["cmd", "/c", "start", "", name], shell=False)
    elif system == "Darwin":
        subprocess.Popen(["open", "-a", name])
    else:
        exe = shutil.which(name.lower())
        if not exe:
            return f"Could not find an app called {name}."

        subprocess.Popen([exe])
    return f"Opening {name}."


@registry.register(
    "open_website",
    "Open a website in the default browser.",
    {"url": {"type": "string", "description": "Full URL, e.g. https://youtube.com"}},
    ["url"],
)
def open_website(url: str):
    if not url.startswith("http"):
        url = "https://" + url
    webbrowser.open(url)
    return f"Opened {url}."


@registry.register("system_status", "Report CPU usage, RAM usage and battery level.")
def system_status():
    cpu = psutil.cpu_percent(interval=0.5)
    ram = psutil.virtual_memory().percent
    battery = psutil.sensors_battery()
    text = f"CPU {cpu}%, RAM {ram}%."
    if battery:
        text += f" Battery {battery.percent:.0f}%{' (charging)' if battery.power_plugged else ''}."
    return text