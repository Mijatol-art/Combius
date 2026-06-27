#!/usr/bin/env python3
"""
OWO MULTI-TOKEN SELFBOT v4.0
- All config from .env
- AUTO INVENTORY SCANNING: Parses owo inv response for gem IDs
- AUTO LOOTBOX: owo lb all when lootboxes detected
- AUTO CRATE: owo wc all when weapon crates detected
- Auto gem scanning and equipping
- Railway/GitHub safe
"""

import os
import sys
import json
import re
import random
import time
import threading
import requests
from datetime import datetime
from pathlib import Path

# ====== LOAD .ENV ======
try:
    from dotenv import load_dotenv
    if not os.environ.get('RAILWAY_PROJECT_ID'):
        env_path = Path(__file__).parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
except ImportError:
    pass

# ====== CONFIG FROM ENV ======
def env_bool(key, default=False):
    return os.environ.get(key, str(default)).strip().lower() in ('true', '1', 'yes', 'on')

def env_int(key, default=0):
    try: return int(os.environ.get(key, default))
    except: return default

def env_list(key, default=""):
    return [x.strip() for x in os.environ.get(key, default).split(',') if x.strip()]

DISCORD_TOKENS = env_list('DISCORD_TOKENS')
CHANNEL_IDS = env_list('CHANNEL_IDS')
valid_channels = [c for c in CHANNEL_IDS if c.isdigit()]

MIN_DELAY = env_int('MIN_DELAY', 20)
MAX_DELAY = env_int('MAX_DELAY', 40)
SELLALL_INTERVAL = env_int('SELLALL_INTERVAL', 100)
SELLALL_COOLDOWN = env_int('SELLALL_COOLDOWN', 600)

GEM_ENABLED = env_bool('GEM_ENABLED', True)
GEM_IDS_DEFAULT = [int(x) for x in env_list('GEM_IDS', '51,52,53,56') if x.isdigit()]

INVENTORY_CHECK_INTERVAL = env_int('INVENTORY_CHECK_INTERVAL', 20)
AUTO_OPEN_LOOTBOXES = env_bool('AUTO_OPEN_LOOTBOXES', True)
AUTO_OPEN_CRATES = env_bool('AUTO_OPEN_CRATES', True)
AUTO_CLAIM = env_bool('AUTO_CLAIM', True)
VERIFY_SOUND = env_bool('VERIFY_SOUND', True)
AUTO_SCAN_GEMS = env_bool('AUTO_SCAN_GEMS', True)

CAPTCHA_SERVICE = os.environ.get('CAPTCHA_SERVICE', 'manual')

TOKEN_GEMS_OVERRIDES = {}
for key, val in os.environ.items():
    if key.startswith('TOKEN_GEMS_'):
        prefix = key[11:]
        try:
            ids = [int(x) for x in val.split(',') if x.strip().isdigit()]
            if ids: TOKEN_GEMS_OVERRIDES[prefix] = ids
        except: pass

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# Validation
if not DISCORD_TOKENS:
    print("[!] No DISCORD_TOKENS in environment!")
    sys.exit(1)
if not valid_channels:
    print("[!] No valid CHANNEL_IDS in environment!")
    sys.exit(1)

print(f"[+] Loaded {len(DISCORD_TOKENS)} token(s), {len(valid_channels)} channel(s)")
print(f"[+] Delay: {MIN_DELAY}s-{MAX_DELAY}s | Sellall: every {SELLALL_INTERVAL} / {SELLALL_COOLDOWN}s cd")
print(f"[+] Gems: {GEM_IDS_DEFAULT if GEM_ENABLED else 'OFF'} | Auto-scan gems: {AUTO_SCAN_GEMS}")
print(f"[+] Auto lootboxes: {AUTO_OPEN_LOOTBOXES} | Auto crates: {AUTO_OPEN_CRATES}")

# ====== API ======
HEADERS_TPL = {
    "Content-Type": "application/json",
    "User-Agent": USER_AGENT,
    "Origin": "https://discord.com",
    "Referer": "https://discord.com/channels/@me"
}

def discord_get(token, url):
    headers = {**HEADERS_TPL, "Authorization": token}
    try:
        r = requests.get(url, headers=headers, timeout=10)
        return r if r.status_code == 200 else None
    except: return None

def discord_post(token, url, data=None):
    headers = {**HEADERS_TPL, "Authorization": token}
    try:
        r = requests.post(url, headers=headers, json=data or {}, timeout=10)
        return r
    except: return None

def send_message(token, channel_id, content):
    r = discord_post(token, f"https://discord.com/api/v9/channels/{channel_id}/messages", {"content": content})
    if r and r.status_code == 200:
        return r.json()
    if r and r.status_code == 429:
        retry = r.json().get('retry_after', 5)
        time.sleep(retry + 1)
    return None

def get_recent_messages(token, channel_id, limit=10):
    r = discord_get(token, f"https://discord.com/api/v9/channels/{channel_id}/messages?limit={limit}")
    return r.json() if r else []

def get_username(token):
    r = discord_get(token, "https://discord.com/api/v9/users/@me")
    if r:
        d = r.json()
        return f"{d.get('username','?')}#{d.get('discriminator','0000')}"
    return "Unknown"

def check_verification(token, channel_id):
    msgs = get_recent_messages(token, channel_id, limit=3)
    for m in msgs:
        c = m.get("content", "").lower()
        a = m.get("author", {}).get("username", "").lower()
        if "owo" in a or "owo" in c:
            if any(w in c for w in ["human", "verify", "captcha", "verification", "are you human"]):
                return True
    return False

def play_alert():
    try:
        import winsound
        for _ in range(5): winsound.Beep(1000, 300); time.sleep(0.2)
    except:
        print("\a" * 5)
    print("\n[!!!] 🔔 HUMAN VERIFICATION DETECTED!")


# ====== INVENTORY PARSER ======
def parse_inventory_response(messages, own_user_id):
    """
    Parse owo inv response to extract:
    - Available gem IDs (so we can equip them)
    - Lootbox count
    - Weapon crate count
    - Fabled lootbox count
    
    OWO inventory format (typical):
    ⠀**Inventory**
    ⠀49  × 2  ⠀Fabled Lootbox
    ⠀50  × 15 ⠀Lootbox
    ⠀51  × 3  ⠀Common Hunting Gem
    ⠀52  × 2  ⠀Uncommon Hunting Gem
    ⠀53  × 1  ⠀Rare Hunting Gem
    ⠀56  × 1  ⠀Legendary Hunting Gem
    ⠀65  × 1  ⠀Common Empowering Gem
    ⠀72  × 4  ⠀Common Lucky Gem
    ⠀100 × 8  ⠀Weapon Crate
    """
    result = {
        "gem_ids": [],          # All gem IDs found
        "gem_count": {},        # id -> count
        "lootbox_count": 0,
        "fabled_lootbox_count": 0,
        "crate_count": 0,
        "has_inventory": False
    }
    
    for msg in messages:
        content = msg.get("content", "")
        author_id = msg.get("author", {}).get("id", "")
        
        # Only check bot messages (not our own)
        if author_id == own_user_id:
            continue
            
        # Check if this is the OWO bot's inventory response
        if "**Inventory**" not in content and "Inventory" not in content:
            continue
        
        result["has_inventory"] = True
        
        # Parse each line for item IDs and counts
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            
            # Match patterns like: "51  × 3  ⠀Common Hunting Gem" or "50  × 15 ⠀Lootbox"
            # or "49  × 2  ⠀Fabled Lootbox"
            match = re.search(r'(\d+)\s*[×x]\s*(\d+)', line)
            if match:
                item_id = int(match.group(1))
                count = int(match.group(2))
                
                # Lootbox (ID: 50)
                if item_id == 50:
                    result["lootbox_count"] = count
                # Fabled Lootbox (ID: 49)
                elif item_id == 49:
                    result["fabled_lootbox_count"] = count
                # Weapon Crate (ID: 100)
                elif item_id == 100:
                    result["crate_count"] = count
                # Gems (IDs: 51-57, 65-78)
                elif (51 <= item_id <= 57) or (65 <= item_id <= 78):
                    result["gem_ids"].append(item_id)
                    result["gem_count"][item_id] = count
        
        # Break after finding the inventory response
        break
    
    return result


# ====== OWO SELFBOT ======
class OWOSelfbot:
    def __init__(self, token, channels):
        self.token = token
        self.channels = channels
        self.username = get_username(token)
        self.user_id = self._get_user_id()
        self.command_count = 0
        self.cycle_count = 0
        self.running = True
        self.last_gem_check = 0
        self.last_inv_check = 0
        self.last_inv_scan = 0
        self.last_claim = 0
        self.gems_active = False
        self.last_channel_used = None
        
        # Dynamically discovered gems from inventory
        self.discovered_gems = []
        self.last_discovered_gems_equip = 0
        
        # Resolve gem IDs
        self.gem_ids = self._resolve_gem_ids()
        
        # Track what we've opened this session
        self.lootboxes_opened_this_session = 0
    
    def _get_user_id(self):
        r = discord_get(self.token, "https://discord.com/api/v9/users/@me")
        if r:
            return r.json().get("id")
        return None
    
    def _resolve_gem_ids(self):
        for prefix, ids in TOKEN_GEMS_OVERRIDES.items():
            if self.token.startswith(prefix):
                print(f"  [{self.username}] Custom gems: {ids}")
                return ids
        return GEM_IDS_DEFAULT
    
    def _tag(self): return f"[{self.username}]"
    def _pick_channel(self):
        ch = random.choice(self.channels)
        self.last_channel_used = ch
        return ch
    def _get_delay(self): return random.uniform(MIN_DELAY, MAX_DELAY)
    
    def _get_owo_cmd(self):
        cmds = ["owo"] * 4 + ["owo hunt"] * 3 + ["owo battle"] * 2 + ["owo dig", "owo fish", "owo pray"]
        return random.choice(cmds)
    
    def _check_verify(self, channel_id=None):
        ch = channel_id or self.last_channel_used or self._pick_channel()
        if check_verification(self.token, ch):
            if VERIFY_SOUND: play_alert()
            print(f"{self._tag()} [!!!] HUMAN VERIFICATION!")
            input(f"{self._tag()} Press Enter after verifying...")
            print(f"{self._tag()} Resuming...")
            return True
        return False
    
    # ====== INVENTORY SCANNING ======
    def _scan_inventory(self):
        """
        Scan inventory by sending 'owo inv' and parsing the response.
        Returns parsed inventory data.
        """
        channel = self._pick_channel()
        
        print(f"{self._tag()} 🔍 Scanning inventory...")
        
        # Send owo inv
        send_message(self.token, channel, "owo inv")
        
        # Wait for OWO bot to respond
        time.sleep(random.uniform(2.5, 4.0))
        
        # Fetch recent messages
        msgs = get_recent_messages(self.token, channel, limit=10)
        
        # Parse the inventory
        inv_data = parse_inventory_response(msgs, self.user_id)
        
        if inv_data["has_inventory"]:
            print(f"{self._tag()} 📋 Inventory scan complete")
            if inv_data["gem_ids"]:
                print(f"{self._tag()} 💎 Gems found: {inv_data['gem_ids']} (counts: {inv_data['gem_count']})")
                # Store discovered gems for later equipping
                self.discovered_gems = inv_data["gem_ids"]
            if inv_data["lootbox_count"] > 0:
                print(f"{self._tag()} 📦 Lootboxes: {inv_data['lootbox_count']}")
            if inv_data["fabled_lootbox_count"] > 0:
                print(f"{self._tag()} ⭐ Fabled lootboxes: {inv_data['fabled_lootbox_count']}")
            if inv_data["crate_count"] > 0:
                print(f"{self._tag()} 📦 Weapon crates: {inv_data['crate_count']}")
        else:
            print(f"{self._tag()} ⚠️ Could not parse inventory (might need a moment)")
        
        return inv_data
    
    def _do_gem_equip_from_scan(self):
        """Equip gems based on scanned inventory - uses best available gems."""
        if not self.discovered_gems:
            print(f"{self._tag()} ⚠️ No gems discovered yet, scanning first...")
            return
        
        channel = self._pick_channel()
        
        # Strategy: equip best hunting gem + best empowering + best lucky
        hunting = [g for g in self.discovered_gems if 51 <= g <= 57]
        empowering = [g for g in self.discovered_gems if 65 <= g <= 71]
        lucky = [g for g in self.discovered_gems if 72 <= g <= 78]
        
        to_equip = []
        if hunting: to_equip.append(max(hunting))  # Best hunting gem
        if empowering: to_equip.append(max(empowering))  # Best empowering gem
        if lucky: to_equip.append(max(lucky))  # Best lucky gem
        
        if not to_equip:
            # Fallback to configured gems
            to_equip = self.gem_ids[:3]
        
        ids_str = " ".join(str(g) for g in to_equip)
        cmd = f"owo use {ids_str}"
        send_message(self.token, channel, cmd)
        print(f"{self._tag()} 💎 Equipped scanned gems: {to_equip}")
        self.gems_active = True
        self.last_gem_check = self.cycle_count
        self.last_discovered_gems_equip = self.cycle_count
    
    def _do_open_lootboxes(self, count=None):
        """Open all lootboxes using owo lb all"""
        channel = self._pick_channel()
        
        if count and count > 0:
            # Open in batches of 100 (max per command)
            batch_size = min(count, 100)
            cmd = f"owo lb {batch_size}" if batch_size > 1 else "owo lb"
            send_message(self.token, channel, cmd)
            print(f"{self._tag()} 📦 Opened {batch_size} lootbox(es)")
            self.lootboxes_opened_this_session += batch_size
            time.sleep(random.uniform(2, 3))
            
            remaining = count - batch_size
            if remaining > 0:
                # Open remaining in next cycle
                print(f"{self._tag()} 📦 {remaining} lootboxes remaining for next cycle")
        else:
            # Just use 'owo lb all'
            send_message(self.token, channel, "owo lb all")
            print(f"{self._tag()} 📦 Opened ALL lootboxes (owo lb all)")
            self.lootboxes_opened_this_session += 999  # Approximate
    
    def _do_open_crates(self, count=None):
        """Open all weapon crates using owo wc all"""
        channel = self._pick_channel()
        
        if count and count > 0:
            batch_size = min(count, 50)  # Max 50 per command
            cmd = f"owo wc {batch_size}" if batch_size > 1 else "owo wc"
            send_message(self.token, channel, cmd)
            print(f"{self._tag()} 📦 Opened {batch_size} weapon crate(s)")
            time.sleep(random.uniform(2, 3))
            
            remaining = count - batch_size
            if remaining > 0:
                print(f"{self._tag()} 📦 {remaining} crates remaining for next cycle")
        else:
            send_message(self.token, channel, "owo wc all")
            print(f"{self._tag()} 📦 Opened ALL weapon crates (owo wc all)")
    
    def _do_open_fabled(self, count=None):
        """Open fabled lootboxes using owo use 49"""
        channel = self._pick_channel()
        
        if count and count > 0:
            for _ in range(min(count, 5)):  # Max 5 at a time to avoid spam
                send_message(self.token, channel, "owo use 49")
                print(f"{self._tag()} ⭐ Opened fabled lootbox")
                time.sleep(random.uniform(2, 3))
        else:
            # Just do one
            send_message(self.token, channel, "owo use 49")
            print(f"{self._tag()} ⭐ Opened fabled lootbox")
    
    def _do_gem_equip(self):
        """Fallback gem equip using configured IDs"""
        channel = self._pick_channel()
        selected = self.gem_ids[:random.randint(1, min(4, len(self.gem_ids)))]
        cmd = f"owo use {' '.join(str(g) for g in selected)}"
        send_message(self.token, channel, cmd)
        print(f"{self._tag()} 💎 Gems equipped (config): {selected}")
        self.gems_active = True
        self.last_gem_check = self.cycle_count
    
    def _do_sellall(self):
        self.command_count = 0
        channel = self._pick_channel()
        print(f"{self._tag()} ⚡ SELLALL!")
        send_message(self.token, channel, "owo sellall")
        print(f"{self._tag()} 😴 Cooldown: {SELLALL_COOLDOWN//60}min")
        end = time.time() + SELLALL_COOLDOWN
        while time.time() < end and self.running:
            self._check_verify()
            time.sleep(10)
        print(f"{self._tag()} ✅ Resuming")
    
    def _do_claim(self):
        channel = self._pick_channel()
        send_message(self.token, channel, "owo claim")
        print(f"{self._tag()} 🎁 Claimed")
        time.sleep(random.uniform(1, 2))
        send_message(self.token, channel, "owo daily")
        print(f"{self._tag()} 📅 Daily sent")
        self.last_claim = time.time()
    
    # ====== MAIN LOOP ======
    def run(self):
        print(f"{self._tag()} ✅ Started")
        if self.discovered_gems:
            print(f"{self._tag()} 💎 Scanned gems: {self.discovered_gems}")
        else:
            print(f"{self._tag()} 💎 Config gems: {self.gem_ids}")
        
        while self.running:
            try:
                # ---- Periodic: Claim (~8 hours) ----
                if AUTO_CLAIM:
                    if self.last_claim == 0 and self.cycle_count > 5:
                        self._do_claim()
                    elif self.last_claim > 0 and (time.time() - self.last_claim > 28800):
                        self._do_claim()
                
                # ---- Periodic: Scan inventory every N cycles ----
                if INVENTORY_CHECK_INTERVAL > 0 and self.cycle_count > 0 \
                   and self.cycle_count % INVENTORY_CHECK_INTERVAL == 0:
                    
                    inv = self._scan_inventory()
                    
                    # Auto-open lootboxes
                    if AUTO_OPEN_LOOTBOXES and inv["lootbox_count"] > 0:
                        self._do_open_lootboxes(inv["lootbox_count"])
                        time.sleep(random.uniform(2, 4))
                    
                    # Auto-open fabled lootboxes
                    if AUTO_OPEN_LOOTBOXES and inv["fabled_lootbox_count"] > 0:
                        self._do_open_fabled(inv["fabled_lootbox_count"])
                        time.sleep(random.uniform(2, 4))
                    
                    # Auto-open weapon crates
                    if AUTO_OPEN_CRATES and inv["crate_count"] > 0:
                        self._do_open_crates(inv["crate_count"])
                        time.sleep(random.uniform(2, 4))
                    
                    # Scan again after opening (to get new gems)
                    if AUTO_OPEN_LOOTBOXES and (inv["lootbox_count"] > 0 or inv["fabled_lootbox_count"] > 0):
                        time.sleep(random.uniform(3, 5))
                        inv2 = self._scan_inventory()
                        if inv2["has_inventory"] and inv2["gem_ids"]:
                            self.discovered_gems = inv2["gem_ids"]
                    
                    self.last_inv_check = self.cycle_count
                
                # ---- Equip gems ----
                if GEM_ENABLED:
                    if not self.gems_active:
                        if AUTO_SCAN_GEMS and self.discovered_gems:
                            self._do_gem_equip_from_scan()
                        else:
                            self._do_gem_equip()
                    elif self.cycle_count - self.last_gem_check > 25:
                        # Re-equip (gems expire)
                        self.gems_active = False
                
                # ---- Main command ----
                channel = self._pick_channel()
                cmd = self._get_owo_cmd()
                
                self.command_count += 1
                self.cycle_count += 1
                
                print(f"{self._tag()} [{datetime.now().strftime('%H:%M:%S')}] #{self.command_count} '{cmd}'")
                send_message(self.token, channel, cmd)
                
                # Check verification
                self._check_verify(channel)
                
                # Sellall check
                if self.command_count >= SELLALL_INTERVAL:
                    self._do_sellall()
                    continue
                
                # Delay with verification checks
                delay = self._get_delay()
                elapsed = 0
                while elapsed < delay and self.running:
                    time.sleep(1)
                    elapsed += 1
                    if int(elapsed) % 5 == 0 and elapsed > 0:
                        self._check_verify()
                
            except KeyboardInterrupt:
                print(f"\n{self._tag()} Stopped")
                self.running = False
                break
            except Exception as e:
                print(f"{self._tag()} Error: {e}")
                time.sleep(15)
    
    def stop(self):
        self.running = False


# ====== MAIN ======
def main():
    print()
    print("  ╔═══════════════════════════════════════════════╗")
    print("  ║      OWO MULTI-TOKEN SELFBOT v4.0            ║")
    print("  ║   Auto Inventory | Gems | LB | WC | Sellall   ║")
    print("  ╚═══════════════════════════════════════════════╝")
    print()
    
    if os.environ.get('RAILWAY_PROJECT_ID'):
        print("[+] Running on Railway")
    
    print(f"  Tokens:  {len(DISCORD_TOKENS)}")
    print(f"  Channels: {len(valid_channels)}")
    print(f"  Delay:   {MIN_DELAY}s - {MAX_DELAY}s")
    print(f"  Sellall: every {SELLALL_INTERVAL} / {SELLALL_COOLDOWN}s")
    print(f"  Gems:    {GEM_IDS_DEFAULT if GEM_ENABLED else 'OFF'} (auto-scan: {AUTO_SCAN_GEMS})")
    print(f"  LB:      {'AUTO' if AUTO_OPEN_LOOTBOXES else 'OFF'}")
    print(f"  WC:      {'AUTO' if AUTO_OPEN_CRATES else 'OFF'}")
    print(f"  Captcha: {CAPTCHA_SERVICE}")
    print()
    
    bots = []
    threads = []
    
    for token in DISCORD_TOKENS:
        bot = OWOSelfbot(token, valid_channels)
        bots.append(bot)
        t = threading.Thread(target=bot.run, daemon=True)
        threads.append(t)
        t.start()
        time.sleep(random.uniform(2, 5))
    
    print(f"\n  ✅ {len(bots)} bot(s) running. Ctrl+C to stop.\n")
    
    try:
        while any(t.is_alive() for t in threads):
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n  ⛔ Shutting down...")
        for bot in bots:
            bot.stop()
        print("  ✅ Done.\n")


if __name__ == "__main__":
    main()