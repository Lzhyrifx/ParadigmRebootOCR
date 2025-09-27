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


def method_partial_ratio(ocr_title, songs, threshold=70):
    """方法2: 部分匹配"""
    best_match = None
    best_score = 0

    ocr_clean = re.sub(r'[^\w\s]', '', ocr_title.lower().strip())

    for song in songs:
        api_title = song.get('title', '')
        api_clean = re.sub(r'[^\w\s]', '', api_title.lower().strip())

        ratio = fuzz.partial_ratio(ocr_clean, api_clean)

        if ratio > best_score and ratio >= threshold:
            best_score = ratio
            best_match = song

    return best_match, best_score


def find_matching_song(song_name, artist, level, songs_data):
    """使用部分匹配方法查找匹配的歌曲"""
    # 首先尝试匹配当前难度的歌曲
    same_level_songs = [song for song in songs_data if song.get('difficulty', '').lower() == level.lower()]

    if same_level_songs:
        match, score = method_partial_ratio(song_name, same_level_songs)
        if match:
            return match, score, 'same_level'

    # 如果同难度没找到，尝试所有歌曲
    all_songs_match, all_songs_score = method_partial_ratio(song_name, songs_data)

    if all_songs_match:
        return all_songs_match, all_songs_score, 'all_songs'

    return None, 0, 'no_match'


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

    print(f"识别结果:")
    print(f"  歌曲: {song_name}")
    print(f"  曲师: {artist}")
    print(f"  分数: {rating}")
    print(f"  难度: {level}")

    # 查找匹配的歌曲
    match, score, match_type = find_matching_song(song_name, artist, level, songs_data)

    result_data = {
        'filename': os.path.basename(img_path),
        'ocr_results': {
            'song': song_name,
            'artist': artist,
            'rating': rating,
            'level': level
        },
        'match_info': {
            'match_score': score,
            'match_type': match_type
        }
    }

    if match:
        print(f"匹配成功 (相似度: {score}%, 类型: {match_type}):")
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
        print("未找到匹配的歌曲")
        result_data['matched_song'] = None

    print("-" * 50)
    return result_data


def save_results_to_json(results, output_file='songs_results.json'):
    """按照指定格式保存结果到JSON文件"""
    # 按照您指定的格式组织数据
    formatted_results = []

    for result in results:
        if result['matched_song']:
            song_data = result['matched_song'].copy()
            # 确保level是数值类型
            try:
                song_data['level'] = float(song_data['level'])
            except (ValueError, TypeError):
                song_data['level'] = 0.0

            formatted_results.append(song_data)

    # 按歌曲名和艺术家分组，合并不同难度的记录
    final_output = []
    seen_songs = set()

    for song in formatted_results:
        # 创建唯一标识符
        song_key = f"{song['title']}|{song['artist']}"

        if song_key not in seen_songs:
            seen_songs.add(song_key)
            # 查找这首歌的所有难度记录
            same_song_records = [s for s in formatted_results
                                 if s['title'] == song['title'] and s['artist'] == song['artist']]

            # 为每个难度创建单独的记录
            for record in same_song_records:
                final_output.append({
                    "title": record['title'],
                    "artist": record['artist'],
                    "difficulty": record['difficulty'],
                    "level": record['level'],
                    "score": record['score']
                })

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_output, f, indent=2, ensure_ascii=False)

    print(f"结果已保存到 {output_file}")
    print(f"共保存 {len(final_output)} 条记录")


# 区域坐标定义
region_rating1 = (559, 1180, 1319, 1323)
region_song1 = (935, 266, 2272, 346)
region_artist1 = (1000, 351, 2200, 425)

region_song2 = (1603, 454, 3016, 535)
region_artist2 = (1681, 555, 3018, 624)
region_rating2 = (1946, 1485, 2420, 1596)


def main():

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