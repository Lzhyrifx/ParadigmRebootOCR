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


def find_artist_songs(ocr_artist, songs_data, artist_threshold=70):
    """先匹配曲师，返回该曲师的所有歌曲"""
    # 获取所有唯一的曲师
    all_artists = list(set([song.get('artist', '') for song in songs_data]))

    # 匹配曲师
    matched_artist, artist_score = method_partial_ratio(ocr_artist, all_artists, artist_threshold)

    if matched_artist:
        print(f"匹配到曲师: {matched_artist} (相似度: {artist_score}%)")

        # 获取该曲师的所有歌曲
        artist_songs = [song for song in songs_data if song.get('artist', '') == matched_artist]
        print(f"该曲师有以下歌曲 ({len(artist_songs)} 首):")
        for i, song in enumerate(artist_songs, 1):
            print(
                f"  {i}. {song.get('title', 'N/A')} - {song.get('difficulty', 'N/A')} (等级: {song.get('level', 'N/A')})")

        return matched_artist, artist_songs
    else:
        print(f"未找到匹配的曲师: {ocr_artist}")
        return None, []


def find_song_in_artist_songs(ocr_song, artist_songs, level, song_threshold=70):
    """在曲师的歌曲中匹配歌名"""
    if not artist_songs:
        return None, 0

    # 首先尝试匹配同难度的歌曲
    same_level_songs = [song for song in artist_songs if song.get('difficulty', '').lower() == level.lower()]

    if same_level_songs:
        match, score = method_partial_ratio(ocr_song, same_level_songs, song_threshold, key='title')
        if match:
            print(f"在同难度歌曲中匹配成功 (相似度: {score}%)")
            return match, score

    # 如果同难度没找到，尝试所有该曲师的歌曲
    match, score = method_partial_ratio(ocr_song, artist_songs, song_threshold, key='title')
    if match:
        print(f"在曲师所有歌曲中匹配成功 (相似度: {score}%)")
        return match, score

    return None, 0


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

    print(f"\n识别结果:")
    print(f"  歌曲: {song_name}")
    print(f"  曲师: {artist}")
    print(f"  分数: {rating}")
    print(f"  难度: {level}")

    # 第一步：匹配曲师
    matched_artist, artist_songs = find_artist_songs(artist, songs_data)

    result_data = {
        'filename': os.path.basename(img_path),
        'ocr_results': {
            'song': song_name,
            'artist': artist,
            'rating': rating,
            'level': level
        },
        'match_info': {
            'matched_artist': matched_artist,
            'artist_song_count': len(artist_songs) if matched_artist else 0
        }
    }

    # 第二步：在曲师的歌曲中匹配歌名
    if matched_artist and artist_songs:
        match, score = find_song_in_artist_songs(song_name, artist_songs, level)

        result_data['match_info']['song_match_score'] = score
        result_data['match_info']['song_match_type'] = 'artist_songs'

        if match:
            print(f"最终匹配成功 (总相似度: {score}%):")
            print(f"  歌曲: {match.get('title', 'N/A')}")
            print(f"  曲师: {match.get('artist', 'N/A')}")
            print(f"  等级: {match.get('level', 'N/A')}")
            print(f"  难度: {match.get('difficulty', 'N/A')}")

            # 添加匹配的歌曲信息
            result_data['matched_song'] = {
                'title': match.get('title', ''),
                'artist': match.get('artist', ''),
                'level': match.get('level', ''),
                'difficulty': match.get('difficulty', ''),
                'score': rating
            }
        else:
            print("在该曲师的歌曲中未找到匹配的歌名")
            result_data['matched_song'] = None
    else:
        print("无法进行歌曲匹配：未找到匹配的曲师")
        result_data['matched_song'] = None
        result_data['match_info']['song_match_score'] = 0
        result_data['match_info']['song_match_type'] = 'no_artist'

    print("-" * 60)
    return result_data


def save_results_to_json(results, output_file='songs_results.json'):
    """按照指定格式保存结果到JSON文件"""
    # 按照您指定的格式组织数据
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

    print(f"\n结果已保存到 {output_file}")
    print(f"共保存 {len(final_output)} 条记录")

    # 显示统计信息
    if final_output:
        artists = set([song['artist'] for song in final_output])
        songs = set([song['title'] for song in final_output])
        print(f"涉及 {len(artists)} 位曲师，{len(songs)} 首歌曲")


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
            print(f"处理文件: {filename}")

            result_type = distinguish(img_path)
            result_data = process_screenshot(img_path, result_type, songs_data)
            results.append(result_data)

    # 保存结果
    save_results_to_json(results)


if __name__ == "__main__":
    main()