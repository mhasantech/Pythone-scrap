from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bdshare import get_current_trade_data
import time

app = FastAPI()

# ওয়েবসাইট থেকে ডেটা অ্যাক্সেসের অনুমতি দেওয়া
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cached_data = None
last_update_time = 0
UPDATE_INTERVAL = 180  # ৩ মিনিট

def fetch_dse_data_with_retry(retries=3, delay=2):
    """ব্যর্থ হলে ৩ বার পর্যন্ত পুনরায় চেষ্টা করবে"""
    for i in range(retries):
        try:
            print(f"DSE থেকে ডেটা আনার চেষ্টা করা হচ্ছে (ধাপ {i+1})...")
            df = get_current_trade_data()
            if df is not None and not df.empty:
                # ডেটা সঠিকভাবে পাওয়া গেলে JSON ফরম্যাটে কনভার্ট করবে
                data_json = df.to_dict(orient="records")
                return data_json
        except Exception as e:
            print(f"চেষ্টা {i+1} ব্যর্থ হয়েছে: {e}")
            time.sleep(delay)
    return None

@app.get("/")
def home():
    return {
        "message": "DSE Live API is running!", 
        "endpoint": "/live-stocks",
        "status": "active"
    }

@app.get("/live-stocks")
def get_live_stocks():
    global cached_data, last_update_time
    current_time = time.time()
    
    # যদি ক্যাশ খালি থাকে অথবা ৩ মিনিট পার হয়ে যায়
    if cached_data is None or (current_time - last_update_time) > UPDATE_INTERVAL:
        new_data = fetch_dse_data_with_retry()
        if new_data:
            cached_data = new_data
            last_update_time = current_time
            print("DSE থেকে নতুন ডেটা ক্যাশ করা হয়েছে।")
        else:
            # যদি নতুন স্ক্র্যাপিং ব্যর্থ হয়, তবে আগের জমানো ডেটাই ব্যাকআপ হিসেবে দেখাবে
            if cached_data is not None:
                print("নতুন ডেটা পাওয়া যায়নি, পুরোনো ক্যাশ ডেটা পাঠানো হচ্ছে।")
            else:
                print("কোনো ডেটা পাওয়া যায়নি এবং ক্যাশ খালি।")
                
    return {
        "status": "success" if cached_data else "fetching_or_market_closed", 
        "last_updated_epoch": last_update_time, 
        "data": cached_data
    }
