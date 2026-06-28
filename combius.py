#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║                    C O M B I U S   v4.0                     ║
║                                                              ║
║     The Ultimate OWO Discord Selfbot — Safe | Smart | Fancy  ║
║                                                              ║
║     "Safety is not optional. It is the foundation."          ║
╚══════════════════════════════════════════════════════════════╝

Features:
   Multi-layer Anti-Detection 
   Multi-Token / Multi-Channel
   Auto-Inventory Scanner (parses owo inv)
   Auto Lootbox (owo lb all) + Crate (owo wc all)
   Auto Smart Gem Equipping (best tier per type)
   Auto Sellall with smart cooldown
   Auto Daily Claim
   Human-like Randomized Behavior
   Auto Browser Open (Windows/Linux/Mac/Termux)
   Human Verification Alert + Auto Browser
   Dynamic Delay Scaling
   Rate Limit Protection
   Live Statistics Dashboard

Author: Combius Security Team
License: Proprietary — Authorized Pentest Use Only
"""

import os
import sys
import json
import re
import math
import random
import time
import threading
import platform
import subprocess
import signal
import requests
from datetime import datetime, timedelta, time as dt_time
from pathlib import Path
from collections import deque
from typing import Optional, Dict, List, Tuple, Any
import components_v2

# ============================================================
# SECTION 0: ENVIRONMENT & CONFIG LOADER
# ============================================================

try:
    from dotenv import load_dotenv
    if not os.environ.get('RAILWAY_PROJECT_ID'):
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
except ImportError:
    pass

def env_bool(k: str, d: bool = False) -> bool:
    return os.environ.get(k, str(d)).strip().lower() in ('true', '1', 'yes', 'on', 'enabled')

def env_int(k: str, d: int = 0) -> int:
    try: return int(os.environ.get(k, d))
    except: return d

def env_float(k: str, d: float = 0.0) -> float:
    try: return float(os.environ.get(k, d))
    except: return d

def env_list(k: str, d: str = "") -> List[str]:
    return [x.strip() for x in os.environ.get(k, d).split(',') if x.strip()]

def env_json(k: str, d: str = "{}") -> dict:
    try: return json.loads(os.environ.get(k, d))
    except: return {}


# ============================================================
# SECTION 1: CONFIGURATION (All from .env)
# ============================================================

CONFIG = {
    # --- Core ---
    "DISCORD_TOKENS": env_list('DISCORD_TOKENS'),
    "CHANNEL_IDS": [c for c in env_list('CHANNEL_IDS') if c.isdigit()],
    
    # --- Timing (Human-like randomization) ---
    "MIN_DELAY": env_int('MIN_DELAY', 20),
    "MAX_DELAY": env_int('MAX_DELAY', 40),
    "DELAY_JITTER": env_float('DELAY_JITTER', 0.3),       # 30% jitter
    "DELAY_SPIKE_CHANCE": env_float('DELAY_SPIKE_CHANCE', 0.05),  # 5% chance of long pause
    "DELAY_SPIKE_MAX": env_int('DELAY_SPIKE_MAX', 120),   # Max spike pause (2 min)
    
    # --- Sellall ---
    "SELLALL_INTERVAL": env_int('SELLALL_INTERVAL', 100),
    "SELLALL_COOLDOWN": env_int('SELLALL_COOLDOWN', 600),
    "SELLALL_VARIANCE": env_int('SELLALL_VARIANCE', 15),   # ±15 commands variance
    
    # --- Gems ---
    "GEM_ENABLED": env_bool('GEM_ENABLED', True),
    "GEM_IDS": [int(x) for x in env_list('GEM_IDS', '51,52,53,56') if x.isdigit()],
    "AUTO_SCAN_GEMS": env_bool('AUTO_SCAN_GEMS', True),
    "MIN_GEM_TIER": env_int('MIN_GEM_TIER', 3),             # 3=Rare minimum
    
    # --- Inventory Management ---
    "INVENTORY_CHECK_INTERVAL": env_int('INVENTORY_CHECK_INTERVAL', 20),
    "AUTO_OPEN_LOOTBOXES": env_bool('AUTO_OPEN_LOOTBOXES', True),
    "AUTO_OPEN_CRATES": env_bool('AUTO_OPEN_CRATES', True),
    "AUTO_OPEN_FABLED": env_bool('AUTO_OPEN_FABLED', True),
    
    # --- Daily & Claim ---
    "AUTO_CLAIM": env_bool('AUTO_CLAIM', True),
    "CLAIM_INTERVAL_HOURS": env_int('CLAIM_INTERVAL_HOURS', 8),
    
    # --- Safety & Anti-Detection ---
    "VERIFY_SOUND": env_bool('VERIFY_SOUND', True),
    "AUTO_BROWSER": env_bool('AUTO_BROWSER', True),
    "MAX_COMMANDS_PER_HOUR": env_int('MAX_COMMANDS_PER_HOUR', 120),
    "RATE_LIMIT_BACKOFF": env_int('RATE_LIMIT_BACKOFF', 30),
    "ANTI_PATTERN_ROTATION": env_bool('ANTI_PATTERN_ROTATION', True),
    
    # --- Captcha ---
    "CAPTCHA_SERVICE": os.environ.get('CAPTCHA_SERVICE', 'manual'),
    "CAPMONSTER_API_KEY": os.environ.get('CAPMONSTER_API_KEY', ''),
    "TWOCAPTCHA_API_KEY": os.environ.get('TWOCAPTCHA_API_KEY', ''),
    "OCR_SPACE_API_KEY": os.environ.get('OCR_SPACE_API_KEY', ''),
    "IMAGE_CAPTCHA_ENABLED": env_bool('IMAGE_CAPTCHA_ENABLED', True),
    "CAPTCHA_IMAGE_LETTER_COUNT": env_int('CAPTCHA_IMAGE_LETTER_COUNT', 6),
    "OAH_CAPTCHA_KEYWORDS": env_list('OAH_CAPTCHA_KEYWORDS', 'enter the text,captcha image,image captcha,random text'),
    "OAH_CAPTCHA_MODE": os.environ.get('OAH_CAPTCHA_MODE', 'manual'),
    
    # --- UI ---
    "THEME": os.environ.get('THEME', 'dark'),
    "SHOW_STATS": env_bool('SHOW_STATS', True),
    "STATS_INTERVAL": env_int('STATS_INTERVAL', 50),
    
    # --- Advanced Safety ---
    "MAX_CONSECUTIVE_SAME_CHANNEL": env_int('MAX_CONSECUTIVE_SAME_CHANNEL', 3),
    "MIN_BREAK_MINUTES": env_int('MIN_BREAK_MINUTES', 0),   # Scheduled breaks
    "BREAK_INTERVAL_MINUTES": env_int('BREAK_INTERVAL_MINUTES', 0),
    "TOKEN_ROTATION": env_bool('TOKEN_ROTATION', False),

    # --- OWO Special Commands ---
    "OAH_ENABLED": env_bool('OAH_ENABLED', True),
    "OAH_COMMAND": os.environ.get('OAH_COMMAND', 'owo autohunt'),
    "OAH_DURATION_SECONDS": env_int('OAH_DURATION_SECONDS', 120),
    "OAH_REST_MINUTES": env_int('OAH_REST_MINUTES', 30),

    "OWO_PIKU_ENABLED": env_bool('OWO_PIKU_ENABLED', True),
    "OWO_RUN_ENABLED": env_bool('OWO_RUN_ENABLED', True),
    "OWO_PIKU_DAILY_TIME": os.environ.get('OWO_PIKU_DAILY_TIME', '13:30'),
    "OWO_RUN_DAILY_TIME": os.environ.get('OWO_RUN_DAILY_TIME', '13:30'),

    "OWO_B_MIN_DELAY": env_int('OWO_B_MIN_DELAY', 0),
    "OWO_B_MAX_DELAY": env_int('OWO_B_MAX_DELAY', 0),
    "OWO_B_DELAY_JITTER": env_float('OWO_B_DELAY_JITTER', -1.0),
    # User ID to ping when a "⚠ are you ..." style flag appears. Set to your numeric user id.
    "ALERT_PING_USER_ID": os.environ.get('ALERT_PING_USER_ID', ''),
    # Path to log file where flagged message JSON lines will be appended
    "ALERT_LOG_FILE": os.environ.get('ALERT_LOG_FILE', 'flagged_messages.log'),
}

# Per-token gem overrides
TOKEN_GEMS_OVERRIDES: Dict[str, List[int]] = {}
for key, val in os.environ.items():
    if key.startswith('TOKEN_GEMS_'):
        prefix = key[11:]
        try:
            ids = [int(x) for x in val.split(',') if x.strip().isdigit()]
            if ids: TOKEN_GEMS_OVERRIDES[prefix] = ids
        except: pass

# Validation
if not CONFIG["DISCORD_TOKENS"]:
    print("[!] No DISCORD_TOKENS set in environment!")
    print("[!] Create a .env file or set env vars on Railway")
    sys.exit(1)
if not CONFIG["CHANNEL_IDS"]:
    print("[!] No valid CHANNEL_IDS set in environment!")
    sys.exit(1)


# ============================================================
# SECTION 2: CONSTANTS & REFERENCE DATA
# ============================================================

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Gem Ranges
HUNTING_GEMS  = list(range(51, 58))    # 51-57: Common -> Fabled
EMPOWERING_GEMS = list(range(65, 72))  # 65-71: Common -> Fabled
LUCKY_GEMS    = list(range(72, 79))    # 72-78: Common -> Fabled
ALL_GEM_IDS   = HUNTING_GEMS + EMPOWERING_GEMS + LUCKY_GEMS

# Item IDs
LOOTBOX_ID = 50
FABLED_LOOTBOX_ID = 49
WEAPON_CRATE_ID = 100

# Gem tier names for display
GEM_NAMES = {
    51: "Cmn Hunt", 52: "Unc Hunt", 53: "Rare Hunt", 54: "Epic Hunt",
    55: "Myth Hunt", 56: "Legd Hunt", 57: "Fabl Hunt",
    65: "Cmn Emp",  66: "Unc Emp",  67: "Rare Emp",  68: "Epic Emp",
    69: "Myth Emp", 70: "Legd Emp", 71: "Fabl Emp",
    72: "Cmn Luck", 73: "Unc Luck", 74: "Rare Luck", 75: "Epic Luck",
    76: "Myth Luck",77: "Legd Luck",78: "Fabl Luck",
}

GEM_TIER_LEVEL = {**{i: i-50 for i in range(51, 58)},   # 51->1, 57->7
                  **{i: i-64 for i in range(65, 72)},    # 65->1, 71->7
                  **{i: i-71 for i in range(72, 79)}}    # 72->1, 78->7

# OWO Command pool for human-like variety
CMD_POOL = {
    "core": ["owo"] * 5 + ["owo hunt"] * 4 + ["owo battle"] * 3,
    "actions": ["owo dig", "owo fish", "owo pray", "owo b", "owo bg"],
    "social": ["owo profile", "owo cookies", "owo cowoncy"],
    "rare": ["owo slots 10", "owo coinflip head 10", "owo coinflip tail 10"],
}

# Safety channel check intervals (seconds)
VERIFY_CHECK_INTERVAL = 5


# ============================================================
# SECTION 3: UTILITY FUNCTIONS
# ============================================================

class FancyConsole:
    """Fancy terminal output with colors and theming."""
    
    COLORS = {
        "dark": {
            "primary": "\033[96m",      # Cyan
            "secondary": "\033[95m",    # Magenta  
            "success": "\033[92m",      # Green
            "warning": "\033[93m",      # Yellow
            "error": "\033[91m",        # Red
            "dim": "\033[90m",          # Gray
            "bold": "\033[1m",
            "reset": "\033[0m",
            "bg": "\033[40m",
        },
        "light": {
            "primary": "\033[94m",
            "secondary": "\033[35m",
            "success": "\033[32m",
            "warning": "\033[33m",
            "error": "\033[31m",
            "dim": "\033[37m",
            "bold": "\033[1m",
            "reset": "\033[0m",
            "bg": "\033[47m",
        }
    }
    
    def __init__(self, theme="dark"):
        self.theme = theme if theme in self.COLORS else "dark"
        self.c = self.COLORS[self.theme]
    
    def primary(self, text): return f"{self.c['primary']}{text}{self.c['reset']}"
    def secondary(self, text): return f"{self.c['secondary']}{text}{self.c['reset']}"
    def success(self, text): return f"{self.c['success']}{text}{self.c['reset']}"
    def warning(self, text): return f"{self.c['warning']}{text}{self.c['reset']}"
    def error(self, text): return f"{self.c['error']}{text}{self.c['reset']}"
    def dim(self, text): return f"{self.c['dim']}{text}{self.c['reset']}"
    def bold(self, text): return f"{self.c['bold']}{text}{self.c['reset']}"
    def tag(self, username, text, color=None):
        c = color or self.c['primary']
        return f"{self.dim('[')}{c}{username}{self.dim(']')} {text}{self.reset()}"
    def reset(self): return self.c['reset']
    def header(self, text): return f"\n{self.c['bold']}{self.c['primary']}{'='*60}{self.c['reset']}\n{self.c['bold']}{self.c['secondary']}{text.center(60)}{self.c['reset']}\n{self.c['bold']}{self.c['primary']}{'='*60}{self.c['reset']}\n"

ui = FancyConsole(CONFIG["THEME"])


def open_browser(url: str) -> bool:
    """
    Open URL in default browser. Supports:
    - Windows (webbrowser)
    - Linux (webbrowser, xdg-open)
    - macOS (open)
    - Termux (termux-open-url)
    - Fallback: print link
    """
    system = platform.system().lower()
    
    # Termux check
    if os.path.exists("/data/data/com.termux") or "termux" in os.environ.get("PREFIX", ""):
        try:
            subprocess.run(["termux-open-url", url], timeout=5)
            print(ui.success("  🌐 Browser opened (Termux)"))
            return True
        except:
            pass
    
    # Standard webbrowser
    try:
        import webbrowser
        # Register termux browser if available
        if system == "linux" and os.path.exists("/data/data/com.termux/files/usr/bin/termux-open-url"):
            webbrowser.register("termux", None, webbrowser.GenericBrowser("termux-open-url"))
        
        opened = webbrowser.open(url, new=2)
        if opened:
            print(ui.success(f"  🌐 Browser opened: {url}"))
            return True
    except:
        pass
    
    # Manual fallback
    print(ui.warning(f"  🌐 Open this URL manually:"))
    print(ui.primary(f"     {url}"))
    return False


def local_time() -> str:
    return datetime.now().strftime('%H:%M:%S')


# ============================================================
# SECTION 4: DISCORD API LAYER (Safe, Rate-Limited)
# ============================================================

class DiscordAPI:
    """Thread-safe Discord HTTP API client with rate limit protection."""
    
    BASE = "https://discord.com/api/v9"
    
    def __init__(self, token: str):
        self.token = token
        self.session_headers = {
            "Content-Type": "application/json",
            "User-Agent": USER_AGENT,
            "Authorization": token,
            "Origin": "https://discord.com",
            "Referer": "https://discord.com/channels/@me",
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
        }
        self.last_request_time = 0
        self.min_request_gap = 0.5  # 500ms between requests minimum
        self.consecutive_ratelimits = 0
        self._cache = {}
        self._cache_ttl = 30
    
    def _rate_limit_safe(self):
        """Ensure we don't send requests too fast."""
        now = time.time()
        gap = now - self.last_request_time
        if gap < self.min_request_gap:
            time.sleep(self.min_request_gap - gap)
        self.last_request_time = time.time()
    
    def _handle_ratelimit(self, response) -> bool:
        """Handle rate limit response. Returns True if should retry."""
        if response.status_code == 429:
            try:
                data = response.json()
                retry_after = data.get('retry_after', 5)
                # Exponential backoff
                self.consecutive_ratelimits += 1
                wait = retry_after * (2 ** min(self.consecutive_ratelimits - 1, 4))
                print(ui.warning(f"  ⏱ Rate limited! Waiting {wait:.1f}s (burst #{self.consecutive_ratelimits})"))
                time.sleep(wait + 0.5)
                return True
            except:
                time.sleep(10)
                return True
        else:
            self.consecutive_ratelimits = 0
            return False
    
    def get(self, path: str, params: dict = None) -> Optional[requests.Response]:
        """Safe GET request."""
        self._rate_limit_safe()
        url = f"{self.BASE}{path}"
        if params:
            qs = "&".join(f"{k}={v}" for k, v in params.items())
            url = f"{url}?{qs}"
        try:
            r = requests.get(url, headers=self.session_headers, timeout=15)
            if self._handle_ratelimit(r):
                return self.get(path, params)
            return r
        except requests.exceptions.Timeout:
            print(ui.warning("  ⏱ Request timeout, retrying..."))
            time.sleep(5)
            return self.get(path, params)
        except Exception as e:
            print(ui.error(f"  ⚠ Request error: {e}"))
            return None
    
    def post(self, path: str, data: dict = None) -> Optional[requests.Response]:
        """Safe POST request."""
        self._rate_limit_safe()
        url = f"{self.BASE}{path}"
        try:
            r = requests.post(url, headers=self.session_headers, json=data or {}, timeout=15)
            if self._handle_ratelimit(r):
                return self.post(path, data)
            return r
        except requests.exceptions.Timeout:
            print(ui.warning("  ⏱ Request timeout, retrying..."))
            time.sleep(5)
            return self.post(path, data)
        except Exception as e:
            print(ui.error(f"  ⚠ Request error: {e}"))
            return None

    def click_component(self, component: Any) -> bool:
        """Click a parsed component button."""
        if not component or not getattr(component, 'is_clickable_button', False):
            return False

        return component.click(self.session_headers)
    
    def send_message(self, channel_id: str, content: str) -> bool:
        """Send a Discord message. Returns True on success."""
        r = self.post(f"/channels/{channel_id}/messages", {"content": content})
        if r and r.status_code == 200:
            return True
        return False
    
    def fetch_messages(self, channel_id: str, limit: int = 10) -> List[dict]:
        """Fetch recent messages."""
        r = self.get(f"/channels/{channel_id}/messages", {"limit": limit})
        if r and r.status_code == 200:
            return r.json()
        return []
    
    def get_me(self) -> Optional[dict]:
        """Get current user info."""
        r = self.get("/users/@me")
        if r and r.status_code == 200:
            return r.json()
        return None
    
    def get_username(self) -> str:
        """Get username: discriminator."""
        me = self.get_me()
        if me:
            return f"{me.get('username','?')}#{me.get('discriminator','0000')}"
        return "Unknown#0000"
    
    def get_user_id(self) -> Optional[str]:
        me = self.get_me()
        return me.get("id") if me else None


# ============================================================
# SECTION 5: INVENTORY PARSER
# ============================================================

class InventoryParser:
    """
    Parses OWO bot's inventory response to extract:
    - All gem IDs with quantities
    - Lootbox count
    - Fabled lootbox count
    - Weapon crate count
    
    OWO Inventory Format:
        **Inventory**
        49  × 2  ⠀Fabled Lootbox
        50  × 15 ⠀Lootbox
        51  × 3  ⠀Common Hunting Gem
        52  × 2  ⠀Uncommon Hunting Gem
        56  × 1  ⠀Legendary Hunting Gem
        65  × 1  ⠀Common Empowering Gem
        72  × 4  ⠀Common Lucky Gem
        100 × 8  ⠀Weapon Crate
    """
    
    @staticmethod
    def parse(messages: List[dict], own_user_id: str) -> dict:
        """Parse inventory from Discord messages."""
        result = {
            "success": False,
            "gem_ids": [],
            "gem_quantities": {},
            "lootbox_count": 0,
            "fabled_lootbox_count": 0,
            "crate_count": 0,
            "all_items": {},
        }
        
        for msg in messages:
            content = msg.get("content", "")
            author_id = msg.get("author", {}).get("id", "")
            
            # Skip own messages
            if author_id == own_user_id:
                continue
            
            # Check for inventory header
            if "**Inventory**" not in content and "Inventory" not in content:
                continue
            
            result["success"] = True
            
            # Parse each line
            lines = content.split('\n')
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Match: "ID  ×  COUNT  ⠀ItemName"
                match = re.search(r'(\d+)\s*[×xX]\s*(\d+)', line)
                if not match:
                    continue
                
                item_id = int(match.group(1))
                count = int(match.group(2))
                result["all_items"][item_id] = count
                
                # Categorize
                if item_id == LOOTBOX_ID:
                    result["lootbox_count"] = count
                elif item_id == FABLED_LOOTBOX_ID:
                    result["fabled_lootbox_count"] = count
                elif item_id == WEAPON_CRATE_ID:
                    result["crate_count"] = count
                elif item_id in ALL_GEM_IDS:
                    result["gem_ids"].append(item_id)
                    result["gem_quantities"][item_id] = count
            
            break  # Only first inventory response
        
        return result
    
    @staticmethod
    def get_best_gems(inv_data: dict, min_tier: int = 3) -> List[int]:
        """Get the best gem of each type (hunting, empowering, lucky) from inventory."""
        gems = inv_data.get("gem_ids", [])
        hunting = sorted([g for g in gems if g in HUNTING_GEMS], reverse=True)
        empowering = sorted([g for g in gems if g in EMPOWERING_GEMS], reverse=True)
        lucky = sorted([g for g in gems if g in LUCKY_GEMS], reverse=True)
        
        best = []
        for gem_list in [hunting, empowering, lucky]:
            for gem_id in gem_list:
                if GEM_TIER_LEVEL.get(gem_id, 0) >= min_tier:
                    best.append(gem_id)
                    break
        
        # Fallback: if none found, take any gems
        if not best and gems:
            best = sorted(gems, key=lambda g: GEM_TIER_LEVEL.get(g, 0), reverse=True)[:3]
        
        return best


# ============================================================
# SECTION 6: CAPTCHA SOLVER
# ============================================================

class CaptchaHandler:
    """Handles Discord hCaptcha challenges.

    Note: OAH captcha challenges may use randomized image text rather than
    standard hCaptcha flows. Future integration should include OCR-based
    solving from external modules like owo-dusk utils/image_to_text and
    utils/captcha_solver.
    """
    
    DISCORD_SITEKEY = "4c672d35-0701-42b2-88c3-78380b0db560"
    
    def __init__(self):
        self.service = CONFIG["CAPTCHA_SERVICE"]
        self.capmonster_key = CONFIG["CAPMONSTER_API_KEY"]
        self.twocaptcha_key = CONFIG["TWOCAPTCHA_API_KEY"]
        self.ocr_space_key = CONFIG["OCR_SPACE_API_KEY"]
        self.image_captcha_enabled = CONFIG["IMAGE_CAPTCHA_ENABLED"]
        self.captcha_image_letter_count = CONFIG["CAPTCHA_IMAGE_LETTER_COUNT"]
        self.oah_captcha_mode = CONFIG["OAH_CAPTCHA_MODE"]
    
    def solve(self, sitekey: str = DISCORD_SITEKEY, rqdata: str = "", 
              url: str = "https://discord.com/channels/@me") -> Optional[str]:
        """Solve captcha via configured service."""
        if self.service == "capmonster" and self.capmonster_key:
            return self._capmonster(sitekey, rqdata, url)
        elif self.service == "2captcha" and self.twocaptcha_key:
            return self._twocaptcha(sitekey, rqdata, url)
        else:
            return self._manual(sitekey, url)

    def solve_image(self, image_url: str) -> Optional[str]:
        if not self.image_captcha_enabled:
            return None
        if self.oah_captcha_mode == 'onnx':
            solution = self._onnx_solve(image_url)
            if solution:
                return solution
            if self.ocr_space_key:
                return self._ocr_space(image_url)
            return None
        if self.oah_captcha_mode == 'ocr_space':
            return self._ocr_space(image_url)
        return None

    def _onnx_solve(self, image_url: str) -> Optional[str]:
        try:
            import io
            import numpy as np
            from PIL import Image
            import onnxruntime
        except ImportError as e:
            print(ui.warning(f'  ⚠ ONNX solver unavailable: {e}'))
            return None

        model_path = "utils/captcha_solver/best.onnx"
        if not os.path.exists(model_path):
            print(ui.warning(f'  ⚠ ONNX model not found at {model_path}'))
            return None

        try:
            onnx_session = onnxruntime.InferenceSession(model_path, providers=["CPUExecutionProvider"])
        except Exception as e:
            print(ui.warning(f'  ⚠ Failed to load ONNX model: {e}'))
            return None

        try:
            r = requests.get(image_url, timeout=15)
            if r.status_code != 200:
                print(ui.error(f'  ⚠ Failed to fetch captcha image: {r.status_code}'))
                return None
            img_bytes = r.content
            image = Image.open(io.BytesIO(img_bytes)).convert('RGB')
            img_array = np.array(image)
        except Exception as e:
            print(ui.error(f'  ⚠ Error loading captcha image: {e}'))
            return None

        def letterbox(img_array, new_size=384, color=(114, 114, 114)):
            img = Image.fromarray(img_array)
            w, h = img.size
            scale = min(new_size / w, new_size / h)
            nw, nh = int(w * scale), int(h * scale)
            img_resized = img.resize((nw, nh), Image.BILINEAR)
            new_img = Image.new('RGB', (new_size, new_size), color)
            paste_x = (new_size - nw) // 2
            paste_y = (new_size - nh) // 2
            new_img.paste(img_resized, (paste_x, paste_y))
            return np.array(new_img)

        try:
            img = letterbox(img_array, 384)
            img = img.astype(np.float32) / 255.0
            img = np.transpose(img, (2, 0, 1))
            img = np.expand_dims(img, axis=0)
            input_name = onnx_session.get_inputs()[0].name
            outputs = onnx_session.run(None, {input_name: img})[0]

            detections = []
            for det in outputs[0]:
                x1, y1, x2, y2, conf, cls_id = det
                if conf < 0.3:
                    continue
                detections.append({'char': chr(int(cls_id) + 97), 'conf': float(conf), 'cx': float((x1 + x2) / 2)})

            if not detections:
                print(ui.warning('  ⚠ ONNX solver detected no characters.'))
                return None

            detections.sort(key=lambda d: d['cx'])
            captcha = ''.join(d['char'] for d in detections[:self.captcha_image_letter_count])
            print(ui.success(f'  ✅ ONNX solved captcha text: {captcha}'))
            return captcha
        except Exception as e:
            print(ui.error(f'  ⚠ ONNX image captcha solve failed: {e}'))
            return None

    def _ocr_space(self, image_url: str) -> Optional[str]:
        if not self.ocr_space_key:
            print(ui.warning('  ⚠ OCR.space key missing, cannot solve image captcha automatically.'))
            return None

        print(ui.warning(f'  🤖 OCR.space solving image captcha: {image_url}'))
        payload = {
            'apikey': self.ocr_space_key,
            'url': image_url,
            'language': 'eng',
            'isOverlayRequired': 'false',
            'OCREngine': '2',
        }

        try:
            r = requests.post('https://api.ocr.space/parse/image', data=payload, timeout=30)
            data = r.json()
            if data.get('IsErroredOnProcessing'):
                print(ui.error(f"  OCR.space error: {data.get('ErrorMessage')}") )
                return None

            parsed = data.get('ParsedResults', [])
            if not parsed:
                print(ui.error('  OCR.space returned no parsed results.'))
                return None

            text = parsed[0].get('ParsedText', '')
            if not text:
                print(ui.error('  OCR.space returned empty text.'))
                return None

            text = re.sub(r'[^A-Za-z0-9]', '', text).strip()
            if not text:
                print(ui.error('  OCR.space text cleaned to empty string.'))
                return None

            print(ui.success(f'  ✅ OCR solved captcha text: {text}'))
            return text
        except Exception as e:
            print(ui.error(f'  OCR.space request failed: {e}'))
            return None
    
    def _capmonster(self, sitekey: str, rqdata: str, url: str) -> Optional[str]:
        print(ui.warning("  🤖 CapMonster solving..."))
        task = {
            "clientKey": self.capmonster_key,
            "task": {
                "type": "HCaptchaTaskProxyless",
                "websiteURL": url,
                "websiteKey": sitekey
            }
        }
        if rqdata:
            task["task"]["data"] = rqdata
        
        try:
            r = requests.post("https://api.capmonster.cloud/createTask", json=task, timeout=30)
            res = r.json()
            if res.get("errorId") != 0:
                print(ui.error(f"  CapMonster error: {res.get('errorDescription')}"))
                return None
            
            tid = res["taskId"]
            for _ in range(60):
                time.sleep(3)
                r = requests.post("https://api.capmonster.cloud/getTaskResult", json={
                    "clientKey": self.capmonster_key, "taskId": tid
                }, timeout=10)
                res = r.json()
                if res.get("status") == "ready":
                    token = res["solution"]["gRecaptchaResponse"]
                    print(ui.success("  ✅ CapMonster solved!"))
                    return token
            
            print(ui.warning("  ⏱ CapMonster timeout"))
            return None
        except Exception as e:
            print(ui.error(f"  CapMonster error: {e}"))
            return None
    
    def _twocaptcha(self, sitekey: str, rqdata: str, url: str) -> Optional[str]:
        print(ui.warning("  🤖 2Captcha solving..."))
        try:
            payload = {
                "key": self.twocaptcha_key, "method": "hcaptcha",
                "sitekey": sitekey, "pageurl": url, "json": 1
            }
            if rqdata:
                payload["data"] = rqdata
            
            r = requests.post("https://2captcha.com/in.php", data=payload, timeout=30)
            res = r.json()
            if res.get("status") != 1:
                print(ui.error(f"  2Captcha error: {res}"))
                return None
            
            cid = res["request"]
            for _ in range(60):
                time.sleep(5)
                r = requests.get(
                    f"https://2captcha.com/res.php?key={self.twocaptcha_key}&action=get&id={cid}&json=1",
                    timeout=10
                )
                res = r.json()
                if res.get("status") == 1:
                    print(ui.success("  ✅ 2Captcha solved!"))
                    return res["request"]
            print(ui.warning("  ⏱ 2Captcha timeout"))
            return None
        except Exception as e:
            print(ui.error(f"  2Captcha error: {e}"))
            return None
    
    def _manual(self, sitekey: str, url: str) -> Optional[str]:
        """Manual solving with auto-browser open."""
        print()
        print(ui.warning("  ╔═══════════════════════════════════════════╗"))
        print(ui.warning("  ║     HUMAN VERIFICATION REQUIRED         ║"))
        print(ui.warning("  ╚═══════════════════════════════════════════╝"))
        print()
        print(ui.dim(f"  Sitekey: {sitekey}"))
        
        # Auto-open browser
        if CONFIG["AUTO_BROWSER"]:
            print(ui.info("  🌐 Attempting to open Discord..."))
            open_browser(url)
        else:
            print(ui.warning(f"  Open manually: {url}"))
        
        print()
        print(ui.dim("  Solve the hCaptcha in your browser, then paste the token below."))
        print(ui.dim("  (Press Enter without token to skip this captcha)"))
        print()
        
        token = input(ui.primary("  Token > ")).strip()
        if token:
            print(ui.success("  ✅ Manual token captured!"))
            return token
        return None


# ============================================================
# SECTION 7: VERIFICATION CHECKER
# ============================================================

class VerificationMonitor:
    """Monitors for human verification requests from OWO bot."""
    
    VERIFY_KEYWORDS = ["human", "verify", "captcha", "verification", "are you human",
                       "complete this", "prove you're", "bot check"]
    OAH_CAPTCHA_KEYWORDS = ["enter the text", "captcha image", "image captcha", "random text", "type the text"]
    
    def __init__(self, api: DiscordAPI, channels: List[str], sound: bool = True):
        self.api = api
        self.channels = channels
        self.sound = sound
        self.alerted_channels = set()
        self.captcha_handler = CaptchaHandler()
        self.oah_captcha_keywords = CONFIG['OAH_CAPTCHA_KEYWORDS']

    def handle_flagged_message(self, channel_id: str, msg: dict, dry_run: bool = False) -> bool:
        """Log the full message payload, ping alert user if configured, and exit.

        If dry_run is True, do not exit and just perform logging and ping attempt.
        Returns True if handled.
        """
        ping_id = CONFIG.get('ALERT_PING_USER_ID', '')
        log_path = CONFIG.get('ALERT_LOG_FILE', 'flagged_messages.log')
        raw_content = msg.get('content', '')

        # Full payload logging (append and also write a timestamped copy)
        try:
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'channel_id': channel_id,
                'message_id': msg.get('id'),
                'author': msg.get('author', {}),
                'content': raw_content,
                'attachments': msg.get('attachments', []),
                'full_payload': msg,
            }
            # append to main log
            with open(log_path, 'a', encoding='utf-8') as lf:
                lf.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

            # write timestamped copy
            ts = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            ts_path = f"{log_path}.{ts}.json"
            with open(ts_path, 'w', encoding='utf-8') as tf:
                tf.write(json.dumps(log_entry, ensure_ascii=False, indent=2))

            print(ui.info(f"  Logged flagged message to {log_path} and {ts_path}"))
        except Exception as e:
            print(ui.warning(f"  Failed to log flagged message: {e}"))

        # Ping the configured user if available
        if ping_id and str(ping_id).isdigit():
            try:
                self.api.send_message(channel_id, f"<@{ping_id}> You were flagged for verification in this channel. Stopping bot immediately.")
            except Exception:
                pass

        if dry_run:
            return True

        # Exit immediately
        print(ui.error("  ⛔ Flagged message detected; stopping immediately."))
        os._exit(0)
    
    def check(self, channel_id: str = None) -> bool:
        """Check if verification is requested. Returns True if verification was detected and handled."""
        channels_to_check = [channel_id] if channel_id else random.sample(self.channels, min(2, len(self.channels)))
        
        for ch in channels_to_check:
            if ch in self.alerted_channels:
                continue
            
            msgs = self.api.fetch_messages(ch, limit=3)
            for msg in msgs:
                content = msg.get("content", "").lower()
                author = msg.get("author", {}).get("username", "").lower()
                
                # Is it from OWO bot?
                is_owo = "owo" in author or "owo" in content
                if not is_owo:
                    continue
                
                # Is it asking for verification?
                # OAH may send randomized image text captchas; detect both keyword
                # prompts and image attachments so the solver can handle them.
                oah_image_flag = any(kw in content for kw in self.oah_captcha_keywords)
                attachments = msg.get("attachments", []) or []
                has_image_attachment = any(att.get("content_type", "").startswith("image") or att.get("url", "").lower().endswith((".png", ".jpg", ".jpeg", ".gif")) for att in attachments)
                if any(kw in content for kw in self.VERIFY_KEYWORDS) or oah_image_flag or has_image_attachment:
                    self.alerted_channels.add(ch)
                    print()
                    print(ui.error("  ╔═══════════════════════════════════════════╗"))
                    print(ui.error("  ║   🔔 HUMAN VERIFICATION DETECTED!        ║"))
                    print(ui.error("  ╚═══════════════════════════════════════════╝"))
                    
                    # Sound alert
                    if self.sound:
                        try:
                            import winsound
                            for _ in range(5):
                                winsound.Beep(1200, 200)
                                time.sleep(0.15)
                            winsound.Beep(800, 500)
                        except:
                            print("\a" * 5)
                    
                    # Auto-open browser
                    captcha_url = "https://discord.com/channels/@me"
                    if CONFIG["AUTO_BROWSER"]:
                        open_browser(captcha_url)
                    else:
                        print(ui.warning(f"  🌐 Open: {captcha_url}"))

                    # Immediate stop + ping if message contains warning emoji and an "are you" prompt
                    ping_id = CONFIG.get('ALERT_PING_USER_ID', '')
                    raw_content = msg.get('content', '')
                    if (('⚠' in raw_content or '⚠️' in raw_content) and 'are you' in content):
                        if ping_id and str(ping_id).isdigit():
                            try:
                                self.api.send_message(ch, f"<@{ping_id}> You were flagged for verification in this channel. Stopping bot immediately.")
                            except Exception:
                                pass
                        print(ui.error("  ⛔ Flagged message detected; stopping immediately and pinging alert user."))
                        os._exit(0)

                    parsed_msg = components_v2.message.get_message_obj(msg)
                    verify_buttons = [
                        btn
                        for btn in parsed_msg.buttons
                        if btn and getattr(btn, 'label', None) and 'verify' in btn.label.lower()
                    ]
                    if verify_buttons:
                        print(ui.secondary("  Attempting to click verify button via components_v2 handler..."))
                        for button in verify_buttons:
                            if self.api.click_component(button):
                                print(ui.success("  ✅ Verify button clicked automatically."))
                                self.alerted_channels.discard(ch)
                                return True
                        print(ui.warning("  ⚠ Failed to click verify button automatically."))

                    # If flagged with warning emoji + 'are you', handle via handler
                    raw_content = msg.get('content', '')
                    if (('⚠' in raw_content or '⚠️' in raw_content) and 'are you' in content):
                        return self.handle_flagged_message(ch, msg)

                    if oah_image_flag or has_image_attachment:
                        for att in attachments:
                            img_url = att.get("url") or att.get("proxy_url")
                            if not img_url:
                                continue
                            solution = self.captcha_handler.solve_image(img_url)
                            if solution:
                                print(ui.success(f"  ✅ Solved OAH image captcha: {solution}"))
                                sent = self.api.send_message(ch, solution)
                                if sent:
                                    print(ui.success("  ✅ Sent captcha answer automatically."))
                                else:
                                    print(ui.warning("  ⚠ Failed to send captcha answer."))
                                self.alerted_channels.discard(ch)
                                return True
                        print(ui.dim("  This looks like an OAH image text captcha. Open the link, read the text, and paste it below."))
                    else:
                        print(ui.dim("  Complete the captcha in your browser then press Enter."))
                    
                    print(ui.dim("  If the captcha is shown as an image, copy the text exactly."))
                    input(ui.primary("  Press Enter after verifying... "))
                    
                    print(ui.success("  ✅ Verification acknowledged. Resuming operations."))
                    self.alerted_channels.discard(ch)
                    return True
        
        return False


# ============================================================
# SECTION 8: STATISTICS TRACKER
# ============================================================

class StatsTracker:
    """Tracks and displays bot statistics."""
    
    def __init__(self, username: str):
        self.username = username
        self.total_commands = 0
        self.total_cycles = 0
        self.start_time = time.time()
        self.commands_timeline = deque(maxlen=100)
        self.lootboxes_opened = 0
        self.crates_opened = 0
        self.gems_equipped = 0
        self.sellalls_performed = 0
        self.errors = 0
        self.ratelimits = 0
        self.verifications_handled = 0
        
    def record_command(self):
        self.total_commands += 1
        self.total_cycles += 1
        self.commands_timeline.append(time.time())
    
    def commands_last_hour(self) -> int:
        cutoff = time.time() - 3600
        return sum(1 for t in self.commands_timeline if t >= cutoff)
    
    def uptime(self) -> str:
        delta = timedelta(seconds=int(time.time() - self.start_time))
        return str(delta).split('.')[0]
    
    def commands_per_minute(self) -> float:
        elapsed = max(time.time() - self.start_time, 1)
        return self.total_commands / (elapsed / 60)
    
    def display(self) -> str:
        return (
            f"{ui.dim('─── ')}{ui.primary('STATS')}{ui.dim(' ───')}\n"
            f"  {ui.dim('User:')}      {ui.bold(self.username)}\n"
            f"  {ui.dim('Uptime:')}    {ui.success(self.uptime())}\n"
            f"  {ui.dim('Commands:')}  {ui.primary(str(self.total_commands))} "
            f"({ui.dim(str(self.commands_last_hour())+'/hr')}) "
            f"[{ui.dim(f'{self.commands_per_minute():.1f}/min')}]\n"
            f"  {ui.dim('Sellalls:')}  {ui.warning(str(self.sellalls_performed))}\n"
            f"  {ui.dim('Lootboxes:')} {ui.secondary(str(self.lootboxes_opened))}\n"
            f"  {ui.dim('Crates:')}    {ui.secondary(str(self.crates_opened))}\n"
            f"  {ui.dim('Gems:')}      {ui.secondary(str(self.gems_equipped))}\n"
            f"  {ui.dim('Errors:')}    {ui.error(str(self.errors)) if self.errors else ui.success('0')}\n"
            f"  {ui.dim('Verify:')}    {ui.warning(str(self.verifications_handled))}"
        )


# ============================================================
# SECTION 9: MAIN SELFBOT ENGINE
# ============================================================

class CombiusEngine:
    """
    The core Combius selfbot engine.
    Each token gets its own engine instance running in a thread.
    """
    
    def __init__(self, token: str, channels: List[str], instance_id: int = 0):
        self.token = token
        self.channels = channels
        self.instance_id = instance_id
        self.running = False
        self.paused = False
        
        # Core components
        self.api = DiscordAPI(token)
        self.username = self.api.get_username()
        self.user_id = self.api.get_user_id()
        self.stats = StatsTracker(self.username)
        self.verify_monitor = VerificationMonitor(self.api, channels, CONFIG["VERIFY_SOUND"])
        
        # State
        self.commands_since_sellall = 0
        self.cycle = 0
        self.last_inventory_scan = -10
        self.last_claim_time = 0
        self.gems_equipped_this_session = False
        self.last_gem_equip_cycle = 0
        self.consecutive_same_channel = 0
        self.last_channel_used = None
        self.discovered_gems = []
        self.inventory_cache = None
        self.last_command = ""

        # Special command memory
        self.oah_last_run = 0
        self.oah_complete_at = 0
        self.oah_rest_until = 0
        self.oah_claimed = True
        self.last_piku_run_date = None
        self.last_run_run_date = None
        self.commands_since_oah = 0
        
        # Human-like behavior state
        self.typing_speed = random.uniform(0.05, 0.15)
        self.activity_pattern = self._generate_activity_pattern()
        self.break_until = 0
        
        # Resolve gem IDs (per-token override)
        self.gem_ids = self._resolve_gem_ids()
    
    def _resolve_gem_ids(self) -> List[int]:
        """Check for per-token gem overrides."""
        for prefix, ids in TOKEN_GEMS_OVERRIDES.items():
            if self.token.startswith(prefix):
                print(ui.success(f"  [{self.username}] Custom gems from override: {ids}"))
                return ids
        return CONFIG["GEM_IDS"]
    
    def _generate_activity_pattern(self) -> List[float]:
        """
        Generate a human-like activity pattern with natural pauses.
        Returns multipliers for delay timing.
        """
        pattern = []
        for _ in range(50):
            base = 1.0
            # Natural variation
            base += random.gauss(0, 0.2)
            # Occasional longer pauses (like checking phone, reading)
            if random.random() < 0.1:
                base += random.uniform(0.5, 2.0)
            pattern.append(max(0.5, min(3.0, base)))
        return pattern
    
    def _human_delay(self) -> float:
        """Calculate a human-like delay with jitter, spikes, and pattern."""
        base = random.uniform(CONFIG["MIN_DELAY"], CONFIG["MAX_DELAY"])
        
        # Apply activity pattern
        pattern_idx = self.cycle % len(self.activity_pattern)
        base *= self.activity_pattern[pattern_idx]
        
        # Add jitter
        jitter = CONFIG["DELAY_JITTER"]
        base *= random.uniform(1 - jitter, 1 + jitter)
        
        # Occasional spike (long pause like human walking away)
        if random.random() < CONFIG["DELAY_SPIKE_CHANCE"]:
            spike = random.uniform(CONFIG["MAX_DELAY"], CONFIG["DELAY_SPIKE_MAX"])
            print(ui.dim(f"  [{self.username}] ⏸ Natural pause: {spike:.0f}s..."))
            base += spike
        
        return max(5, min(300, base))
    
    def _pick_channel(self) -> str:
        """Pick a channel with anti-pattern protection."""
        # Avoid using same channel repeatedly
        if self.consecutive_same_channel >= CONFIG["MAX_CONSECUTIVE_SAME_CHANNEL"]:
            others = [c for c in self.channels if c != self.last_channel_used]
            if others:
                ch = random.choice(others)
            else:
                ch = random.choice(self.channels)
            self.consecutive_same_channel = 0
        else:
            ch = random.choice(self.channels)
        
        # Rotate channels naturally
        if self.last_channel_used and CONFIG["ANTI_PATTERN_ROTATION"]:
            # 30% chance to switch channel even if not forced
            if random.random() < 0.3:
                others = [c for c in self.channels if c != self.last_channel_used]
                if others:
                    ch = random.choice(others)
                    self.consecutive_same_channel = 0
        
        if ch == self.last_channel_used:
            self.consecutive_same_channel += 1
        else:
            self.consecutive_same_channel = 1
        
        self.last_channel_used = ch
        return ch
    
    def _get_owo_command(self) -> str:
        """Generate a human-like OWO command with variety."""
        # Weighted random selection
        pool_choice = random.choices(
            list(CMD_POOL.keys()),
            weights=[0.6, 0.2, 0.1, 0.1],
            k=1
        )[0]
        
        cmd = random.choice(CMD_POOL[pool_choice])
        
        # Occasionally add variation
        if random.random() < 0.15:
            cmd += f" {random.choice(['pls', 'now', 'go', '!', '.'])}"
        
        return cmd

    def _gmt7_now(self) -> datetime:
        return datetime.utcnow() + timedelta(hours=7)

    def _parse_daily_time(self, time_str: str) -> Optional[dt_time]:
        try:
            hh, mm = [int(x) for x in time_str.split(':')]
            return dt_time(hh, mm)
        except Exception:
            return None

    def _daily_task_due(self, last_run_date: Optional[datetime.date], target_time: str) -> bool:
        now = self._gmt7_now()
        target = self._parse_daily_time(target_time)
        if not target:
            return False
        if now.time() < target:
            return False
        return last_run_date != now.date()

    def _record_daily_run(self, cmd: str):
        date_today = self._gmt7_now().date()
        if cmd == 'owo piku':
            self.last_piku_run_date = date_today
        elif cmd == 'owo run':
            self.last_run_run_date = date_today

    def _command_delay(self, cmd: str) -> float:
        """Return the delay after a command, applying optional custom settings for owo b."""
        if cmd.startswith('owo b') or cmd == 'owo b':
            min_delay = CONFIG['OWO_B_MIN_DELAY'] or CONFIG['MIN_DELAY']
            max_delay = CONFIG['OWO_B_MAX_DELAY'] or CONFIG['MAX_DELAY']
            jitter = CONFIG['OWO_B_DELAY_JITTER'] if CONFIG['OWO_B_DELAY_JITTER'] >= 0 else CONFIG['DELAY_JITTER']
            base = random.uniform(min_delay, max_delay)
            base *= random.uniform(1 - jitter, 1 + jitter)
            return max(5, min(300, base))
        return self._human_delay()

    def _scheduled_command(self) -> Optional[str]:
        """Return a scheduled command if a special command is due."""
        now = time.time()

        # If OAH completed and claim is still pending, claim immediately
        if self.oah_complete_at and now >= self.oah_complete_at and not self.oah_claimed:
            self.oah_claimed = True
            self.oah_rest_until = now + CONFIG['OAH_REST_MINUTES'] * 60
            self.oah_complete_at = 0
            print(ui.secondary(f"  [{self.username}] ⏱ OAH complete — claiming now and resting {CONFIG['OAH_REST_MINUTES']}m"))
            return 'owo claim'

        # Keep OAH resting for the configured cooldown
        if self.oah_rest_until and now < self.oah_rest_until:
            return None

        # Run OAH when ready if enabled and not already active
        if CONFIG['OAH_ENABLED'] and not self.oah_complete_at and self.oah_claimed:
            self.oah_last_run = now
            self.oah_complete_at = now + CONFIG['OAH_DURATION_SECONDS']
            self.oah_claimed = False
            expected = datetime.fromtimestamp(self.oah_complete_at).strftime('%H:%M:%S')
            print(ui.secondary(f"  [{self.username}] 🤖 Running {CONFIG['OAH_COMMAND']} — will complete at {expected}"))
            return CONFIG['OAH_COMMAND']

        # Daily scheduled commands in GMT+7
        if CONFIG['OWO_PIKU_ENABLED'] and self._daily_task_due(self.last_piku_run_date, CONFIG['OWO_PIKU_DAILY_TIME']):
            self._record_daily_run('owo piku')
            print(ui.secondary(f"  [{self.username}] 📅 Scheduled owo piku for GMT+7 {CONFIG['OWO_PIKU_DAILY_TIME']}"))
            return 'owo piku'

        if CONFIG['OWO_RUN_ENABLED'] and self._daily_task_due(self.last_run_run_date, CONFIG['OWO_RUN_DAILY_TIME']):
            self._record_daily_run('owo run')
            print(ui.secondary(f"  [{self.username}] 📅 Scheduled owo run for GMT+7 {CONFIG['OWO_RUN_DAILY_TIME']}"))
            return 'owo run'

        return None
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within rate limits. Returns True if should proceed."""
        hourly = self.stats.commands_last_hour()
        max_cmd = CONFIG["MAX_COMMANDS_PER_HOUR"]
        if hourly >= max_cmd:
            wait = 3600 - (time.time() - max(self.stats.commands_timeline[-1] if self.stats.commands_timeline else 0, 0))
            wait = max(60, min(3600, wait))
            print(ui.warning(f"  [{self.username}] ⏱ Hourly limit ({max_cmd}/hr) reached. Pausing {wait:.0f}s..."))
            time.sleep(wait)
            return True
        return True
    
    def _scan_inventory(self) -> dict:
        """Send owo inv and parse the response."""
        channel = self._pick_channel()
        print(ui.dim(f"  [{self.username}] 🔍 Inventory scan..."))
        
        self.api.send_message(channel, "owo inv")
        time.sleep(random.uniform(3.0, 4.5))
        
        msgs = self.api.fetch_messages(channel, limit=10)
        inv = InventoryParser.parse(msgs, self.user_id)
        
        if inv["success"]:
            self.inventory_cache = inv
            if inv["gem_ids"]:
                self.discovered_gems = inv["gem_ids"]
                gems_detail = ", ".join(f"{gid}({inv['gem_quantities'].get(gid,'?')})" for gid in inv["gem_ids"])
                print(ui.success(f"  [{self.username}] 💎 Found gems: {gems_detail}"))
            if inv["lootbox_count"] > 0:
                print(ui.secondary(f"  [{self.username}] 📦 Lootboxes: {inv['lootbox_count']}"))
            if inv["fabled_lootbox_count"] > 0:
                print(ui.secondary(f"  [{self.username}] ⭐ Fabled: {inv['fabled_lootbox_count']}"))
            if inv["crate_count"] > 0:
                print(ui.secondary(f"  [{self.username}] 📦 Crates: {inv['crate_count']}"))
        else:
            print(ui.warning(f"  [{self.username}] ⚠ Could not parse inventory"))
        
        return inv
    
    def _handle_inventory(self):
        """Full inventory management: scan, open lootboxes/crates, equip gems."""
        inv = self._scan_inventory()
        if not inv["success"]:
            return
        
        # Open lootboxes
        if CONFIG["AUTO_OPEN_LOOTBOXES"] and inv["lootbox_count"] > 0:
            count = min(inv["lootbox_count"], 100)
            self.api.send_message(self.last_channel_used or self._pick_channel(), f"owo lb {count}")
            self.stats.lootboxes_opened += count
            print(ui.success(f"  [{self.username}] 📦 Opened {count} lootboxes"))
            time.sleep(random.uniform(2, 4))
        
        # Open fabled lootboxes
        if CONFIG["AUTO_OPEN_FABLED"] and inv["fabled_lootbox_count"] > 0:
            for _ in range(min(inv["fabled_lootbox_count"], 3)):
                self.api.send_message(self.last_channel_used or self._pick_channel(), "owo use 49")
                self.stats.lootboxes_opened += 1
                print(ui.success(f"  [{self.username}] ⭐ Opened fabled lootbox"))
                time.sleep(random.uniform(2, 3))
        
        # Open weapon crates
        if CONFIG["AUTO_OPEN_CRATES"] and inv["crate_count"] > 0:
            count = min(inv["crate_count"], 50)
            self.api.send_message(self.last_channel_used or self._pick_channel(), f"owo wc {count}")
            self.stats.crates_opened += count
            print(ui.success(f"  [{self.username}] 📦 Opened {count} weapon crates"))
            time.sleep(random.uniform(2, 4))
        
        # Re-scan after opening to get new gems
        if inv["lootbox_count"] > 0 or inv["fabled_lootbox_count"] > 0:
            time.sleep(random.uniform(3, 5))
            inv2 = self._scan_inventory()
            if inv2["success"] and inv2["gem_ids"]:
                self.discovered_gems = inv2["gem_ids"]
                self.inventory_cache = inv2
    
    def _equip_gems(self):
        """Equip best available gems using discovered or configured IDs."""
        channel = self._pick_channel()
        
        gems_to_equip = []
        
        if CONFIG["AUTO_SCAN_GEMS"] and self.discovered_gems:
            # Use best gems from inventory scan
            gems_to_equip = InventoryParser.get_best_gems(
                {"gem_ids": self.discovered_gems}, 
                CONFIG["MIN_GEM_TIER"]
            )
        
        if not gems_to_equip and self.inventory_cache and self.inventory_cache["success"]:
            gems_to_equip = InventoryParser.get_best_gems(
                self.inventory_cache, CONFIG["MIN_GEM_TIER"]
            )
        
        if not gems_to_equip:
            # Fallback to configured
            gems_to_equip = self.gem_ids[:4]
        
        if not gems_to_equip:
            return
        
        # Max 4 gems at a time
        gems_to_equip = gems_to_equip[:4]
        
        ids_str = " ".join(str(g) for g in gems_to_equip)
        cmd = f"owo use {ids_str}"
        self.api.send_message(channel, cmd)
        self.gems_equipped_this_session = True
        self.last_gem_equip_cycle = self.cycle
        self.stats.gems_equipped += len(gems_to_equip)
        
        gem_names = ", ".join(GEM_NAMES.get(g, f"ID:{g}") for g in gems_to_equip)
        print(ui.success(f"  [{self.username}] 💎 Equipped: {gem_names}"))
    
    def _do_sellall(self):
        """Execute sellall with cooldown and safety checks."""
        channel = self._pick_channel()
        self.commands_since_sellall = 0
        self.stats.sellalls_performed += 1
        
        print(ui.warning(f"  [{self.username}] ⚡ SELLALL (#{self.stats.sellalls_performed})"))
        self.api.send_message(channel, "owo sellall")
        
        # Cooldown with variance
        cd = CONFIG["SELLALL_COOLDOWN"] + random.randint(-30, 60)
        cd = max(120, cd)
        
        print(ui.dim(f"  [{self.username}] 😴 Sellall cooldown: {cd//60}m{cd%60}s"))
        
        # Break cooldown into chunks for safety checks
        end = time.time() + cd
        while time.time() < end and self.running:
            # Check for verification during cooldown
            self.verify_monitor.check()
            time.sleep(min(15, end - time.time())) if end - time.time() > 0 else None
        
        print(ui.success(f"  [{self.username}] ✅ Sellall cooldown complete"))
        
        # Scan inventory after sellall
        time.sleep(random.uniform(2, 5))
        if CONFIG["INVENTORY_CHECK_INTERVAL"] > 0:
            self._handle_inventory()
    
    def _do_claim(self):
        """Claim daily rewards."""
        channel = self._pick_channel()
        print(ui.secondary(f"  [{self.username}] 🎁 Claiming daily..."))
        
        self.api.send_message(channel, "owo claim")
        time.sleep(random.uniform(2, 4))
        self.api.send_message(channel, "owo daily")
        
        self.last_claim_time = time.time()
        print(ui.success(f"  [{self.username}] 🎁 Daily claimed"))
    
    def _check_breaks(self):
        """Check if we should take a scheduled break."""
        if CONFIG["BREAK_INTERVAL_MINUTES"] <= 0 or CONFIG["MIN_BREAK_MINUTES"] <= 0:
            return
        
        elapsed_minutes = (time.time() - self.stats.start_time) / 60
        if int(elapsed_minutes) % CONFIG["BREAK_INTERVAL_MINUTES"] == 0 and elapsed_minutes > 10:
            if time.time() > self.break_until:
                break_duration = random.randint(
                    CONFIG["MIN_BREAK_MINUTES"] * 60,
                    CONFIG["MIN_BREAK_MINUTES"] * 60 * 2
                )
                print(ui.warning(f"  [{self.username}] ☕ Scheduled break: {break_duration//60}min"))
                self.break_until = time.time() + break_duration
                
                while time.time() < self.break_until and self.running:
                    self.verify_monitor.check()
                    time.sleep(30)
                
                print(ui.success(f"  [{self.username}] ☕ Break over, resuming"))
    
    def _display_stats_if_needed(self):
        """Periodically display stats."""
        if CONFIG["SHOW_STATS"] and self.cycle > 0 and self.cycle % CONFIG["STATS_INTERVAL"] == 0:
            print()
            print(ui.header(f"  📊 {self.username} — Cycle #{self.cycle}"))
            print(self.stats.display())
            print()
    
    # ====== MAIN LOOP ======
    def run(self):
        """Main bot loop."""
        self.running = True
        
        print(ui.success(f"  [{self.username}] ✅ Engine started"))
        print(ui.dim(f"  [{self.username}] Channels: {len(self.channels)} | Gems: {self.gem_ids}"))
        
        # Initial claim after startup
        if CONFIG["AUTO_CLAIM"]:
            time.sleep(random.uniform(5, 15))
            self._do_claim()
        
        while self.running:
            try:
                # ---- Pause check ----
                if self.paused:
                    time.sleep(5)
                    continue
                
                # ---- Scheduled breaks ----
                self._check_breaks()
                
                # ---- Rate limit check ----
                if not self._check_rate_limit():
                    continue
                
                # ---- Periodic inventory scan (every N cycles) ----
                if (CONFIG["INVENTORY_CHECK_INTERVAL"] > 0 and 
                    self.cycle > 0 and 
                    self.cycle % CONFIG["INVENTORY_CHECK_INTERVAL"] == 0):
                    self._handle_inventory()
                
                # ---- Auto-claim (every ~8 hours) ----
                if CONFIG["AUTO_CLAIM"] and self.last_claim_time > 0:
                    claim_interval = CONFIG["CLAIM_INTERVAL_HOURS"] * 3600
                    if time.time() - self.last_claim_time > claim_interval:
                        self._do_claim()
                
                # ---- Equip gems (initial + re-equip every 25 cycles) ----
                if CONFIG["GEM_ENABLED"]:
                    if not self.gems_equipped_this_session:
                        if self.cycle >= 3:  # Wait a few cycles for inventory data
                            self._equip_gems()
                    elif (self.cycle - self.last_gem_equip_cycle) > 25:
                        self.gems_equipped_this_session = False
                
                # ---- Main command or scheduled task ----
                channel = self._pick_channel()
                cmd = self._scheduled_command() or self._get_owo_command()
                
                self.commands_since_sellall += 1
                self.cycle += 1
                
                # Send command
                success = self.api.send_message(channel, cmd)
                if success:
                    self.stats.record_command()
                    print(ui.tag(self.username, 
                        f"{ui.dim(local_time())} #{self.commands_since_sellall} "
                        f"{ui.primary(cmd)} "
                        f"{ui.dim(f'[{channel[:5]}..]')}"))
                else:
                    self.stats.errors += 1
                
                # ---- Verification check ----
                self.verify_monitor.check(channel)
                
                # ---- Sellall check (with variance) ----
                sellall_target = CONFIG["SELLALL_INTERVAL"] + random.randint(
                    -CONFIG["SELLALL_VARIANCE"], CONFIG["SELLALL_VARIANCE"]
                )
                if self.commands_since_sellall >= sellall_target:
                    self._do_sellall()
                    continue
                
                # ---- Display stats ----
                self._display_stats_if_needed()
                
                # ---- Human-like delay ----
                delay = self._human_delay()
                elapsed = 0
                while elapsed < delay and self.running:
                    time.sleep(1)
                    elapsed += 1
                    
                    # Safety checks during delay
                    if int(elapsed) % VERIFY_CHECK_INTERVAL == 0 and elapsed > 0:
                        self.verify_monitor.check()
                    
                    # Check for pause signal
                    if self.paused:
                        break
                
            except KeyboardInterrupt:
                print(ui.warning(f"\n  [{self.username}] ⛔ Received stop signal"))
                self.running = False
                break
            except Exception as e:
                self.stats.errors += 1
                print(ui.error(f"  [{self.username}] ⚠ Error: {e}"))
                time.sleep(15)
    
    def stop(self):
        """Graceful stop."""
        self.running = False
        print(ui.dim(f"  [{self.username}] 🛑 Engine stopping..."))


# ============================================================
# SECTION 10: BANNER & MAIN
# ============================================================

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║     ██████  ██████  ███    ███ ██████  ██    ██ ██    ██     ║
║    ██      ██    ██ ████  ████ ██   ██ ██    ██ ██    ██     ║
║    ██      ██    ██ ██ ████ ██ ██████  ██    ██ ██    ██     ║
║    ██      ██    ██ ██  ██  ██ ██   ██ ██    ██ ██    ██     ║
║     ██████  ██████  ██      ██ ██████   ██████   ██████      ║
║                                                              ║
║     The Ultimate OWO Selfbot Engine                          ║
║     Safe • Smart • Fancy • Multi-Token                       ║
║                                                              ║
║     "Safety is not optional — it is the foundation."         ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""


def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully."""
    print()
    print(ui.warning("\n  ⛔ Received interrupt signal. Shutting down all engines..."))
    for bot in running_bots:
        bot.stop()
    print(ui.success("\n  ✅ All engines stopped. Goodbye.\n"))
    sys.exit(0)


running_bots = []


def main():
    """Main entry point."""
    print(BANNER)
    
    # System info
    system = platform.system()
    print(ui.dim(f"  System: {system} {platform.release()}"))
    print(ui.dim(f"  Python: {sys.version.split()[0]}"))
    print(ui.dim(f"  Platform: {platform.platform()}"))
    
    # Check Termux
    if os.path.exists("/data/data/com.termux"):
        print(ui.success("  ✅ Termux detected — URL opening configured"))
    
    # Check Railway
    if os.environ.get('RAILWAY_PROJECT_ID'):
        print(ui.success("  ✅ Railway environment detected"))
    
    print()
    
    # Configuration summary
    print(ui.header("  CONFIGURATION"))
    print(f"  {ui.dim('Tokens:')}     {ui.bold(str(len(CONFIG['DISCORD_TOKENS'])))}")
    print(f"  {ui.dim('Channels:')}   {ui.bold(str(len(CONFIG['CHANNEL_IDS'])))}")
    delay_text = f"{CONFIG['MIN_DELAY']}s - {CONFIG['MAX_DELAY']}s"
    print(f"  {ui.dim('Delay:')}      {ui.primary(delay_text)}")
    if CONFIG["DELAY_SPIKE_CHANCE"] > 0:
        spikes_text = f"up to {CONFIG['DELAY_SPIKE_MAX']}s ({CONFIG['DELAY_SPIKE_CHANCE']*100:.0f}% chance)"
        print(f"  {ui.dim('Spikes:')}     {ui.dim(spikes_text)}")
    sellall_text = f"every {CONFIG['SELLALL_INTERVAL']}±{CONFIG['SELLALL_VARIANCE']} / {CONFIG['SELLALL_COOLDOWN']}s cd"
    print(f"  {ui.dim('Sellall:')}    {ui.warning(sellall_text)}")
    gem_status = 'ON' if CONFIG['GEM_ENABLED'] else 'OFF'
    gem_details = f"(scan: {CONFIG['AUTO_SCAN_GEMS']}, IDs: {CONFIG['GEM_IDS']})" if CONFIG['GEM_ENABLED'] else ''
    print(f"  {ui.dim('Gems:')}       {ui.secondary(gem_status)} {gem_details}")
    loot_status = 'ON' if CONFIG['AUTO_OPEN_LOOTBOXES'] else 'OFF'
    crate_status = 'ON' if CONFIG['AUTO_OPEN_CRATES'] else 'OFF'
    print(f"  {ui.dim('Lootboxes:')}  {ui.secondary(loot_status)} | {ui.dim('Crates:')} {ui.secondary(crate_status)}")
    print(f"  {ui.dim('Inventory:')}  {ui.primary('every ' + str(CONFIG['INVENTORY_CHECK_INTERVAL']) + ' cycles')}")
    browser_status = 'ON' if CONFIG['AUTO_BROWSER'] else 'OFF'
    sound_status = 'ON' if CONFIG['VERIFY_SOUND'] else 'OFF'
    print(f"  {ui.dim('Browser:')}    {ui.primary(browser_status)} | {ui.dim('Sound:')} {ui.primary(sound_status)}")
    print(f"  {ui.dim('Captcha:')}    {ui.warning(CONFIG['CAPTCHA_SERVICE'])}")
    limit_status = str(CONFIG['MAX_COMMANDS_PER_HOUR']) + '/hr'
    anti_pattern_status = 'ON' if CONFIG['ANTI_PATTERN_ROTATION'] else 'OFF'
    print(f"  {ui.dim('Limit:')}      {ui.warning(limit_status)} | {ui.dim('Anti-Pattern:')} {ui.success(anti_pattern_status)}")
    
    # Per-token overrides
    if TOKEN_GEMS_OVERRIDES:
        print(f"  {ui.dim('Overrides:')}  {ui.secondary(f'{len(TOKEN_GEMS_OVERRIDES)} token(s) with custom gems')}")
    
    print()
    print(ui.header("  DEPLOYMENT"))
    print()
    
    confirm = input(ui.primary("  Start all engines? (y/N): ")).strip().lower()
    if confirm != 'y':
        print(ui.warning("  Aborted."))
        return
    
    # Register signal handler
    signal.signal(signal.SIGINT, signal_handler)
    
    print()
    print(ui.success(f"  🚀 Launching {len(CONFIG['DISCORD_TOKENS'])} engine(s)..."))
    print(ui.dim("  ─" * 30))
    print()
    
    # Start engines
    global running_bots
    threads = []
    
    for i, token in enumerate(CONFIG["DISCORD_TOKENS"]):
        bot = CombiusEngine(token, CONFIG["CHANNEL_IDS"], i)
        running_bots.append(bot)
        t = threading.Thread(target=bot.run, daemon=True)
        threads.append(t)
        t.start()
        # Stagger launches (human-like)
        stagger = random.uniform(3, 8)
        time.sleep(stagger)
    
    print()
    print(ui.success(f"  ✅ {len(running_bots)} engine(s) running. Press Ctrl+C to stop all.\n"))
    
    try:
        while any(t.is_alive() for t in threads):
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    print(ui.warning("\n  ⛔ Shutting down all engines..."))
    for bot in running_bots:
        bot.stop()
    print(ui.success("\n  ✅ All engines stopped. Thank you for using Combius.\n"))


if __name__ == "__main__":
    # Check for imports
    try:
        import requests
    except ImportError:
        print("[!] Missing 'requests' module. Install: pip install requests")
        sys.exit(1)
    
    try:
        from dotenv import load_dotenv
    except ImportError:
        pass  # Optional
    
    main()
