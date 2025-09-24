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


def colors(image_path):
    img = cv2.imread(image_path)
    x, y = 27, 1934
    b, g, r = img[y, x]
    return "type2" if (60 <= r <= 66 and 136 <= g <= 142 and 170 <= b <= 176) else "type1"


region_rating1 = (559, 1180, 1319, 1323)
region_song1 = (1190, 272, 2056, 352)
region_rating2 = (1946, 1485, 2420, 1596)
region_song2 = (1985, 448, 3022, 539)
src_folder = "SCR"

for filename in os.listdir(src_folder):
    if filename.upper().endswith('.JPG'):
        img_path = os.path.join(src_folder, filename)

        result = colors(img_path)
        if result == "type1":
            result_rating = ocr_region(img_path, region_rating1)
            result_song = ocr_region(img_path, region_song1)
            print(result_rating.txts)
            print(result_song.txts)
            song_name = os.path.splitext(filename)[0]
            result_song.vis("Result/" + song_name + ".jpg")
            result_rating.vis("Result/" + song_name + "XXX.jpg")
        elif result == "type2":
            result_rating = ocr_region(img_path, region_rating2)
            result_song = ocr_region(img_path, region_song2)
            print(result_rating.txts)
            print(result_song.txts)
            song_name = os.path.splitext(filename)[0]
            result_song.vis("RE/" + song_name + ".jpg")
            result_rating.vis("RE/" + song_name + "XXX.jpg")
        else:
            pass
