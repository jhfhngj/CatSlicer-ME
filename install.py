import os
with open("requirements.txt") as f:
    rqs = f.readlines()
commands = f"""winget install ffmpeg
winget install Python.Python.3.13
py -m pip install {" ".join(rqs)}"""
for cmd in commands.splitlines():
    os.system(cmd)