#!/usr/bin/env python3

import argparse
import os
import queue
import sounddevice as sd
import vosk
import sys
import pyperclip
import keyboard
import beepy
import pygame as pg
import openai
import time
import json
import re
# import pyautogui # requires `xhost + local:` to work for root

def copy():
    # pyautogui.hotkey('ctrl', 'a')
    # pyautogui.hotkey('ctrl', 'c')

    keyboard.send('ctrl+a')
    keyboard.send('ctrl+c')
    text = pyperclip.paste()

    # keyboard.press('ctrl')
    # time.sleep(0.1)
    # keyboard.press('a')
    # time.sleep(0.1)
    # keyboard.release('a')
    # time.sleep(0.1)
    # keyboard.press('c')
    # time.sleep(0.1)
    # keyboard.release('c')
    # time.sleep(0.1)
    # keyboard.release('ctrl')
    # time.sleep(0.1)

    text = pyperclip.paste()
    return text

class Stt:
    def _int_or_str(self, text):
        """Helper function for argument parsing."""
        try:
            return int(text)
        except ValueError:
            return text

    def init(self):
        parser = argparse.ArgumentParser(add_help=False)
        parser.add_argument(
            '-l', '--list-devices', action='store_true',
            help='show list of audio devices and exit')
        args, remaining = parser.parse_known_args()
        if args.list_devices:
            print(sd.query_devices())
            parser.exit(0)
        parser = argparse.ArgumentParser(
            description=__doc__,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            parents=[parser])
        parser.add_argument(
            '-f', '--filename', type=str, metavar='FILENAME',
            help='audio file to store recording to')
        parser.add_argument(
            '-m', '--model', type=str, metavar='MODEL_PATH',
            help='Path to the model')
        parser.add_argument(
            '-d', '--device', type=self._int_or_str,
            help='input device (numeric ID or substring)')
        parser.add_argument(
            '-r', '--samplerate', type=int, help='sampling rate')
        args = parser.parse_args(remaining)

        if args.model is None:
            args.model = "model"
        if not os.path.exists(args.model):
            print ("Please download a model for your language from https://alphacephei.com/vosk/models")
            print ("and unpack as 'model' in the current folder.")
            parser.exit(0)
        if args.samplerate is None:
            device_info = sd.query_devices(args.device, 'input')
            # soundfile expects an int, sounddevice provides a float:
            args.samplerate = int(device_info['default_samplerate'])

        model = vosk.Model(args.model)

        if args.filename:
            dump_fn = open(args.filename, "wb")
        else:
            dump_fn = None

        self.model = model
        self.args = args
        self.dump_fn = dump_fn
        print('initialized', args.samplerate, args.device)

    def _callback(self, indata, frames, time, status):
        """This is called (from a separate thread) for each audio block."""
        q = self.q
        if status:
            print(status, file=sys.stderr)
        q.put(bytes(indata))

    def record_once(self):
        self.q = queue.Queue()
        args = self.args
        model = self.model
        dump_fn = self.dump_fn
        q = self.q

        try:
            with sd.RawInputStream(samplerate=args.samplerate, blocksize = 8000, device=args.device, dtype='int16',
                                    channels=1, callback=self._callback):

                    rec = vosk.KaldiRecognizer(model, args.samplerate)
                    while True:
                        if keyboard.is_pressed('esc'):
                            return
                        data = q.get()
                        if rec.AcceptWaveform(data):
                            res = rec.Result()
                            r = json.loads(res)['text']
                            print('Text:', r)
                            return r
                        else:
                            res = rec.PartialResult()
                            r = json.loads(res)['partial']
                            print('Partial:', r)
                            words = r.split(' ')
                            if words[-1] == 'enter':
                                return re.sub(' enter\s*$', '', r)
                        if dump_fn is not None:
                            dump_fn.write(data)
        except BaseException as err:
            print('Could not record', err)
            return None

class Osd:
    pass

class App:
    def __init__(self, stt):
        self.stt = stt
        self.is_running = False

    def start_edit(self):
        if self.is_running: return
        self.is_running = True
        old_clipboard = pyperclip.paste()
        text = copy()
        keyboard.call_later(lambda: beepy.beep(sound=1), delay=0)
        print('=' * 60)
        print('-' * 40, 'Edit text:')
        print(f'{text[0:60]}...')
        # return

        instruction = self.stt.record_once()
        if instruction is None:
            print('CANCELED')
            pyperclip.copy(old_clipboard)
            keyboard.call_later(lambda: beepy.beep(sound=3), delay=0)
            self.is_running = False
            return

        keyboard.call_later(lambda: beepy.beep(sound=3), delay=0)
        print('=' * 60)
        print('-' * 40, 'Edit text:')
        print(f'{text[0:60]}...')
        print('-' * 40, 'Instruction:')
        print(instruction)


        pg.init()
        info = pg.display.Info()
        screen = pg.display.set_mode((info.current_w, 200))
        screen_rect = screen.get_rect()
        font = pg.font.Font(None, 45)
        clock = pg.time.Clock()
        color = (250, 250, 250)

        txt = font.render(f'{instruction} [{text[0:60]}...]', True, color)
        screen.fill((30, 30, 30))
        screen.blit(txt, txt.get_rect(center=screen_rect.center))
        pg.display.flip()


        response = openai.Edit.create(
            engine="text-davinci-edit-001",
            input=text,
            instruction=instruction,
            temperature=0.7,
            top_p=0.9
        )
        pg.quit()
        if keyboard.is_pressed('esc'):
            print('CANCELED')
            pyperclip.copy(old_clipboard)
            keyboard.call_later(lambda: beepy.beep(sound=3), delay=0)
            self.is_running = False
            return

        print(response)
        choice = response.choices[0].text
        print()

        pyperclip.copy(choice)
        keyboard.send('ctrl+a')
        keyboard.send('ctrl+v')

        time.sleep(0.1)
        pyperclip.copy(old_clipboard)
        keyboard.call_later(lambda: beepy.beep(sound=0), delay=0)
        self.is_running = False
        return

stt = Stt()
app = App(stt)

def main():
    openai.api_key = os.getenv("OPENAI_API_KEY")
    if (openai.api_key is None or openai.api_key == ''):
        raise BaseException('no OPENAI_API_KEY')

    keyboard.send('esc') # error fast if no root
    stt.init()
    keyboard.call_later(lambda: beepy.beep(sound=3), delay=0) # sound hint that app started

    keyboard.on_release_key('alt gr', lambda evt: app.start_edit())

    try:
        keyboard.wait()
    except KeyboardInterrupt:
        print('\nDone')

main()
