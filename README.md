# Voice Assistant

Edit text in current window by giving voice instructions to GPT-3.

## Start

- `pipenv install`
- download and extract `vosk` models
- add `OPENAI_API_KEY` to `.env` file
- `pipenv shell`
- `sudo -E python main.py`

## Usage

- put the cursor into the text input that supports `ctrl+a`, `ctrl+c` and `ctrl+v`
- press `alt gr` (right alt key) to copy text and give edit instructions
- the edited result will be pasted back to the input
