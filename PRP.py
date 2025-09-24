import requests
import json


def get_all_songs_levels():
    url = "https://api.prp.icel.site/songs/"
    response = requests.get(url)
    response.raise_for_status()
    songs_data = response.json()
    return songs_data

if __name__ == "__main__":
    songs = get_all_songs_levels()

    if songs:
        for i, song in enumerate(songs[:30]):
            print(f"  标题: {song.get('title', 'N/A')}")
            print(f"  等级: {song.get('level', 'N/A')}")
            print(f"  难度: {song.get('difficulty', 'N/A')}")
    with open('songs_data.json', 'w', encoding='utf-8') as f:
        json.dump(songs, f, indent=2, ensure_ascii=False)