import time
import threading
from datetime import datetime
import requests

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import HTMLResponse
import uvicorn

from config import config
from src.fetcher import StockFetcher, fetch_and_write_historical
from src.storage import get_storage_backend
from src.ticker_manager import TickerManager

app = FastAPI()
ticker_manager = TickerManager()

html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Ticker Manager</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 20px; background-color: #f4f6f8; color: #333; }
        .container { max-width: 600px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        h1 { font-size: 24px; margin-bottom: 20px; }
        ul { list-style-type: none; padding: 0; }
        li { background: #e9ecef; margin: 5px 0; padding: 10px; border-radius: 4px; display: flex; justify-content: space-between; align-items: center; }
        button { background: #dc3545; color: white; border: none; padding: 5px 10px; border-radius: 4px; cursor: pointer; }
        button:hover { background: #c82333; }
        .add-form, .search-form { display: flex; margin-bottom: 20px; }
        input[type="text"] { flex-grow: 1; padding: 10px; border: 1px solid #ced4da; border-radius: 4px 0 0 4px; }
        .add-btn { background: #28a745; border-radius: 0 4px 4px 0; }
        .add-btn:hover { background: #218838; }
        .search-btn { background: #007bff; border-radius: 0 4px 4px 0; }
        .search-btn:hover { background: #0069d9; }
        #searchResults li { background: #e2e3e5; margin-bottom: 5px; font-size: 14px; }
        .divider { border-top: 1px solid #dee2e6; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Manage Tickers</h1>
        
        <div class="search-form">
            <input type="text" id="searchInput" placeholder="Search by Company Name (e.g. Samsung, Apple)">
            <button class="search-btn" onclick="searchTicker()">Search</button>
        </div>
        <ul id="searchResults"></ul>

        <div class="divider"></div>

        <div class="add-form">
            <input type="text" id="tickerInput" placeholder="Enter Exact Ticker (e.g., 005930.KS)">
            <button class="add-btn" onclick="addTicker()">Add Directly</button>
        </div>
        
        <h3>Current Tickers</h3>
        <ul id="tickerList"></ul>
    </div>
    <script>
        async function fetchTickers() {
            const response = await fetch('/tickers');
            const tickers = await response.json();
            const list = document.getElementById('tickerList');
            list.innerHTML = '';
            tickers.forEach(t => {
                const li = document.createElement('li');
                li.innerText = `${t.name} (${t.symbol})`;
                const btn = document.createElement('button');
                btn.innerText = 'Delete';
                btn.onclick = () => deleteTicker(t.symbol);
                li.appendChild(btn);
                list.appendChild(li);
            });
        }
        
        async function searchTicker() {
            const input = document.getElementById('searchInput');
            const q = input.value.trim();
            if (q) {
                const response = await fetch(`/search?q=${encodeURIComponent(q)}`);
                const data = await response.json();
                const list = document.getElementById('searchResults');
                list.innerHTML = '';
                
                if (data.status === 'success' && data.results) {
                    if (data.results.length === 0) {
                        list.innerHTML = '<li style="justify-content:center; color:#6c757d;">No results found</li>';
                        return;
                    }
                    data.results.forEach(res => {
                        const li = document.createElement('li');
                        li.innerText = `${res.name} (${res.symbol}) - ${res.exchDisp}`;
                        const btn = document.createElement('button');
                        btn.innerText = '+ Add';
                        btn.className = 'add-btn';
                        btn.style.borderRadius = '4px';
                        btn.onclick = () => {
                            document.getElementById('tickerInput').value = res.symbol;
                            document.getElementById('tickerInput').dataset.name = res.name;
                            addTicker();
                            list.innerHTML = '';
                            input.value = '';
                        };
                        li.appendChild(btn);
                        list.appendChild(li);
                    });
                }
            }
        }

        async function addTicker() {
            const input = document.getElementById('tickerInput');
            const ticker = input.value.trim();
            const name = input.dataset.name || ticker; // fallback to ticker if name not set
            if (ticker) {
                await fetch('/tickers', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ticker: ticker, name: name})
                });
                input.value = '';
                delete input.dataset.name;
                fetchTickers();
            }
        }
        async function deleteTicker(ticker) {
            await fetch(`/tickers/${ticker}`, { method: 'DELETE' });
            fetchTickers();
        }
        
        // Enter key support for search
        document.getElementById("searchInput").addEventListener("keypress", function(event) {
          if (event.key === "Enter") {
            event.preventDefault();
            searchTicker();
          }
        });

        // Enter key support for add
        document.getElementById("tickerInput").addEventListener("keypress", function(event) {
          if (event.key === "Enter") {
            event.preventDefault();
            addTicker();
          }
        });

        fetchTickers();
    </script>
</body>
</html>
"""

@app.get("/")
def get_ui():
    return HTMLResponse(content=html_content)

@app.get("/tickers")
def get_tickers():
    return ticker_manager.get_tickers()

@app.post("/tickers")
async def add_ticker(request: Request, background_tasks: BackgroundTasks):
    data = await request.json()
    ticker = data.get("ticker")
    name = data.get("name", "")
    years = data.get("years", 5)
    if ticker:
        ticker_manager.add_ticker(ticker, name)
        background_tasks.add_task(fetch_and_write_historical, ticker, years)
        return {"status": "success", "ticker": ticker, "name": name, "years": years}
    return {"status": "error"}

@app.delete("/tickers/{ticker}")
def delete_ticker(ticker: str):
    ticker_manager.remove_ticker(ticker)
    return {"status": "success", "ticker": ticker}

@app.get("/search")
def search_ticker(q: str):
    try:
        url = f"https://query2.finance.yahoo.com/v1/finance/search?q={q}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=5)
        data = response.json()
        results = []
        for quote in data.get('quotes', []):
            if 'symbol' in quote and 'shortname' in quote:
                results.append({
                    'symbol': quote['symbol'],
                    'name': quote['shortname'],
                    'exchDisp': quote.get('exchDisp', 'Unknown')
                })
        return {"status": "success", "results": results}
    except Exception as e:
        return {"status": "error", "message": str(e)}

def run_server():
    uvicorn.run(app, host="0.0.0.0", port=28001, log_level="warning")

def main():
    print(f"[{datetime.now()}] Starting stock data collection...")
    print(f"Storage Mode: {config.STORAGE_MODE}")
    
    # Start web server in background
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print("Web UI available at http://localhost:28001")

    storage_backends = get_storage_backend(config)

    if not storage_backends:
        print("Error: No storage backends available. Exiting.")
        return

    while True:
        try:
            current_tickers = ticker_manager.get_ticker_symbols()
            print(f"\n[{datetime.now()}] Fetching for tickers: {current_tickers}")
            fetcher = StockFetcher(current_tickers)
            
            for ticker in fetcher.tickers:
                data = fetcher.fetch_data(ticker)
                
                if data is not None:
                    stored = False
                    for backend in storage_backends:
                        if backend.store(ticker, data):
                            stored = True
                            break
                    
                    if not stored:
                        print(f"Failed to store data for {ticker} in any backend")

            print(f"Waiting {config.FETCH_INTERVAL} seconds until next fetch...")
            time.sleep(config.FETCH_INTERVAL)

        except Exception as e:
            print(f"Error in main loop: {e}")
            print(f"Retrying in {config.FETCH_INTERVAL} seconds...")
            time.sleep(config.FETCH_INTERVAL)

if __name__ == "__main__":
    main()
