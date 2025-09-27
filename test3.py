import os
import json
import cv2
import re
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR
from fuzzywuzzy import fuzz

# 初始化OCR引擎
engine = RapidOCR(
    params={
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Rec.model_type": ModelType.MOBILE,
    }
)


def load_songs_data():
    """加载歌曲数据"""
    try:
        with open('songs_data.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("songs_data.json 文件未找到，请先运行获取歌曲数据的脚本")
        return []


def ocr_region(image_path, region_coords):
    """OCR识别指定区域"""
    img = cv2.imread(image_path)
    x1, y1, x2, y2 = region_coords
    roi = img[y1:y2, x1:x2]
    res = engine(roi, use_cls=False, use_det=False, use_rec=True)
    return res


def distinguish(image_path):
    """识别截图类型"""
    img = cv2.imread(image_path)
    x, y = 27, 1934
    b, g, r = img[y, x]
    return "type2" if (60 <= r <= 66 and 136 <= g <= 142 and 170 <= b <= 176) else "type1"


def get_level(image_path, result_type):
    """获取难度等级"""
    img = cv2.imread(image_path)
    if result_type == "type1":
        x, y = 1590, 441
        b, g, r = img[y, x]
        if 210 <= r <= 225 and 135 <= g <= 150 and 235 <= b <= 255:
            return "Massive"
        elif 225 <= r <= 238 and 108 <= g <= 120 and 105 <= b <= 120:
            return "Invaded"
        else:
            return "Detected"
    elif result_type == "type2":
        x, y = 2982, 1520
        b, g, r = img[y, x]
        if 170 <= r <= 190 and 120 <= g <= 135 and 200 <= b <= 215:
            return "Massive"
        elif 195 <= r <= 210 and 110 <= g <= 120 and 105 <= b <= 120:
            return "Invaded"
        else:
            return "Detected"
    return "Unknown"


def clean_ocr_text(text):
    """清理OCR识别结果"""
    return text.replace('/', '').replace('、', '').replace(',', '').strip()


def method_partial_ratio(ocr_text, items, threshold=70, key=None):
    """部分匹配方法"""
    best_match = None
    best_score = 0

    ocr_clean = re.sub(r'[^\w\s]', '', ocr_text.lower().strip())

    for item in items:
        if key:
            compare_text = item.get(key, '')
        else:
            compare_text = str(item)

        api_clean = re.sub(r'[^\w\s]', '', compare_text.lower().strip())

        ratio = fuzz.partial_ratio(ocr_clean, api_clean)

        if ratio > best_score and ratio >= threshold:
            best_score = ratio
            best_match = item

    return best_match, best_score


def get_artists_by_difficulty(difficulty, songs_data):
    """获取指定难度的所有曲师"""
    artists = list(set([song.get('artist', '') for song in songs_data
                        if song.get('difficulty', '').lower() == difficulty.lower()]))
    return artists


def get_songs_by_artist_and_difficulty(artist, difficulty, songs_data):
    """获取指定曲师在指定难度下的所有歌曲"""
    songs = [song for song in songs_data
             if song.get('artist', '').lower() == artist.lower()
             and song.get('difficulty', '').lower() == difficulty.lower()]
    return songs


def match_difficulty_artist_song(ocr_difficulty, ocr_artist, ocr_song, songs_data,
                                 difficulty_threshold=70, artist_threshold=70, song_threshold=70):
    """按照难度→曲师→歌名的顺序进行匹配"""

    # 第一步：匹配难度
    print(f"\n第一步：匹配难度 '{ocr_difficulty}'")
    all_difficulties = list(set([song.get('difficulty', '') for song in songs_data]))
    matched_difficulty, diff_score = method_partial_ratio(ocr_difficulty, all_difficulties, difficulty_threshold)

    if not matched_difficulty:
        print(f"❌ 未找到匹配的难度")
        return None, None, None, 0

    print(f"✅ 匹配到难度: {matched_difficulty} (相似度: {diff_score}%)")

    # 第二步：在匹配的难度中匹配曲师
    print(f"\n第二步：在难度 '{matched_difficulty}' 中匹配曲师 '{ocr_artist}'")
    difficulty_artists = get_artists_by_difficulty(matched_difficulty, songs_data)
    matched_artist, artist_score = method_partial_ratio(ocr_artist, difficulty_artists, artist_threshold)

    if not matched_artist:
        print(f"❌ 在难度 '{matched_difficulty}' 中未找到匹配的曲师")
        # 尝试在所有曲师中匹配
        all_artists = list(set([song.get('artist', '') for song in songs_data]))
        matched_artist, artist_score = method_partial_ratio(ocr_artist, all_artists, artist_threshold)
        if matched_artist:
            print(f"⚠️  在所有曲师中匹配到: {matched_artist} (相似度: {artist_score}%)")
        else:
            print(f"❌ 完全未找到匹配的曲师")
            return matched_difficulty, None, None, 0

    print(f"✅ 匹配到曲师: {matched_artist} (相似度: {artist_score}%)")

    # 第三步：在匹配的难度和曲师中匹配歌名
    print(f"\n第三步：在难度 '{matched_difficulty}' 和曲师 '{matched_artist}' 中匹配歌名 '{ocr_song}'")
    artist_songs = get_songs_by_artist_and_difficulty(matched_artist, matched_difficulty, songs_data)

    if artist_songs:
        print(f"曲师 '{matched_artist}' 在难度 '{matched_difficulty}' 下有 {len(artist_songs)} 首歌曲:")
        for i, song in enumerate(artist_songs, 1):
            print(f"  {i}. {song.get('title', 'N/A')} (等级: {song.get('level', 'N/A')})")

        matched_song, song_score = method_partial_ratio(ocr_song, artist_songs, song_threshold, key='title')

        if matched_song:
            print(f"✅ 匹配到歌曲: {matched_song.get('title', 'N/A')} (相似度: {song_score}%)")
            total_score = (diff_score + artist_score + song_score) / 3
            return matched_difficulty, matched_artist, matched_song, total_score
        else:
            print(f"❌ 在该曲师的歌曲中未找到匹配的歌名")
    else:
        print(f"❌ 曲师 '{matched_artist}' 在难度 '{matched_difficulty}' 下没有歌曲")

    # 如果在前三步没找到，尝试在曲师的所有歌曲中匹配
    print(f"\n备选方案：在曲师 '{matched_artist}' 的所有歌曲中匹配")
    all_artist_songs = [song for song in songs_data if song.get('artist', '').lower() == matched_artist.lower()]
    if all_artist_songs:
        print(f"曲师 '{matched_artist}' 共有 {len(all_artist_songs)} 首歌曲:")
        for i, song in enumerate(all_artist_songs, 1):
            print(
                f"  {i}. {song.get('title', 'N/A')} - {song.get('difficulty', 'N/A')} (等级: {song.get('level', 'N/A')})")

        matched_song, song_score = method_partial_ratio(ocr_song, all_artist_songs, song_threshold, key='title')
        if matched_song:
            print(
                f"✅ 匹配到歌曲: {matched_song.get('title', 'N/A')} (难度: {matched_song.get('difficulty', 'N/A')}) (相似度: {song_score}%)")
            total_score = (diff_score + artist_score + song_score) / 3
            return matched_difficulty, matched_artist, matched_song, total_score

    print(f"❌ 最终未找到匹配的歌曲")
    return matched_difficulty, matched_artist, None, 0


def process_screenshot(img_path, result_type, songs_data):
    """处理单张截图"""
    # OCR识别各个区域
    if result_type == "type1":
        song_result = ocr_region(img_path, region_song1)
        artist_result = ocr_region(img_path, region_artist1)
        rating_result = ocr_region(img_path, region_rating1)
    else:  # type2
        song_result = ocr_region(img_path, region_song2)
        artist_result = ocr_region(img_path, region_artist2)
        rating_result = ocr_region(img_path, region_rating2)

    # 清理识别结果
    song_name = clean_ocr_text(song_result.txts[0]) if song_result.txts else "Unknown"
    artist = clean_ocr_text(artist_result.txts[0]) if artist_result.txts else "Unknown"
    rating = clean_ocr_text(rating_result.txts[0]) if rating_result.txts else "Unknown"
    level = get_level(img_path, result_type)

    print(f"\n🎯 识别结果:")
    print(f"  歌曲: {song_name}")
    print(f"  曲师: {artist}")
    print(f"  分数: {rating}")
    print(f"  难度: {level}")

    # 按照难度→曲师→歌名的顺序进行匹配
    matched_difficulty, matched_artist, matched_song, total_score = match_difficulty_artist_song(
        level, artist, song_name, songs_data)

    result_data = {
        'filename': os.path.basename(img_path),
        'ocr_results': {
            'song': song_name,
            'artist': artist,
            'rating': rating,
            'level': level
        },
        'match_info': {
            'matched_difficulty': matched_difficulty,
            'matched_artist': matched_artist,
            'total_match_score': total_score
        }
    }

    if matched_song:
        print(f"\n🎉 最终匹配成功 (综合相似度: {total_score:.1f}%):")
        print(f"  📝 歌曲: {matched_song.get('title', 'N/A')}")
        print(f"  👤 曲师: {matched_song.get('artist', 'N/A')}")
        print(f"  ⭐ 等级: {matched_song.get('level', 'N/A')}")
        print(f"  🎯 难度: {matched_song.get('difficulty', 'N/A')}")

        # 添加匹配的歌曲信息
        result_data['matched_song'] = {
            'title': matched_song.get('title', ''),
            'artist': matched_song.get('artist', ''),
            'level': matched_song.get('level', ''),
            'difficulty': matched_song.get('difficulty', ''),
            'score': rating
        }
    else:
        print(f"\n❌ 匹配失败")
        result_data['matched_song'] = None

    print("=" * 70)
    return result_data


def save_results_to_json(results, output_file='songs_results.json'):
    """按照指定格式保存结果到JSON文件"""
    formatted_results = []

    for result in results:
        if result.get('matched_song'):
            song_data = result['matched_song'].copy()
            # 确保level是数值类型
            try:
                song_data['level'] = float(song_data['level'])
            except (ValueError, TypeError):
                song_data['level'] = 0.0

            formatted_results.append(song_data)

    # 按歌曲名和艺术家分组，合并不同难度的记录
    final_output = []
    seen_combinations = set()

    for song in formatted_results:
        # 创建唯一标识符（歌曲+艺术家+难度）
        combo_key = f"{song['title']}|{song['artist']}|{song['difficulty']}"

        if combo_key not in seen_combinations:
            seen_combinations.add(combo_key)
            final_output.append({
                "title": song['title'],
                "artist": song['artist'],
                "difficulty": song['difficulty'],
                "level": song['level'],
                "score": song['score']
            })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"\n💾 结果已保存到 {output_file}")
    print(f"📊 共保存 {len(final_output)} 条记录")

    # 显示统计信息
    if final_output:
        artists = set([song['artist'] for song in final_output])
        songs = set([song['title'] for song in final_output])
        difficulties = set([song['difficulty'] for song in final_output])
        print(f"🎵 涉及 {len(artists)} 位曲师，{len(songs)} 首歌曲，{len(difficulties)} 种难度")


# 区域坐标定义
region_rating1 = (559, 1180, 1319, 1323)
region_song1 = (935, 266, 2272, 346)
region_artist1 = (1000, 351, 2200, 425)

region_song2 = (1603, 454, 3016, 535)
region_artist2 = (1681, 555, 3018, 624)
region_rating2 = (1946, 1485, 2420, 1596)


def main():
    # 检查是否安装了fuzzywuzzy
    try:
        from fuzzywuzzy import fuzz
    except ImportError:
        print("请先安装fuzzywuzzy: pip install fuzzywuzzy python-Levenshtein")
        return

    # 加载歌曲数据
    songs_data = load_songs_data()
    if not songs_data:
        return

    src_folder = "SCR"
    results = []

    # 处理所有截图
    for filename in os.listdir(src_folder):
        if filename.upper().endswith('.JPG'):
            img_path = os.path.join(src_folder, filename)
            print(f"\n{'=' * 80}")
            print(f"📁 处理文件: {filename}")
            print(f"{'=' * 80}")

            result_type = distinguish(img_path)
            result_data = process_screenshot(img_path, result_type, songs_data)
            results.append(result_data)

    # 保存结果
    save_results_to_json(results)


if __name__ == "__main__":
    main()