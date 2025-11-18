import tkinter as tk
from tkinter import ttk
from pynput import keyboard # type: ignore
import threading
import time
import winsound

key_pressed_time = {}
recorded_durations = {}
recorded_key_vars = {}
active_keys_playback = set()
beeping_keys = set()
ignored_keys = set()
mode_toggle_hotkey = 'f10'  # default hotkey to toggle modes
adding_ignored_key = False
previous_mode = None

# GUI setup
root = tk.Tk()
root.title("Hypixcel Skyblock Farming KeyTimer")
root.geometry("768x768")

# Helper function to convert pynput keys to consistent string format
def key_to_str(key):
    try:
        return key.char.lower()  # normal character keys
    except AttributeError:
        return str(key).replace('Key.', '').lower()  # special keys

# Mode variable
mode_options = ['Tracking', 'Playback', 'Standby']
mode_index = 0  # Start at Tracking
mode = tk.StringVar(value=mode_options[mode_index])

# Text box with its own scrollbar frame
text_box_frame = tk.Frame(root)
text_box_frame.pack(pady=10, fill=tk.BOTH, expand=True)

text_scroll = tk.Scrollbar(text_box_frame)
text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

text_box = tk.Text(text_box_frame, height=15, width=80, yscrollcommand=text_scroll.set)
text_box.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
text_scroll.config(command=text_box.yview)

# Only scroll text_box with mouse wheel when hovering over it
def _on_textbox_mousewheel(event):
    text_box.yview_scroll(int(-1*(event.delta/120)), 'units')
text_box.bind('<Enter>', lambda e: text_box.bind_all('<MouseWheel>', _on_textbox_mousewheel))
text_box.bind('<Leave>', lambda e: text_box.unbind_all('<MouseWheel>'))

mode_frame = tk.Frame(root)
mode_frame.pack()

tracking_radio = ttk.Radiobutton(mode_frame, text='Tracking', variable=mode, value='Tracking')
playback_radio = ttk.Radiobutton(mode_frame, text='Playback', variable=mode, value='Playback')
standby_radio = ttk.Radiobutton(mode_frame, text='Standby', variable=mode, value='Standby')
tracking_radio.pack(side=tk.LEFT, padx=10)
playback_radio.pack(side=tk.LEFT, padx=10)
standby_radio.pack(side=tk.LEFT, padx=10)

# Recorded Keys Frame
recorded_frame = tk.LabelFrame(root, text="Recorded Keys", padx=10, pady=10)
recorded_frame.pack(pady=10, fill=tk.X)

# Canvas + Scrollbar for scrollable area
recorded_canvas = tk.Canvas(recorded_frame, height=150)
recorded_scroll = tk.Scrollbar(recorded_frame, orient=tk.VERTICAL, command=recorded_canvas.yview)
recorded_canvas.configure(yscrollcommand=recorded_scroll.set)

recorded_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
recorded_scroll.pack(side=tk.RIGHT, fill=tk.Y)

# Frame inside canvas to hold key entries
recorded_keys_inner = tk.Frame(recorded_canvas)
recorded_canvas.create_window((0, 0), window=recorded_keys_inner, anchor='nw')

# Update scroll region when widgets change
recorded_keys_inner.bind('<Configure>', lambda e: recorded_canvas.configure(scrollregion=recorded_canvas.bbox('all')))

# Only scroll recorded keys canvas with mouse wheel when hovering over it
def _on_recorded_mousewheel(event):
    recorded_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')

recorded_canvas.bind('<Enter>', lambda e: recorded_canvas.bind_all('<MouseWheel>', _on_recorded_mousewheel))
recorded_canvas.bind('<Leave>', lambda e: recorded_canvas.unbind_all('<MouseWheel>'))

# Dictionary to store entry widgets per key
recorded_key_entries = {}

def refresh_recorded_keys():
    global previous_mode
    # Clear old widgets
    for widget in recorded_keys_inner.winfo_children():
        widget.destroy()
    recorded_key_entries.clear()
    recorded_key_vars.clear()

    for key_str, duration in recorded_durations.items():
        frame = tk.Frame(recorded_keys_inner)
        frame.pack(fill=tk.X, pady=2)

        # Checkbox for deletion
        var_chk = tk.IntVar()
        chk = tk.Checkbutton(frame, variable=var_chk)
        chk.pack(side=tk.LEFT, padx=5)
        recorded_key_vars[key_str] = (var_chk, chk)

        # Key label
        lbl = tk.Label(frame, text=key_str.upper(), width=8, anchor='w')
        lbl.pack(side=tk.LEFT, padx=5)

        # Entry for duration
        var_entry = tk.StringVar(value=f"{duration:.4f}")
        entry = tk.Entry(frame, textvariable=var_entry, width=10)
        entry.pack(side=tk.LEFT, padx=5)

        # Track original value to detect real changes
        original_value = var_entry.get()

        def on_change(event=None, k=key_str, v=var_entry):
            nonlocal original_value
            try:
                new_val = float(v.get())
                # Only update if value actually changed
                if float(original_value) != new_val:
                    recorded_durations[k] = new_val
                    log_message(f"Updated {k.upper()} duration to {new_val:.4f} seconds")
                    original_value = v.get()
            except ValueError:
                v.set(original_value)  # reset if invalid

        entry.bind('<Return>', on_change)

        # Temporary Standby while editing
        def on_focus_in(event, e=entry):
            global previous_mode
            if previous_mode is None:
                previous_mode = mode.get()
            mode.set('Standby')

        entry.bind('<FocusIn>', on_focus_in)

        # FocusOut updates only if value changed
        def on_focus_out(event, e=entry):
            on_change()
            global previous_mode
            if previous_mode is not None:
                mode.set(previous_mode)
                previous_mode = None

        entry.bind('<FocusOut>', on_focus_out)

        recorded_key_entries[key_str] = entry

    # Detect clicks outside entries to restore previous mode
    def on_click_outside(event):
        global previous_mode
        widget = event.widget
        if widget not in recorded_key_entries.values():
            if previous_mode is not None:
                mode.set(previous_mode)
                previous_mode = None

    root.bind_all('<Button-1>', on_click_outside, add='+')

    recorded_canvas.yview_moveto(1.0)

def delete_checked_recorded_keys():
    to_delete = [k for k, (var, chk) in recorded_key_vars.items() if var.get() == 1]
    for key in to_delete:
        # Remove from data
        if key in recorded_durations:
            del recorded_durations[key]

        # Destroy widgets
        _, chk = recorded_key_vars[key]
        chk.master.destroy()  # destroy the whole frame containing the checkbox, label, and entry

        # Remove from dictionaries
        if key in recorded_key_entries:
            del recorded_key_entries[key]
        del recorded_key_vars[key]

    refresh_recorded_keys()  # refresh the list
    recorded_canvas.yview_moveto(0.0)  # scroll to top

# Button to delete selected keys
delete_recorded_button = tk.Button(recorded_frame, text="Delete Checked Tracked Keys", command=delete_checked_recorded_keys)
delete_recorded_button.pack(anchor=tk.W, pady=5)

# Settings Frame
settings_frame = tk.LabelFrame(root, text="Settings", padx=10, pady=10)
settings_frame.pack(pady=10, fill=tk.X)

hotkey_label = tk.Label(settings_frame, text=f"Toggle Mode Hotkey: {mode_toggle_hotkey}")
hotkey_label.pack(anchor=tk.W)

hotkey_button = tk.Button(settings_frame, text="Change Hotkey")
hotkey_button.pack(anchor=tk.W, pady=5)

ignored_label = tk.Label(settings_frame, text="Ignored Keys:")
ignored_label.pack(anchor=tk.W)

ignored_keys_canvas = tk.Canvas(settings_frame, height=150)
ignored_keys_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

ignored_keys_scroll = tk.Scrollbar(settings_frame, orient=tk.VERTICAL, command=ignored_keys_canvas.yview)
ignored_keys_scroll.pack(side=tk.RIGHT, fill=tk.Y)
ignored_keys_canvas.configure(yscrollcommand=ignored_keys_scroll.set)
ignored_keys_frame = tk.Frame(ignored_keys_canvas)
ignored_keys_canvas.create_window((0, 0), window=ignored_keys_frame, anchor='nw')
ignored_keys_frame.bind('<Configure>', lambda e: ignored_keys_canvas.configure(scrollregion=ignored_keys_canvas.bbox('all')))

refresh_recorded_keys()

# Only scroll ignored keys canvas with mouse wheel when hovering over it
def _on_ignored_mousewheel(event):
    ignored_keys_canvas.yview_scroll(int(-1*(event.delta/120)), 'units')
ignored_keys_canvas.bind('<Enter>', lambda e: ignored_keys_canvas.bind_all('<MouseWheel>', _on_ignored_mousewheel))
ignored_keys_canvas.bind('<Leave>', lambda e: ignored_keys_canvas.unbind_all('<MouseWheel>'))

ignored_key_vars = {}  # key: tk.IntVar for checkbox

def log_message(message):
    text_box.insert(tk.END, message + '\n')
    text_box.see(tk.END)

# Function to add an ignored key
def add_ignored_key():
    global adding_ignored_key
    adding_ignored_key = True

    def on_key_press(event):
        global adding_ignored_key
        key_name = event.keysym.lower()
        if key_name != 'backspace' and key_name not in ignored_keys:
            ignored_keys.add(key_name)
            var = tk.IntVar()
            chk = tk.Checkbutton(ignored_keys_frame, text=key_name, variable=var)
            chk.pack(anchor=tk.W)
            ignored_key_vars[key_name] = (var, chk)
            log_message(f"Added {key_name.upper()} to ignored keys list")
        root.unbind('<Key>')
        adding_ignored_key = False

    log_message("Press a key to ignore...")
    root.bind('<Key>', on_key_press)

# Function to delete checked ignored keys
def delete_checked_ignored_keys():
    to_delete = [k for k, (var, chk) in ignored_key_vars.items() if var.get() == 1]
    for key in to_delete:
        _, chk = ignored_key_vars[key]
        chk.destroy()
        ignored_keys.discard(key)
        del ignored_key_vars[key]

    ignored_keys_canvas.yview_moveto(0.0)  # scroll to top

hotkey_change_callback = None

def change_hotkey():
    def on_key_press(event):
        global mode_toggle_hotkey
        key_name = event.keysym.lower()
        mode_toggle_hotkey = key_name
        hotkey_label.config(text=f"Toggle Mode Hotkey: {mode_toggle_hotkey}")
        log_message(f"Mode toggle hotkey changed to {mode_toggle_hotkey}")
        root.unbind('<Key>')
    log_message("Press a key to set as toggle hotkey...")
    root.bind('<Key>', on_key_press)

add_ignore_button = tk.Button(settings_frame, text="Add Ignore Key", command=add_ignored_key)
add_ignore_button.pack(anchor=tk.W, pady=5)

delete_checked_button = tk.Button(settings_frame, text="Delete Checked Ignored Keys", command=delete_checked_ignored_keys)
delete_checked_button.pack(anchor=tk.W, pady=5)

def on_press(key):
    try:
        global adding_ignored_key
        if adding_ignored_key:
            return  # ignore normal key processing while adding ignored key

        # Convert key to string
        try:
            key_name = key.char.lower()  # normal keys
        except AttributeError:
            key_name = str(key).replace('Key.', '').lower()  # special keys

        # Check for mode toggle hotkey
        if key_name == mode_toggle_hotkey:  # compare as string
            global mode_index
            mode_index = (mode_index + 1) % len(mode_options)
            mode.set(mode_options[mode_index])
            log_message(f"Mode toggled to {mode.get()} via hotkey")

            # Cancel all active playback and tracking if switching to Standby
            if mode.get() == 'Standby':
                beeping_keys.clear()
                active_keys_playback.clear()
                key_pressed_time.clear()
            return

        # Ignore keys in ignored list
        if key_name in ignored_keys:
            return

        key_str = key_to_str(key)

        # Do nothing in Standby
        if mode.get() == 'Standby':
            return
        elif mode.get() == 'Tracking':
            if key_str not in key_pressed_time:
                key_pressed_time[key_str] = time.time()
        elif mode.get() == 'Playback':
            if key_str in recorded_durations and key_str not in active_keys_playback:
                active_keys_playback.add(key_str)
                duration = recorded_durations[key_str]
                log_message(f"Playback started for {key_str} for {duration:.4f} seconds")
                threading.Thread(target=play_timer, args=(key_str, duration), daemon=True).start()

    except Exception as e:
        log_message(f"Error on_press: {e}")

def on_release(key):
    try:
        key_str = key_to_str(key)

        if mode.get() == 'Standby':
            return  # Do nothing in standby
        if mode.get() == 'Tracking' and key_str in key_pressed_time:
            duration = time.time() - key_pressed_time[key_str]
            recorded_durations[key_str] = duration
            log_message(f"Key {key_str} was pressed for {duration:.4f} seconds")
            del key_pressed_time[key_str]

            refresh_recorded_keys()

        if key_str in beeping_keys:
            beeping_keys.discard(key_str)

        if key_str in active_keys_playback:
            active_keys_playback.discard(key_str)


        if key == keyboard.Key.esc:
            return False
    except Exception as e:
        log_message(f"Error on_release: {e}")

def play_timer(key_str, duration):
    # Sleep for the duration of the original key press
    time.sleep(duration)
    log_message(f"Playback timer ended for {key_str}! Beeping...")

    # Calculate number of short beeps (100ms each)
    num_beeps = max(1, int(duration / 0.1))  # at least one beep
    for _ in range(num_beeps):
        winsound.Beep(1000, 100)
        time.sleep(0.05)  # small delay to reduce CPU usage

    log_message(f"Playback finished for {key_str}")
    active_keys_playback.discard(key_str)

def start_listener():
    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()

listener_thread = threading.Thread(target=start_listener, daemon=True)
listener_thread.start()

hotkey_button.config(command=change_hotkey)

root.mainloop()