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

---

## 🛡️ Philosophy

> **"Safety is not optional — it is the foundation."**

Combius was built on a single principle: **maximum effectiveness through maximum safety**. Every feature, every delay, every randomization is designed to make the bot behave indistinguishably from a human user. This isn't just about avoiding bans — it's about respecting the platform and operating with surgical precision.

---

## ✨ Features

| Category | Feature | Status |
|---|---|---|
| **🧠 Intelligence** | Human-like behavior engine with natural pauses, jitter, and activity patterns | ✅ |
| **🔄 Multi-Token** | Run unlimited Discord tokens simultaneously | ✅ |
| **📡 Multi-Channel** | Distribute commands across channels | ✅ |
| **💎 Gems** | Auto-scan inventory, discover gems, equip best tier per type | ✅ |
| **📦 Lootboxes** | Auto-open all with `owo lb all`, batch processing | ✅ |
| **📦 Crates** | Auto-open all with `owo wc all` | ✅ |
| **💰 Sellall** | Smart sellall with variance, cooldown, and post-scan | ✅ |
| **🎁 Daily** | Auto-claim with configurable interval | ✅ |
| **🔔 Verification** | hCaptcha detection with browser auto-open | ✅ |
| **🌐 Browser** | Auto-open on Windows, macOS, Linux, **Termux** | ✅ |
| **📊 Statistics** | Live dashboard: commands/hr, uptime, rates | ✅ |
| **🛡️ Rate Limits** | Smart backoff, hourly cap (120/hr default) | ✅ |
| **🎭 Anti-Pattern** | Channel rotation, command variety, timing variance | ✅ |
| **⚡ Railway Ready** | Deploy in 2 minutes, zero config | ✅ |
| **📱 Termux** | Full Android support with termux-open-url | ✅ |

---

## 🚀 Quick Start

### Option 1: Local (Windows/Linux/macOS)

```bash
# Clone
git clone https://github.com/Mijatol-art/combius.git
cd combius

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your tokens and channel IDs

# Run
python combius.py
```

### Option 2: Termux
```bash
pkg update && pkg upgrade
pkg install python git
pip install -r requirements.txt

# Set up browser support
export BROWSER="termux-open-url '%s'"

# Configure and run
cp .env.example .env
nano .env   # Edit with your tokens
python combius.py
```

### Option 3: Railsway (cloud)
1. Fork this repo to GitHub
2. Go to railway.app → New Project → Deploy from GitHub
3. Add all env vars from .env.example in Railway Dashboard → Variables
4. Deploy! That's it.

# 🤝 Contributing
Combius is a proprietary tool for education ONLY!.
If you've discovered a improvement, or improved it open a discussion.
<p align="center">
  <img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&height=100&section=footer&text=WutDaDev&fontSize=30&fontAlignY=70" />
</p>