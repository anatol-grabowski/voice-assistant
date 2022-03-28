# Voice Assistant

Edit text in current window by giving voice instructions to GPT-3.

## Start

- sign up for [openai API](https://beta.openai.com/account/api-keys)
  - email and phone number verification is required
- add `OPENAI_API_KEY` to `.env` file
- unpack `vosk` english language [model](https://alphacephei.com/vosk/models) (e.g. vosk-model-en-us-0.22) to the application directory
  - if 1.8GB model is used then the app takes ~5.5GB in RAM
- `pipenv install`
- `pipenv shell`
- `sudo -E python main.py --model vosk-model-en-us-0.22 --device 5`
  - running as root is required for keyboard hooks to work
  - `-E` flag is required to pass `OPENAI_API_KEY` to the root shell
  - specify your own model derictory
  - you may need to experiment with sound input device ids (starting from 0)
    - some useful commands to debug devices: `pactl list sources | grep 'Name: '`, `arecord -l`

## Usage

- put the cursor into the text input that supports `ctrl+a`, `ctrl+c` and `ctrl+v`
- press `alt gr` (right alt key) to copy text and give edit instructions
- the edited result will be pasted back into the input
