from flask import Flask, request, jsonify, send_file
import requests
from bs4 import BeautifulSoup
import time
import random
from duckduckgo_search import DDGS

app = Flask(__name__)

# User-Agent to avoid being blocked quickly
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

@app.route('/')
def index():
    return send_file('crawlingnich-neobrutalism.html')

@app.route('/api/crawl', methods=['POST'])
def crawl():
    data = request.json
    keywords = data.get('keywords', [])
    
    if not keywords:
        return jsonify([])

    query = " ".join(keywords)
    results = []
    
    # 1. DuckDuckGo Agent
    try:
        with DDGS() as ddgs:
            ddg_results = list(ddgs.text(query, max_results=10))
            for item in ddg_results:
                title = item.get("title", "")
                snippet = item.get("body", "")
                link = item.get("href", "")
                
                seed = str(hash(title))[-5:]
                item_type = random.choice(['berita', 'jurnal', 'video'])
                
                results.append({
                    "type": item_type,
                    "seed": seed,
                    "title": title,
                    "source": "DuckDuckGo",
                    "date": time.strftime("%d %b %Y"),
                    "snippet": snippet,
                    "content": snippet + " (Buka tautan asli untuk membaca selengkapnya).",
                    "url": link
                })
    except Exception as e:
        print(f"Error fetching from DuckDuckGo: {e}")

    # 2. Wikipedia (sebagai pelengkap)
    try:
        url = "https://id.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "utf8": "1",
            "format": "json",
            "srlimit": 5
        }
        response = requests.get(url, params=params, headers=HEADERS, timeout=10)
        data = response.json()
        search_results = data.get("query", {}).get("search", [])
        
        for item in search_results:
            title = item.get("title", "")
            snippet_html = item.get("snippet", "")
            snippet = BeautifulSoup(snippet_html, "html.parser").text
            page_id = item.get("pageid")
            link = f"https://id.wikipedia.org/?curid={page_id}"
            
            seed = str(hash(title))[-5:]
            item_type = random.choice(['berita', 'jurnal', 'video'])
            
            results.append({
                "type": item_type,
                "seed": seed,
                "title": title,
                "source": "Wikipedia",
                "date": time.strftime("%d %b %Y"),
                "snippet": snippet,
                "content": snippet + " (Buka tautan asli untuk membaca selengkapnya).",
                "url": link
            })
    except Exception as e:
        print(f"Error fetching from Wikipedia: {e}")

    # 3. Yandex Scraper Agent (Basic)
    try:
        yandex_url = f"https://yandex.com/search/?text={query}"
        response = requests.get(yandex_url, headers=HEADERS, timeout=5)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        for li in soup.find_all('li', class_='serp-item')[:5]:
            title_el = li.find('h2')
            if not title_el: continue
            title = title_el.text
            link_el = title_el.find('a')
            link = link_el['href'] if link_el else ""
            
            snippet_el = li.find('div', class_='TextContainer')
            snippet = snippet_el.text if snippet_el else "Hasil penelusuran dari Yandex."
            
            if title and link:
                seed = str(hash(title))[-5:]
                results.append({
                    "type": random.choice(['berita', 'jurnal', 'video']),
                    "seed": seed,
                    "title": title,
                    "source": "Yandex",
                    "date": time.strftime("%d %b %Y"),
                    "snippet": snippet[:150] + "...",
                    "content": snippet + " (Diperoleh melalui agen Yandex).",
                    "url": link
                })
    except Exception as e:
        print(f"Error fetching from Yandex: {e}")

    # Acak agar hasilnya bercampur natural dari ketiga engine
    random.shuffle(results)
    
    # Kembalikan maksimal 20 hasil terbaik
    return jsonify(results[:20])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
