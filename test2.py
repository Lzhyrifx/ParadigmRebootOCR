import requests
import time
import re
from difflib import SequenceMatcher
from fuzzywuzzy import fuzz
import random


def get_all_songs_levels():
    url = "https://api.prp.icel.site/songs/"
    response = requests.get(url)
    response.raise_for_status()
    songs_data = response.json()
    return songs_data


def method1_difflib(ocr_title, songs, threshold=0.6):
    """方法1: 使用difflib的SequenceMatcher"""
    best_match = None
    best_score = 0

    for song in songs:
        api_title = song.get('title', '')
        similarity = SequenceMatcher(None, ocr_title.lower(), api_title.lower()).ratio()

        if similarity > best_score and similarity >= threshold:
            best_score = similarity
            best_match = song

    return best_match, best_score


def method2_fuzzywuzzy_simple(ocr_title, songs, threshold=70):
    """方法2: 使用fuzzywuzzy的简单比率"""
    best_match = None
    best_score = 0

    ocr_clean = re.sub(r'[^\w\s]', '', ocr_title.lower().strip())

    for song in songs:
        api_title = song.get('title', '')
        api_clean = re.sub(r'[^\w\s]', '', api_title.lower().strip())

        ratio = fuzz.ratio(ocr_clean, api_clean)

        if ratio > best_score and ratio >= threshold:
            best_score = ratio
            best_match = song

    return best_match, best_score


def method3_fuzzywuzzy_advanced(ocr_title, songs, threshold=70):
    """方法3: 使用fuzzywuzzy的多种策略组合"""
    best_match = None
    best_score = 0

    ocr_clean = re.sub(r'[^\w\s]', '', ocr_title.lower().strip())

    for song in songs:
        api_title = song.get('title', '')
        api_clean = re.sub(r'[^\w\s]', '', api_title.lower().strip())

        ratio1 = fuzz.ratio(ocr_clean, api_clean)
        ratio2 = fuzz.partial_ratio(ocr_clean, api_clean)
        ratio3 = fuzz.token_sort_ratio(ocr_clean, api_clean)

        current_score = max(ratio1, ratio2, ratio3)

        if current_score > best_score and current_score >= threshold:
            best_score = current_score
            best_match = song

    return best_match, best_score


def performance_test(methods, test_cases, songs, iterations=100):
    """性能测试函数"""
    results = {}

    for method_name, method_func in methods.items():
        print(f"正在测试 {method_name}...")
        total_time = 0
        successful_matches = 0

        # 预热（避免第一次运行的冷启动影响）
        for _ in range(10):
            method_func(test_cases[0], songs)

        # 正式测试
        start_time = time.time()

        for _ in range(iterations):
            for ocr_title in test_cases:
                match_result, score = method_func(ocr_title, songs)
                if match_result:
                    successful_matches += 1

        end_time = time.time()
        total_time = end_time - start_time

        # 计算统计数据
        avg_time_per_match = total_time / (len(test_cases) * iterations) * 1000  # 毫秒
        matches_per_second = (len(test_cases) * iterations) / total_time

        results[method_name] = {
            'total_time': total_time,
            'avg_time_per_match': avg_time_per_match,
            'matches_per_second': matches_per_second,
            'success_rate': successful_matches / (len(test_cases) * iterations) * 100
        }

    return results


def print_results(results):
    """打印测试结果"""
    print("\n" + "=" * 60)
    print("性能测试结果对比")
    print("=" * 60)

    # 按速度排序
    sorted_results = sorted(results.items(), key=lambda x: x[1]['avg_time_per_match'])

    for i, (method_name, data) in enumerate(sorted_results, 1):
        print(f"\n{i}. {method_name}:")
        print(f"   总时间: {data['total_time']:.3f}秒")
        print(f"   单次匹配平均时间: {data['avg_time_per_match']:.3f}毫秒")
        print(f"   匹配速度: {data['matches_per_second']:.1f} 次/秒")
        print(f"   匹配成功率: {data['success_rate']:.1f}%")


def accuracy_test(methods, test_cases, expected_matches, songs):
    """准确性测试"""
    print("\n" + "=" * 60)
    print("准确性测试")
    print("=" * 60)

    accuracy_results = {}

    for method_name, method_func in methods.items():
        correct_matches = 0

        for ocr_title, expected_title in zip(test_cases, expected_matches):
            match_result, score = method_func(ocr_title, songs)
            if match_result and match_result.get('title') == expected_title:
                correct_matches += 1
            elif match_result:
                print(f"{method_name}: '{ocr_title}' → '{match_result.get('title')}' (期望: '{expected_title}')")

        accuracy = correct_matches / len(test_cases) * 100
        accuracy_results[method_name] = accuracy
        print(f"{method_name}: 准确率 {accuracy:.1f}% ({correct_matches}/{len(test_cases)})")


if __name__ == "__main__":
    # 获取歌曲数据
    print("正在获取歌曲数据...")
    songs = get_all_songs_levels()
    print(f"获取到 {len(songs)} 首歌曲")

    # 测试用例（模拟OCR可能出现的各种情况）
    test_cases = [
        "鸟之诗",  # 完全正确
        "鳥之詩",  # 繁体字
        "鸟之",  # 不完整
        "千本樱",  # 正确
        "千本桜",  # 日文汉字
        "千本",  # 不完整
        "恋爱循环",  # 正确
        "戀愛循環",  # 繁体
        "恋爱",  # 不完整
        "罗密欧与灰姑娘",  # 长歌名
        "罗密欧",  # 部分
        "God knows",  # 英文
        "god know",  # 英文错误
    ]

    # 期望的正确匹配结果
    expected_matches = [
        "鸟之诗", "鸟之诗", "鸟之诗",
        "千本樱", "千本樱", "千本樱",
        "恋爱循环", "恋爱循环", "恋爱循环",
        "罗密欧与灰姑娘", "罗密欧与灰姑娘",
        "God knows", "God knows"
    ]

    # 定义要测试的方法
    methods = {
        "difflib(SequenceMatcher)": method1_difflib,
        "fuzzywuzzy(简单比率)": method2_fuzzywuzzy_simple,
        "fuzzywuzzy(多策略)": method3_fuzzywuzzy_advanced
    }

    # 运行性能测试
    print("开始性能测试...")
    results = performance_test(methods, test_cases, songs, iterations=50)

    # 打印性能结果
    print_results(results)

    # 运行准确性测试
    accuracy_test(methods, test_cases, expected_matches, songs)

    # 推荐建议
    print("\n" + "=" * 60)
    print("推荐建议")
    print("=" * 60)

    fastest_method = min(results.items(), key=lambda x: x[1]['avg_time_per_match'])
    best_accuracy = max([(name, results[name]['success_rate']) for name in results],
                        key=lambda x: x[1])

    print(f"最快的方​法: {fastest_method[0]} ({fastest_method[1]['avg_time_per_match']:.3f}毫秒/次)")
    print(f"成功率最高的方法: {best_accuracy[0]} ({best_accuracy[1]:.1f}%)")

    if "fuzzywuzzy(简单比率)" in results and "difflib(SequenceMatcher)" in results:
        speed_ratio = results["difflib(SequenceMatcher)"]['avg_time_per_match'] / results["fuzzywuzzy(简单比率)"][
            'avg_time_per_match']
        print(f"fuzzywuzzy(简单比率) 比 difflib 快 {speed_ratio:.1f} 倍")