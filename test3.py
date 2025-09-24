import re
import time
from fuzzywuzzy import fuzz
import requests


def get_all_songs_levels():
    url = "https://api.prp.icel.site/songs/"
    response = requests.get(url)
    response.raise_for_status()
    songs_data = response.json()
    return songs_data


def method_ratio(ocr_title, songs, threshold=70):
    """方法1: 简单相似度"""
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


def method_token_sort_ratio(ocr_title, songs, threshold=70):
    """方法3: 令牌排序匹配"""
    best_match = None
    best_score = 0

    ocr_clean = re.sub(r'[^\w\s]', '', ocr_title.lower().strip())

    for song in songs:
        api_title = song.get('title', '')
        api_clean = re.sub(r'[^\w\s]', '', api_title.lower().strip())

        ratio = fuzz.token_sort_ratio(ocr_clean, api_clean)

        if ratio > best_score and ratio >= threshold:
            best_score = ratio
            best_match = song

    return best_match, best_score


def speed_test():
    """速度测试函数"""
    print("正在获取歌曲数据...")
    songs = get_all_songs_levels()
    print(f"获取到 {len(songs)} 首歌曲")

    # 测试用例
    ocr_results = ["Rocket Lanter", "we're dying", "Libra"]

    # 定义三种方法
    methods = {
        "ratio(简单相似度)": method_ratio,
        "partial_ratio(部分匹配)": method_partial_ratio,
        "token_sort_ratio(令牌排序)": method_token_sort_ratio
    }

    # 预热（避免冷启动影响）
    print("预热中...")
    for method_name, method_func in methods.items():
        for ocr_title in ocr_results:
            method_func(ocr_title, songs)

    # 正式测试
    test_results = {}
    iterations = 1000  # 测试次数，增加以获得更准确的结果

    for method_name, method_func in methods.items():
        print(f"\n正在测试 {method_name}...")

        total_time = 0
        start_time = time.time()

        # 多次测试取平均值
        for i in range(iterations):
            for ocr_title in ocr_results:
                match_result, score = method_func(ocr_title, songs)

        end_time = time.time()
        total_time = end_time - start_time

        # 计算统计数据
        total_operations = len(ocr_results) * iterations
        avg_time_per_operation = (total_time / total_operations) * 1_000_000  # 微秒
        operations_per_second = total_operations / total_time

        test_results[method_name] = {
            'total_time': total_time,
            'avg_time_microseconds': avg_time_per_operation,
            'operations_per_second': operations_per_second,
            'total_operations': total_operations
        }

    # 打印结果
    print("\n" + "=" * 70)
    print("三种匹配方法速度测试结果")
    print("=" * 70)

    # 按速度排序（从快到慢）
    sorted_results = sorted(test_results.items(), key=lambda x: x[1]['avg_time_microseconds'])

    for i, (method_name, data) in enumerate(sorted_results, 1):
        print(f"\n{i}. {method_name}:")
        print(f"   📊 总测试次数: {data['total_operations']} 次匹配操作")
        print(f"   ⏱️ 总耗时: {data['total_time']:.3f} 秒")
        print(f"   🚀 单次匹配平均时间: {data['avg_time_microseconds']:.2f} 微秒")
        print(f"   💨 匹配速度: {data['operations_per_second']:,.0f} 次/秒")

    # 性能对比
    print("\n" + "=" * 70)
    print("性能对比分析")
    print("=" * 70)

    fastest = sorted_results[0]
    slowest = sorted_results[-1]

    speed_ratio = slowest[1]['avg_time_microseconds'] / fastest[1]['avg_time_microseconds']

    print(f"最快方法: {fastest[0]}")
    print(f"最慢方法: {slowest[0]}")
    print(f"速度差异: {speed_ratio:.1f} 倍")

    # 详细对比
    print(f"\n详细对比:")
    for i in range(len(sorted_results)):
        for j in range(i + 1, len(sorted_results)):
            method1, data1 = sorted_results[i]
            method2, data2 = sorted_results[j]
            ratio = data2['avg_time_microseconds'] / data1['avg_time_microseconds']
            print(f"  {method1} 比 {method2} 快 {ratio:.1f} 倍")


def accuracy_comparison():
    """准确性对比（可选）"""
    print("\n" + "=" * 70)
    print("准确性对比（使用你的测试用例）")
    print("=" * 70)

    songs = get_all_songs_levels()
    ocr_results = ["Rocket Lanter", "we're dying", "00.","soar","wolve stan towa en"]

    methods = {
        "ratio": method_ratio,
        "partial_ratio": method_partial_ratio,
        "token_sort_ratio": method_token_sort_ratio
    }

    for ocr_title in ocr_results:
        print(f"\nOCR识别: '{ocr_title}'")
        print("-" * 40)

        for method_name, method_func in methods.items():
            match_result, score = method_func(ocr_title, songs)
            if match_result:
                print(f"  {method_name:15} → {match_result['title']:20} (置信度: {score}%)")
            else:
                print(f"  {method_name:15} → 未匹配")


if __name__ == "__main__":
    # 运行速度测试
    speed_test()

    # 运行准确性对比
    accuracy_comparison()