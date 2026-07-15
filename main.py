from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bdshare import get_current_trade_data
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

cached_data = None
last_update_time = 0
UPDATE_INTERVAL = 180 # ৩ মিনিট

def fetch_dse_data():
    try:
        df = get_current_trade_data()
        if df is not None and not df.empty:
            data_json = df.to_dict(orient="records")
            return data_json
        return None
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# সার্ভার চালু হওয়ার সাথে সাথেই একবার ব্যাকগ্রাউন্ডে ডেটা স্ক্র্যাপ করে রাখবে
try:
    print("সার্ভার চালু হচ্ছে, প্রথমবার ডেটা স্ক্র্যাপ করা হচ্ছে...")
    cached_data = fetch_dse_data()
    if cached_data:
        last_update_time = time.time()
except Exception as e:
    print(f"Startup fetch failed: {e}")

@app.get("/")
def home():
    return {"message": "DSE Live API is running!", "endpoint": "/live-stocks"}

@app.get("/live-stocks")
def get_live_stocks():
    global cached_data, last_update_time
    current_time = time.time()
    
    # ৩ মিনিট পর পর আপডেট হবে
    if cached_data is None or (current_time - last_update_time) > UPDATE_INTERVAL:
        new_data = fetch_dse_data()
        if new_data:
            cached_data = new_data
            last_update_time = current_time
            print("Successfully updated from DSE")
            
    return {
        "status": "success", 
        "last_updated_epoch": last_update_time, 
        "data": cached_data
    }
