import mido
import keyboard
import time
import threading
import heapq

# -------- CONFIG --------
midi_files = {
    "1": "music/32ki_-_Mesmerizer_Piano_Ver..mid",
    "2": "music/ASGORE.mid",
    "3": "music/Camille-Michael-Giacchino-Le-Festin-Anonymous-20210822171256-nonstop2k.com.mid",
    "4": "music/DIE.mid",
    "5": "music/gurenge.mid",
    "6": "music/Inferno.mid",
    "7": "music/Kimi.mid",
    "8": "music/op.mid",
    "9": "music/stromae-papaoutai.mid",
    "0": "music/teto territory - kasane teto.mid"
}

first_note_midi = 60 - 24
transposition = 0
stop_key = "F8"

piano_keys = [
    "1", "!", "2", "@", "3", "4", "$",  "5", "%", "6", "^", "7", "8", "*", "9", "(", "0",
    "q", "Q", "w", "W", "e", "E", "r", "t", "T", "y", "Y", "u", "i", "I", "o", "O", "p", "P",
    "a", "s", "S", "d", "D","f", "g", "G", "h", "H", "j", "J", "k", "l", "L", "z", "Z", "x", "c", "C", "v", "V", "b", "B", "n", "m"
]

note_to_key = {first_note_midi + transposition + i: key for i, key in enumerate(piano_keys)}

# Caractères qui demandent Shift
shift_chars = {"!", "@", "$", "%", "^", "*", "(", "Q", "W", "E", "T", "Y", "I", "O", "P",
               "S", "D", "G", "H", "J", "L", "Z", "C", "V", "B"}

# Mapping pour les touches shiftées
shift_base_key = {}
for i, key in enumerate(piano_keys):
    if key in shift_chars:
        shift_base_key[key] = piano_keys[i - 1]

# État des touches pressées
pressed_keys = set()

def press_key(key):
    if key in pressed_keys:
        return
    pressed_keys.add(key)
    if key in shift_chars:
        base_key = shift_base_key.get(key, key.lower())
        keyboard.press('shift')
        keyboard.press(base_key)
        keyboard.release('shift')
    else:
        keyboard.press(key)

def release_key(key):
    if key not in pressed_keys:
        return
    pressed_keys.remove(key)
    if key in shift_chars:
        base_key = shift_base_key.get(key, key.lower())
        keyboard.release(base_key)
    else:
        keyboard.release(key)

# -------- PRÉCONVERSION MIDI --------
def preconvert_midi(file_path):
    midi = mido.MidiFile(file_path)
    events = []
    current_time = 0.0

    for msg in midi:
        current_time += msg.time
        if msg.type == 'note_on' and msg.velocity > 0:
            if msg.note in note_to_key:
                heapq.heappush(events, (current_time, 'press', note_to_key[msg.note]))
        elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
            if msg.note in note_to_key:
                heapq.heappush(events, (current_time, 'release', note_to_key[msg.note]))
    return events


# -------- LECTURE ULTRA-PRÉCISE --------
is_running = False
play_thread = None

midi_events = []

def play_events(events):
    global is_running
    start_time = time.perf_counter()
    while events and is_running:
        t, action, key = heapq.heappop(events)
        wait_time = t - (time.perf_counter() - start_time)
        if wait_time > 0:
            if wait_time > 0.002:
                time.sleep(wait_time - 0.001)
            while (time.perf_counter() - start_time) < t:
                pass
        if action == 'press':
            press_key(key)
        elif action == 'release':
            release_key(key)
    print("✅ Lecture terminée.")

def start_song(midi_path):
    global is_running, play_thread, midi_events
    midi_events = preconvert_midi(midi_path)
    print(f"{len(midi_events)} événements MIDI chargés pour {midi_path}.")
    is_running = True
    events_copy = list(midi_events)
    heapq.heapify(events_copy)
    play_thread = threading.Thread(target=play_events, args=(events_copy,))
    play_thread.start()

def stop_song():
    global is_running
    if is_running:
        is_running = False
        print("⏸ Lecture stoppée.")

# Hotkey pour stopper
keyboard.add_hotkey(stop_key, lambda: stop_song())

print("🎹 Piano Bot prêt.")
print("Appuie sur une touche 0-9 pour lancer un morceau. Appuie sur F8 pour stopper.")

# Boucle principale
while True:
    for num, path in midi_files.items():
        if keyboard.is_pressed(num) and not is_running:
            print(f"▶ Lecture de {path}")
            start_song(path)
            while is_running:  # Attente fin ou stop
                time.sleep(0.05)
            print("🎼 Choisis un autre morceau (0-9).")
    time.sleep(0.05)
