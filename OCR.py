import os
from rapidocr import EngineType, ModelType, OCRVersion, RapidOCR
import cv2


engine = RapidOCR(
    params={
        "Rec.ocr_version": OCRVersion.PPOCRV5,
        "Rec.engine_type": EngineType.ONNXRUNTIME,
        "Rec.model_type": ModelType.MOBILE,
    }
)


def ocr_region(image_path, region_coords):
    img = cv2.imread(image_path)
    x1, y1, x2, y2 = region_coords
    roi = img[y1:y2, x1:x2]
    res = engine(roi, use_cls=False, use_det=False, use_rec=True)
    return res


def distinguish(image_path):
    img = cv2.imread(image_path)
    x, y = 27, 1934
    b, g, r = img[y, x]
    return "type2" if (60 <= r <= 66 and 136 <= g <= 142 and 170 <= b <= 176) else "type1"

def level(image_path):
    img = cv2.imread(image_path)
    if result == "type1":
        x, y = 1590, 441
        b, g, r = img[y, x]
        if 210 <= r <= 225 and 135 <= g <= 150 and 235 <= b <= 255:
            print("Massive")
        else:
            pass
    if result == "type2":
        x, y = 2687, 1780
        b, g, r = img[y, x]
        print(r,g,b)
        if 245 <= r <= 255 and 245 <= g <= 255 and 245 <= b <= 255:
            print("Massive")
        else:
            pass


def region_ocr(path, region):
    re = ocr_region(path, region)
    text = re.txts[0]
    retext = text.replace('/', '').replace('、', '').replace(',', '').replace('\\', '')
    print(retext)
    return re

region_rating1 = (559, 1180, 1319, 1323)
region_song1 = (935, 266, 2272, 346)
region_artist1 = (1000,351,2200,425)

region_song2 = (1603,454,3016,535)
region_artist2 = (1681,555,3018,624)
region_rating2 = (1946, 1485, 2420, 1596)
src_folder = "SCR"

for filename in os.listdir(src_folder):
    if filename.upper().endswith('.JPG'):
        img_path = os.path.join(src_folder, filename)
        result = distinguish(img_path)

        if result == "type1":
            result_song = region_ocr(img_path, region_song1)
            result_artist = region_ocr(img_path, region_artist1)
            result_rating = region_ocr(img_path, region_rating1)
            level(img_path)
            song_name = os.path.splitext(filename)[0]
            result_song.vis("Result/" + song_name + ".jpg")
            result_artist.vis("Result/" + song_name + "ART.jpg")
            result_rating.vis("Result/" + song_name + "RAT.jpg")
        elif result == "type2":
            result_song = region_ocr(img_path, region_song2)
            result_artist = region_ocr(img_path, region_artist2)
            result_rating = region_ocr(img_path, region_rating2)
            level(img_path)
            song_name = os.path.splitext(filename)[0]
            result_song.vis("Result/" + song_name + ".jpg")
            result_artist.vis("Result/" + song_name + "ART.jpg")
            result_rating.vis("Result/" + song_name + "XXX.jpg")
        else:
            pass
