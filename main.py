from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from bdshare import get_current_trade_data
import time

app = FastAPI()

# আপনার ওয়েবসাইট যাতে কোনো বাধা ছাড়াই ডেটা নিতে পারে (CORS Policy সমাধান)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ডেটা ক্যাশ এবং ৩ মিনিট সময় নির্ধারণ
cached_data = None
last_update_time = 0
UPDATE_INTERVAL = 180 # ১৮০ সেকেন্ড বা ৩ মিনিট

def fetch_dse_data():
    try:
        df = get_current_trade_data()
        # pandas dataframe-কে সহজে পড়ার উপযোগী ডিকশনারি ফরমেটে নেওয়া
        data_json = df.to_dict(orient="records")
        return data_json
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

@app.get("/")
def home():
    return {"message": "DSE Live API is running!", "endpoint": "/live-stocks"}

@app.get("/live-stocks")
def get_live_stocks():
    global cached_data, last_update_time
    current_time = time.time()
    
    # যদি ৩ মিনিট পার হয়ে যায় বা ক্যাশে কোনো ডেটা না থাকে
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
