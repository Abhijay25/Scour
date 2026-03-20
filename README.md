# Scour

A TUI tool for competitive research — searches the web, extracts rich content via Tinyfish AI, and synthesizes a report using Gemini.

## Requirements

- Python 3.11+
- API keys for:
  - [Serper](https://serper.dev) — web search
  - [Tinyfish](https://tinyfish.ai) — AI web extraction
  - [Google AI Studio](https://aistudio.google.com) — Gemini analysis

## Install

```bash
curl -sSL https://raw.githubusercontent.com/your-username/Scour/main/install.sh | bash
```

Then add your API keys to `~/.config/scour/.env` and run:

```bash
scour
```

## Manual Setup (alternative)

```bash
git clone https://github.com/your-username/Scour
cd Scour
python -m venv .venv
source .venv/bin/activate
pip install -e .
mkdir -p ~/.config/scour
cp .env.example ~/.config/scour/.env
# Edit ~/.config/scour/.env with your API keys
```

## Usage

Type `/search <your query>` in the TUI. Reports are saved to `~/.local/share/scour/results/`.
