# Scour

Scour is a terminal tool for competitive and market research. Give it a plain-English query and it searches the web, visits the most relevant pages, and comes back with a structured analysis — strengths, weaknesses, and a written report saved to your machine.

It's built for anyone who needs to quickly understand a market, find competitors, or research a space — without opening a dozen browser tabs.

---

## What it looks like

You type a query like:

```
/search SaaS tools for AI-assisted grading for teachers
```

And Scour returns a breakdown of the top competitors — what they do well, where they fall short, and how they compare. Reports are saved as Markdown files you can open any time.

---

## Before you start: API keys

Scour connects three services together. You'll need a free (or paid) account with each:

| Service | What it does | Get a key |
|---|---|---|
| **Serper** | Searches the web | [serper.dev](https://serper.dev) |
| **Tinyfish** | Reads and extracts page content | [tinyfish.ai](https://tinyfish.ai) |
| **Google AI Studio** | Analyzes and synthesizes the report | [aistudio.google.com](https://aistudio.google.com) |

All three have free tiers to get started. Once you have your keys, setup takes about two minutes.

> **Gemini note:** Scour uses `gemini-2.5-flash`. If your Google Cloud project has billing enabled, the free-tier quota for this model may be zero — you'll see a quota error on first run. To fix it, either enable a billing account on your project or check your quota limits at [aistudio.google.com](https://aistudio.google.com).

---

## Setup

### Option 1 — One-line install (recommended)

```bash
curl -sSL https://raw.githubusercontent.com/your-username/Scour/main/install.sh | bash
```

This installs Scour via `pipx` and creates a config file at `~/.config/scour/.env`. Open that file and paste in your three API keys:

```
SERPER_API_KEY=your_key_here
TINYFISH_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
```

Then run:

```bash
scour
```

### Option 2 — Manual setup

If you prefer to set things up yourself:

```bash
git clone https://github.com/your-username/Scour
cd Scour
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Create the config file:

```bash
mkdir -p ~/.config/scour
cat > ~/.config/scour/.env << EOF
SERPER_API_KEY=your_key_here
TINYFISH_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
EOF
```

Then run:

```bash
source .venv/bin/activate
scour
```

---

## Using Scour

Once inside, type commands into the bar at the bottom of the screen:

| Command | What it does |
|---|---|
| `/search <your query>` | Run a research search |
| `/history` | Browse your saved reports |
| `/help` | Show the help screen |
| `/clear` | Return to the home screen |
| `/quit` | Exit |

**Tips:**
- Queries don't need quotes — just type naturally
- The analysis adapts to your intent: UX-focused queries get UX-focused reports, business-focused queries get business-focused reports
- Press `Up` / `Down` to cycle through previous commands
- Press `Escape` to go back

Reports are saved as Markdown to `~/.local/share/scour/results/` and viewable any time via `/history`.

---

## Troubleshooting

Errors appear as notifications in the app. Here's what they mean:

| Error | Fix |
|---|---|
| `Gemini quota exhausted` | Free-tier limit hit — wait for reset or enable billing at aistudio.google.com |
| `Gemini API key invalid` | Check `GEMINI_API_KEY` in `~/.config/scour/.env` |
| `Serper rate limit exceeded` | Check your plan at serper.dev |
| `Serper API key invalid` | Check `SERPER_API_KEY` in `~/.config/scour/.env` |
| `No content could be extracted` | Tinyfish couldn't reach the pages — check your `TINYFISH_API_KEY` or try a different query |

---

## Requirements

- Python 3.11+
- macOS or Linux
