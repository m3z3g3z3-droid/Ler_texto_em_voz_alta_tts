#!/usr/bin/env python3
# uso  python3 ler.py livrotexto.txt
# Dependências do sistema:
# - python >= 3.8
# - espeak-ng
# sudo pacman -S python espeak-ng
# sudo apt install python3 espeak-ng
# Dependências Python (biblioteca padrão):
# - curses
# - subprocess
# - time
# - sys
# - re
# - textwrap
# - json
# - os
# - hashlib
#!/usr/bin/env python3
#
# Dependências do sistema:
#   - python >= 3.8
#   - espeak-ng
#
# Dependências Python (stdlib):
#   - curses
#   - subprocess
#   - time
#   - sys
#   - re
#   - textwrap
#   - json
#   - os
#   - hashlib
#

import curses
import subprocess
import time
import sys
import re
import textwrap
import json
import os
import hashlib

VOICE = "pt-br"
BASE_SPEED = 160
SAVE_DIR = os.path.expanduser("~/.local/share/tts_reader")

def split_sentences(text):
    return [s.strip() for s in re.split(r'(?<=[.!?])\s+', text) if s.strip()]

def speak_sentence(sentence, speed):
    return subprocess.Popen(
        ["espeak-ng", "-v", VOICE, "-s", str(speed), sentence],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

def file_id(path):
    return hashlib.sha1(path.encode()).hexdigest()

def save_path(filename):
    os.makedirs(SAVE_DIR, exist_ok=True)
    base = os.path.basename(filename)
    return os.path.join(SAVE_DIR, f"{base}.{file_id(filename)}.json")

def save_state(path, pos, speed):
    with open(path, "w") as f:
        json.dump({"sentence": pos, "speed": speed}, f)

def load_state(path):
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)

def draw_progress(stdscr, pos, total, y, w):
    bar_width = max(10, w - 12)
    filled = int(bar_width * (pos + 1) / total)
    bar = "█" * filled + "░" * (bar_width - filled)
    stdscr.addstr(y, 0, f"[{bar}] {pos+1}/{total}")

def main(stdscr, filename):
    curses.curs_set(0)
    stdscr.nodelay(True)
    stdscr.keypad(True)

    with open(filename, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    sentences = split_sentences(text)
    total = len(sentences)

    savefile = save_path(filename)
    state = load_state(savefile)

    pos = state["sentence"] if state else 0
    speed = state["speed"] if state else BASE_SPEED
    paused = False
    proc = None

    while True:
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        wrapper = textwrap.TextWrapper(width=w - 2)

        start = max(0, pos - 4)
        y = 0
        for i in range(start, min(start + 8, total)):
            for line in wrapper.wrap(sentences[i]):
                if i == pos:
                    stdscr.addstr(y, 0, line, curses.A_REVERSE)
                else:
                    stdscr.addstr(y, 0, line)
                y += 1
                if y >= h - 4:
                    break

        draw_progress(stdscr, pos, total, h - 3, w)
        stdscr.addstr(
            h - 2, 0,
            f"Velocidade: {speed} | SPACE pausa | ← → navega | s salva | q sai"
        )
        stdscr.refresh()

        if not paused and proc is None:
            proc = speak_sentence(sentences[pos], speed)

        key = stdscr.getch()

        if key == ord('q'):
            save_state(savefile, pos, speed)
            if proc:
                proc.terminate()
            return

        elif key == ord(' '):
            paused = not paused
            if paused and proc:
                proc.terminate()
                proc = None

        elif key in (ord('n'), curses.KEY_RIGHT):
            if proc:
                proc.terminate()
            pos = min(pos + 1, total - 1)
            proc = None
            save_state(savefile, pos, speed)

        elif key in (ord('p'), curses.KEY_LEFT):
            if proc:
                proc.terminate()
            pos = max(pos - 1, 0)
            proc = None
            save_state(savefile, pos, speed)

        elif key == curses.KEY_UP:
            speed += 10
            save_state(savefile, pos, speed)

        elif key == curses.KEY_DOWN:
            speed = max(80, speed - 10)
            save_state(savefile, pos, speed)

        elif key == ord('s'):
            save_state(savefile, pos, speed)

        elif key == ord('r'):
            st = load_state(savefile)
            if st:
                pos = st["sentence"]
                speed = st["speed"]
                if proc:
                    proc.terminate()
                proc = None

        if proc and proc.poll() is not None:
            proc = None
            pos = min(pos + 1, total - 1)
            save_state(savefile, pos, speed)

        time.sleep(0.05)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: ./tts_reader.py texto.txt")
        sys.exit(1)

    curses.wrapper(main, sys.argv[1])

