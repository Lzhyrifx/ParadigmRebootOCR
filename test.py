import re
from fuzzywuzzy import fuzz  # 需要安装: pip install fuzzywuzzy python-Levenshtein
import requests

def get_all_songs_levels():
    url = "https://api.prp.icel.site/songs/"
    response = requests.get(url)
    response.raise_for_status()
    songs_data = response.json()
    return songs_data


def advanced_fuzzy_match(ocr_title, songs, threshold=70):
    """
    使用多种策略进行模糊匹配
    """
    # 预处理OCR文本
    ocr_clean = re.sub(r'[^\w\s]', '', ocr_title.lower().strip())

    best_match = None
    best_score = 0
    best_method = ""

    for song in songs:
        api_title = song.get('title', '')
        api_clean = re.sub(r'[^\w\s]', '', api_title.lower().strip())

        # 方法1: 简单相似度
        ratio1 = fuzz.ratio(ocr_clean, api_clean)
        # 方法2: 部分匹配（适合OCR缺失部分文字）
        ratio2 = fuzz.partial_ratio(ocr_clean, api_clean)
        # 方法3: 令牌排序匹配（忽略单词顺序）
        ratio3 = fuzz.token_sort_ratio(ocr_clean, api_clean)
        print(ratio1)
        print(ratio2)
        print(ratio3)
        print('\n')
        # 取最高分
        current_score = max(ratio1, ratio2, ratio3)

        if current_score > best_score and current_score >= threshold:
            best_score = current_score
            best_match = song

    return best_match, best_score


# 使用示例
if __name__ == "__main__":
    songs = get_all_songs_levels()
    ocr_results = ["Rocket Lanter", "we're dying", "Libra"]  # OCR可能有错别字或简繁体问题

    for ocr_title in ocr_results:
        matched_song, score = advanced_fuzzy_match(ocr_title, songs)

        if matched_song:
            print(f"✅ OCR: {ocr_title} → 匹配: {matched_song['title']} (置信度: {score}%)")
            print(f"   等级: {matched_song.get('level', 'N/A')}")
        else:
            print(f"❌ 未匹配: {ocr_title}")