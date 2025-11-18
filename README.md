Hypixel Skyblock Farming KeyTimer

A simple, open-source tool that measures how long specific keys are held during Hypixel Skyblock farming, then lets you replay those timings with audible cues. Built with Python, Tkinter, and pynput.

This tool is designed for quality-of-life testing and timing analysis.
It does not automate gameplay, and does not send or store any keystrokes.

🔧 What This Tool Does

Tracks how long each key is held down

Logs and displays key press durations

Allows editing, deleting, and organizing tracked keys

Plays back saved timings with beeps

Toggleable modes (Tracking / Playback / Standby)

Customizable hotkey for mode switching

Ignore-list system for keys you don’t want tracked

Full GUI built with Tkinter

All logic runs entirely offline and locally

🛡️ Important Note About Security

This program uses a global keyboard listener (via pynput) to detect key press durations.
Because of this, some antivirus programs may classify the compiled EXE as suspicious.

This tool is not a keylogger.
It does not save key sequences, does not transmit data, and does not monitor text input.
Only press duration of specific keys is measured.

All source code is included here so anyone can audit, build, or modify the program.

📦 Building the EXE Yourself

To verify safety or customize your build, you can compile the script yourself:

pip install pyinstaller
pyinstaller --noconsole --onefile --icon=icon.ico Hypixel_Skyblock_Farming_KeyTimer.py


The resulting EXE will appear in the dist/ folder.

🖼️ Screenshots

<img width="911" height="828" alt="image" src="https://github.com/user-attachments/assets/59e2e0dd-26f1-4bdd-ba97-9c6c46855c8f" />

💬 FAQ
Is this bannable on Hypixel?

The tool does not send inputs or automate anything. It only measures timing.
Still — use at your own discretion and make sure you follow server rules.

Why does my antivirus flag the EXE?

Because global keyboard hooks resemble behavior used by keyloggers.
Since this tool is open-source, anyone may verify that it is safe.

Does it store my keystrokes?

❌ No
Only duration of individual keys is recorded — not text or sequences.

🤝 Contributing

Pull requests, suggestions, and improvements are welcome!
If you find bugs, just open an Issue.

⚖️ Legal

This project is under an MIT License. 

Use the code for personal or commercial purposes. 👍

Copy, modify, merge, publish, distribute, sublicense the code. 👍

Include it in proprietary projects, as long as they include your license notice. 👍
