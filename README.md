# Scour

Scour is a terminal tool for competitive and market research. Give it a plain-English query and it searches the web, visits each competitor's actual website, and comes back with a structured analysis — strengths, weaknesses, market positioning, and an executive summary saved to your machine.

It's built for anyone who needs to quickly understand a market, find competitors, or research a space — without opening a dozen browser tabs.

---

## What it looks like

You type a query like:

```
/search SaaS tools for AI-assisted grading for teachers
```

And Scour returns:

- **Bottom Line** — a 2-3 sentence executive summary with the single most important insight
- **Positioning Statement** — an opinionated one-liner on where to compete
- **Competitive Edge** — ideas to steal, pitfalls to avoid, and market gaps
- **Per-competitor breakdowns** — strengths, weaknesses, business model, and traction signals for each competitor
- **Dig Deeper** — follow-up queries to explore adjacent angles

Results link directly to each competitor's own website — no listicle aggregators or "Top 10" roundup pages.

Reports are saved as Markdown files you can open any time.

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
| `/search <query>` | Run a competitive research search |
| `/search -n <count> <query>` | Control the number of results (2-15, default 5) |
| `/history` | Browse your saved reports |
| `/copy` | Copy the current report's markdown to clipboard |
| `/open` | Open the reports folder in your file manager |
| `/rerun` | Re-run the search for a previewed report |
| `/delete` | Delete the selected report in history view |
| `/tips` | Tips for writing better queries |
| `/help` | Show the help screen |
| `/clear` | Return to the home screen |
| `/quit` | Exit |

**Tips:**
- Queries don't need quotes — just type naturally
- The analysis adapts to your intent: ask about pricing and get pricing comparisons, ask about UX and get UX insights
- Include URLs to anchor results: `/search stem cells similar to https://example.com`
- Stack qualifiers for specificity: `/search bootstrapped B2B SaaS for HR in Europe`
- Press `Up` / `Down` to cycle through previous commands
- Press `Escape` to go back
- Press `Shift+Tab` to jump to the latest results

Reports are saved as Markdown to `~/.local/share/scour/results/` and viewable any time via `/history`. The history preview is a full-screen scrollable Markdown view — press `Escape` to go back.

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
