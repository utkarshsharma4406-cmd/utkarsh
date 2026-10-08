# Dental clinic receptionist demo

This project keeps the Python and LiveKit Agents prototype and adds a free,
no-API-key browser demo that is easier to try in GitHub Codespaces.

## Choose how to run it

### Free browser demo (recommended for Codespaces)

The text chat and scripted replies need no API key, paid service, or AI model
download. They use local Python rules for a few common questions and
appointment requests. This is **not a generative AI language model** and has
limited answers. The browser can optionally turn speech into text and read
replies aloud. Speech recognition depends on browser support and may send audio
to the browser vendor's service; check that service's terms before enabling it.
Typing avoids speech recognition. Spoken replies use a voice available to the
browser/device.

1. Open the project in your Codespace terminal.
2. Start the demo (this uses only Python's standard library):

   ```bash
   python local_demo.py
   ```

   If you have already installed the project's LiveKit dependencies, the same
   demo can also be started with `python agent.py demo`.

3. In VS Code, open the **Ports** tab. This project configures Codespaces to
   forward port `8000` privately. If it is not listed in the current Codespace,
   use **Forward a Port**, enter `8000`, and confirm the visibility is
   **Private**. Click the forwarded address to open the demo in a browser.
   The `.devcontainer/devcontainer.json` setting also requests port forwarding
   when a Codespace is created or configured from this project.
4. Type a message and click **Send**. If your browser supports speech
   recognition, click **Speak** and allow microphone access. Click **Stop
   voice** to stop a spoken reply.
5. Stop the Python server with `Ctrl+C`.

Try “What should I bring?”, “Are you open Saturday?”, and “I'd like to request
an appointment.” Use made-up names and phone numbers. The demo retains intake
details only in server memory while it runs. Details are not written to disk or
sent to a clinic; requests are never confirmed bookings.

### Original LiveKit voice-agent console

The original `python agent.py console` path still uses OpenAI for speech
recognition, language responses, and voice output. That may incur charges and
needs an API key, so it is optional and is not needed for the recommended free
demo. No OpenAI key or LiveKit dependency installation is needed to run
`python local_demo.py`.

If you choose to use that optional path, create a local `.env` from
`.env.example`, add your own `OPENAI_API_KEY`, and then run:

```bash
python agent.py console
```

Never commit `.env` or share its key; it is ignored by Git.

## Codespaces microphone limitations

A LiveKit `console` agent runs in the remote Codespace container. The container
usually cannot directly access the microphone attached to your laptop, so
`python agent.py console` may not find an audio device even when your browser
has a microphone.

The browser demo is different: it opens through the forwarded Codespaces
address, and the browser—not the Python container—requests microphone
permission. Microphone use generally needs a secure page (Codespaces forwarded
ports use HTTPS) and the browser's permission. Speech recognition is not
supported in every browser. Some browsers process recognition through their
own online service; it is not guaranteed to run locally or work offline. If it
doesn't work or you prefer not to use it, type in the message box. Browser
speech output also varies by device and installed voices.

## Resource check and model choice

The Codespace used to prepare this project reported 2 CPU cores, about 5.2 GiB
available memory, 19 GiB free workspace storage, and no GPU. A small
quantized CPU language model may fit, but speech recognition plus language
generation would use more memory and run slowly on two CPU cores. Model files
also need to be downloaded. To avoid unapproved downloads and keep this demo
simple and free, the no-key mode uses scripted rules instead of installing
models. No AI model is downloaded by `python agent.py demo`.

## Test

Run the automated conversation checks from the project folder:

```bash
python -m unittest discover -s tests -v
```

These checks cover general questions, unknown clinic information, appointment
intake, phone-number validation, emergency language, and the unconfirmed
booking behavior.

## Safety and limitations

- This is a prototype, not a real clinic receptionist or medical advice.
- It does not know a clinic's hours, address, prices, insurance, or availability.
- It does not diagnose symptoms. Contact a qualified professional for care;
  contact local emergency services for an immediate emergency.
- The local demo's conversation rules are intentionally limited. It cannot
  understand arbitrary questions like a full language model.
- Use fictional details. Data is kept only in memory, but anyone with access to
  the running demo or its forwarded port could interact with it. Keep the port
  private and stop the server when finished.

## Project files

- `local_demo.py` — free local web server and scripted conversation rules
- `agent.py demo` — starts the same demo from the existing LiveKit entry point
- `web/index.html` — browser chat, optional microphone input, and speech output
- `agent.py` — original LiveKit Agents/OpenAI voice pipeline
- `requirements.txt` — dependencies for the original LiveKit agent
- `.env.example` — template for the optional OpenAI path
- `tests/test_local_demo.py` — standard-library tests for the local demo
