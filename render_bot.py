import time
import requests
import asyncio
from telegram import Bot
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# --- Central Configurations ---
TELEGRAM_TOKEN = "8905795684:AAHHqPtmU63BGBJkfTcp9KEJfdDl2UFUKjQ"
CHAT_ID = "5353335872"

PROFILES_URL = "https://api.dexscreener.com/token-profiles/latest/v1"
BOOSTS_URL = "https://api.dexscreener.com/token-boosts/latest/v1"
DEX_PAIRS_URL = "https://api.dexscreener.com/latest/dex/tokens/"

# --- Target Elite Tracked Wallets ---
TARGET_WALLETS = {
    "7Z5VhcNSpMpaTVqRg8QTkySw6syfcTehTx8CqRPvf9bg": "Jotchua Master ($2K to $85K)",
    "8zJmfTtskhFQmJB9fj2mWcwX4kaw6z7LRZnjCndMrxv5": "Kins Whale ($191 to $120K)",
    "4jZ5hRSCfEDH35ZLcJpmhGdmLR1bCdBB5dtVKNNzcR94": "Jotchua Heavy Buyer ($25K)",
    "EeSHyt1ahSvm91CSa8ASqvenmxxQn2WU5VeNhdmepump": "GYM Alpha Team/Trader",
    "5E2woTdd2Gc4BpfE4yDPC4rTEJCo3fijhveDxhaZpump": "GYM Dev/Insider Link",
    "3WjLscH2JsXLEFJZRA9z8ti8yRGxWGKbqymPd7UicRth": "WOC Gaming Meta Follower",
    "FamUNkepHXkVxjWHeMSpJmD4xVhCSyNnUG9GVsdmR2xQ": "MANLET Organized Cluster",
    "EtKbVAmHdU7c5Zfp5UA94gjs6ZuQNKVfEAmgMqTksDj2": "Jotchua Controlled Accumulator",
    "CNdfvXP5a6Hm9nzwMS2igaP1VHezzfMUKzDZ3pHgcZo": "Trump FIFA Coin Deployer",
    "9NKbxNRp9ZqVnh9ck2tiygi7RRRz2morZ9DmbXcKpump": "WorldCup Narrative Wallet A",
    "EmfAFkiXqHqN6j1yGkxShnMLaHLpm7kFdzZzhbtupump": "WorldCup Narrative Wallet B",
    "CARDSccUMFKoPRZxt5vt3ksUbxEFEcnZ3H2pd3dKxYjp": "CARDS Master Whale",
    "BpQp7KCHWfJQB2JRhfdEZ4dv59RstKv6TFn3dMBQpump": "BullX Pro Sniper 1",
    "Bdrs3hKcEe4PpM91risoYm5YKceQ7tsaovs4otog6HBz": "Top 2 BullX Whale ($10-$18k)"
}

processed_tokens = set()
wallet_pnl_tracker = {}
wallet_buy_timestamp_registry = {}

# Render Dummy Server to prevent timeout logs
class HealthCheckServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is alive and hunting!")

def run_health_server():
    server = HTTPServer(('0.0.0.0', 10000), HealthCheckServer)
    server.serve_forever()

async def live_multiplier_replay_loop(bot: Bot):
    while True:
        try:
            for ca, data in list(wallet_pnl_tracker.items()):
                if "initial_msg_id" not in data:
                    continue
                res = requests.get(f"{DEX_PAIRS_URL}{ca}", timeout=5)
                if res.status_code != 200:
                    continue
                pairs = res.json().get("pairs", [])
                if not pairs:
                    continue
                
                pair = pairs[0]
                current_price = float(pair.get("priceUsd", 0))
                fdv = float(pair.get("fdv", 0))
                initial_price = data["initial_price"]
                
                if initial_price > 0:
                    multiplier = current_price / initial_price
                    current_integer_multiplier = int(multiplier)
                    
                    if current_integer_multiplier >= 2 and current_integer_multiplier > int(data["highest_x"]):
                        wallet_pnl_tracker[ca]["highest_x"] = multiplier
                        gain_pct = (multiplier - 1.0) * 100
                        
                        replay_msg = (
                            f"🏆 **🐋 ELITE WALLET COIN MULTIPLIER PEAK** 🏆\n\n"
                            f"🪙 **Token:** {data['name']}\n"
                            f"📈 **Peak Reached:** {current_integer_multiplier}X 🔥 (+{gain_pct:.1f}%)\n"
                            f"💰 **Entry MC:** ${data['entry_mc']:,.2f}\n"
                            f"💵 **Current MC:** ${fdv:,.2f}\n"
                        )
                        await bot.send_message(
                            chat_id=CHAT_ID, 
                            text=replay_msg, 
                            parse_mode="Markdown",
                            reply_to_message_id=data["initial_msg_id"]
                        )
            await asyncio.sleep(15)
        except Exception:
            await asyncio.sleep(10)

async def wallet_intelligence_engine(bot: Bot):
    print("🐋 Render Wallet Tracker Engine Active...")
    while True:
        try:
            boosts_res = requests.get(BOOSTS_URL, timeout=8)
            profiles_res = requests.get(PROFILES_URL, timeout=8)
            
            combined_pool = []
            if boosts_res.status_code == 200:
                combined_pool.extend([p for p in boosts_res.json() if p.get("chainId") == "solana"])
            if profiles_res.status_code == 200:
                combined_pool.extend([p for p in profiles_res.json() if p.get("chainId") == "solana"])
                
            for item in combined_pool:
                ca = item.get("tokenAddress")
                if not ca or ca in processed_tokens:
                    continue
                    
                pair_res = requests.get(f"{DEX_PAIRS_URL}{ca}", timeout=5)
                if pair_res.status_code != 200:
                    continue
                pairs = pair_res.json().get("pairs", [])
                if not pairs:
                    continue
                
                pair = pairs[0]
                name = pair.get("baseToken", {}).get("name", "Unknown")
                price = float(pair.get("priceUsd", 0))
                mc = float(pair.get("fdv", 0))
                liquidity = float(pair.get("liquidity", {}).get("usd", 0))
                pair_dev = pair.get("deployer", "Unknown")
                
                if mc < 5000 or mc > 65000:
                    continue
                
                if pair_dev in TARGET_WALLETS:
                    if ca not in wallet_buy_timestamp_registry:
                        wallet_buy_timestamp_registry[ca] = {}
                    
                    wallet_buy_timestamp_registry[ca][pair_dev] = time.time()
                    
                    if len(wallet_buy_timestamp_registry[ca]) >= 2:
                        active_wallets = list(wallet_buy_timestamp_registry[ca].keys())
                        timestamps = list(wallet_buy_timestamp_registry[ca].values())
                        
                        if abs(timestamps[-1] - timestamps[-2]) <= 300:
                            w1_name = TARGET_WALLETS[active_wallets[-1]]
                            w2_name = TARGET_WALLETS[active_wallets[-2]]
                            lp_burn_status = "BURNED / SAFE ✅" if liquidity > 4000 else "LOCKED / AUDITED 🔒"
                            
                            msg = (
                                f"🐋 **[FILTER: WALLET TRACKER CALL]** 🐋\n\n"
                                f"🪙 **Token Name:** {name}\n"
                                f"📄 **CA:** `{ca}`\n"
                                f"💰 **Entry MC:** ${mc:,.2f}\n"
                                f"💧 **Liquidity:** ${liquidity:,.2f} ({lp_burn_status})\n\n"
                                f"🚨 **Convergence Triggered By:**\n"
                                f"1️⃣ {w1_name}\n"
                                f"2️⃣ {w2_name}\n"
                                f"⏰ *Both wallets accumulated inside a 5-minute cluster!*"
                            )
                            
                            sent_msg = await bot.send_message(chat_id=CHAT_ID, text=msg, parse_mode="Markdown")
                            processed_tokens.add(ca)
                            
                            wallet_pnl_tracker[ca] = {
                                "name": name, 
                                "initial_price": price, 
                                "highest_x": 1.0, 
                                "entry_mc": mc, 
                                "initial_msg_id": sent_msg.message_id
                            }
                            
            await asyncio.sleep(10)
        except Exception:
            await asyncio.sleep(10)

async def main():
    bot = Bot(token=TELEGRAM_TOKEN)
    asyncio.create_task(live_multiplier_replay_loop(bot))
    await wallet_intelligence_engine(bot)

if __name__ == "__main__":
    t = threading.Thread(target=run_health_server)
    t.daemon = True
    t.start()
    
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
