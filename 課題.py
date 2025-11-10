import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
import json # 辞書を見やすく表示するためにjsonモジュールを追加

# --- 設定 ---
# 武蔵野大学のトップページURLを設定
START_URL = "https://www.musashino-u.ac.jp/"

# 収集対象とするドメインを設定
DOMAIN = urlparse(START_URL).netloc

# 収集済みのURLを格納するセット（重複防止用）
visited_urls = set()

# 結果を格納する辞書型変数
page_data = {}
# ---

def get_page_info(url):
    """
    指定されたURLからHTMLを取得し、<title>と同一ドメイン内のリンクを抽出する
    """
    # URLにクエリやフラグメントがある場合は除去し、正規化
    parsed_url = urlparse(url)
    clean_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
    
    if clean_url in visited_urls:
        return []
    
    # 既に訪問済みとして登録
    visited_urls.add(clean_url)
    
    # URLにアクセス
    try:
        # サーバーに負荷をかけすぎないよう、適度に遅延を入れる
        time.sleep(0.5) 
        
        # タイムアウトを設定
        response = requests.get(clean_url, timeout=10)
        
        # 成功ステータス (200) 以外はスキップ
        if response.status_code != 200:
            print(f"Skipping {clean_url} due to status code {response.status_code}")
            return []
            
        # HTMLコンテンツをBeautifulSoupで解析
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. <title>を取得
        title_tag = soup.find('title')
        title_text = title_tag.text.strip() if title_tag else "No Title Found"
        
        # 辞書型変数に格納
        page_data[clean_url] = title_text
        print(f"Collected: URL: {clean_url}, Title: {title_text}")
        
        # 2. 同一ドメインの全てのリンクを抽出
        links = []
        for a_tag in soup.find_all('a', href=True):
            href = a_tag.get('href')
            # 絶対URLに変換 (相対URLも処理するため)
            absolute_url = urljoin(clean_url, href)
            
            # クエリパラメータやフラグメントを除去し、正規化
            parsed_link = urlparse(absolute_url)
            clean_link = parsed_link.scheme + "://" + parsed_link.netloc + parsed_link.path
            
            # ドメインが一致し、まだ訪問していないURLのみをリストに追加
            if parsed_link.netloc == DOMAIN and clean_link not in visited_urls:
                links.append(clean_link)

        return links
        
    except requests.exceptions.RequestException as e:
        # アクセスエラー（タイムアウト、接続拒否など）が発生した場合
        print(f"Error accessing {clean_url}: {e}")
        return []


def crawl(start_url):
    """
    同一ドメイン内のリンクを再帰的に辿るメイン関数 (幅優先探索)
    """
    # 待機中のURLリスト (キューとして使用)
    queue = [start_url]
    
    # キューが空になるまでループ
    while queue:
        current_url = queue.pop(0) # キューの先頭からURLを取り出す
        
        # ページの情報を取得し、新しいリンク（同一ドメイン内かつ未訪問）を取得
        new_links = get_page_info(current_url)
        
        # 新しいリンクをキューに追加
        for link in new_links:
            if link not in visited_urls and link not in queue:
                queue.append(link)

# --- 実行 ---
print(f"Starting crawl on: {START_URL}")
crawl(START_URL)

# 辞書型変数を print() で表示する (見やすくするためにjson.dumpsを使用)
print("\n" + "="*50)
print("✅ 収集結果の辞書型変数 (URL: <title>の内容)")
print("="*50)
# print() 関数で表示
print(json.dumps(page_data, indent=4, ensure_ascii=False))
# ---