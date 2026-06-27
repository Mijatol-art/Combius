<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=120&section=header&text=COMBIUS&fontSize=70&fontAlignY=35&animation=twinkling" width="100%"/>
</p>

<p align="center">
  <b>The Ultimate OWO Discord Selfbot Engine</b><br>
  <i>Safe · Smart · Fancy · Multi-Token</i>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?style=flat&logo=python" />
  <img src="https://img.shields.io/badge/Status-Stable-brightgreen?style=flat" />
  <img src="https://img.shields.io/badge/Termux-Supported-orange?style=flat&logo=android" />
  <img src="https://img.shields.io/badge/Railway-Ready-purple?style=flat&logo=railway" />
  <img src="https://img.shields.io/badge/License-Proprietary-red?style=flat" />
</p>
======

The ultimate OWO Discord selfbot engine.

This repo is for people who want a clean, safer selfbot with multi-token support and smart automation. It’s simple, efficient, and built to avoid dumb flags.

---

## Philosophy

"Safety is not optional. It’s the baseline."

Combius is built on one idea: keep it effective and keep it safe. Every delay, every random move, every check is there so the bot acts like a real user.

---

## Features

| Category | What it does |
|---|---|
| Intelligence | Human-like timing, pauses, jitter, and activity patterns |
| Multi-Token | Run multiple Discord tokens at once |
| Multi-Channel | Spread commands across channels to avoid spam |
| Gems | Auto-scan inventory and equip your best gems |
| Lootboxes | Auto-open lootboxes and crates |
| Sellall | Smart sellall with cooldowns and variance |
| Daily | Auto-claim daily rewards on a schedule |
| Verification | Detect hCaptcha and auto-open browser if needed |
| Browser | Works on Windows, macOS, Linux, Termux |
| Stats | Live command/hour and uptime tracking |
| Rate Limits | Smart backoff and hourly caps |
| Anti-Pattern | Channel rotation, command variety, timing variance |
| Railway Ready | Easy deploy for cloud hosting |
| Termux | Android-friendly browser support |

---

## Quick Start

Option 1: Local (Windows/Linux/macOS)

```bash
git clone https://github.com/WutDaDev/Combius.git
cd Combius
pip install -r requirements.txt
cp .env.example .env
# edit .env with your tokens and channel IDs
python combius.py
```

Option 2: Termux

```bash
pkg update && pkg upgrade
pkg install python git
pip install -r requirements.txt
export BROWSER="termux-open-url '%s'"
cp .env.example .env
nano .env
python combius.py
```

Option 3: Railway

1. Fork the repo on GitHub
2. Deploy from GitHub in Railway
3. Add all vars from `.env.example`
4. Deploy and run

---

# 🤝 Contributing
Combius is proprietary software for educational use only.
If you've found an improvement or made a change, open a discussion.
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=100&section=footer&text=WutDaDev&fontSize=30&fontAlignY=70" />
</p>