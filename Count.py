import cv2


def get_coordinates(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # 将缩放后的坐标转换回原图坐标
        scale_factor = param['scale_factor']
        orig_x = int(x / scale_factor)
        orig_y = int(y / scale_factor)

        # 获取颜色信息
        if 0 <= orig_x < param['orig_width'] and 0 <= orig_y < param['orig_height']:
            # 从原图获取颜色
            pixel_color = param['original_image'][orig_y, orig_x]
            b, g, r = pixel_color

            print(f"显示窗口坐标: ({x}, {y})")
            print(f"原图实际坐标: ({orig_x}, {orig_y})")
            print(f"RGB颜色: ({r}, {g}, {b})")
            print(f"BGR颜色: ({b}, {g}, {r})")
            print("-" * 30)

            param['points'].append((orig_x, orig_y))

            # 在显示图片上标记点
            cv2.circle(param['display_img'], (x, y), 5, (0, 0, 255), -1)

            # 添加坐标和颜色文本
            text = f"({orig_x},{orig_y}) RGB:({r},{g},{b})"
            cv2.putText(param['display_img'], text, (x + 10, y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

            cv2.imshow('Image', param['display_img'])

            if len(param['points']) >= 2:
                print(f"\n已选择 {len(param['points'])} 个点")
                if len(param['points']) == 4:
                    print("已获取4个点坐标：")
                    for i, (px, py) in enumerate(param['points']):
                        # 获取每个点的颜色
                        point_color = param['original_image'][py, px]
                        b, g, r = point_color
                        print(f"点{i + 1}: ({px}, {py}) - RGB:({r}, {g}, {b})")


image_path = 'SCR/jdld6.jpg'
original_image = cv2.imread(image_path)

if original_image is None:
    print("错误：无法读取图片，请检查文件路径")
    exit()

# 获取原图尺寸
img_height, img_width = original_image.shape[:2]
print(f"原图尺寸: {img_width} x {img_height}")

# 获取屏幕尺寸（估算）
screen_width = 1920  # 可以根据您的屏幕调整
screen_height = 1080

# 计算缩放比例以适应屏幕
scale_factor = min(screen_width / img_width, screen_height / img_height, 1.0)
new_width = int(img_width * scale_factor)
new_height = int(img_height * scale_factor)

# 调整图片大小用于显示
display_img = cv2.resize(original_image, (new_width, new_height))
print(f"显示尺寸: {new_width} x {new_height}, 缩放比例: {scale_factor:.2f}")

# 创建窗口并设置大小
cv2.namedWindow('Image', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Image', new_width, new_height)

# 传递参数
params = {
    'scale_factor': scale_factor,
    'points': [],
    'display_img': display_img,
    'original_image': original_image,
    'orig_width': img_width,
    'orig_height': img_height
}

cv2.setMouseCallback('Image', get_coordinates, param=params)

while True:
    cv2.imshow('Image', display_img)
    key = cv2.waitKey(1) & 0xFF

    if key == ord('q'):
        break
    elif key == ord('r'):
        # 重置
        params['points'] = []
        display_img = cv2.resize(original_image, (new_width, new_height))
        params['display_img'] = display_img
        print("已重置所有点")
    elif key == ord('c'):
        if params['points']:
            print("\n当前所有点的颜色信息：")
            for i, (px, py) in enumerate(params['points']):
                if 0 <= px < img_width and 0 <= py < img_height:
                    pixel_color = original_image[py, px]
                    b, g, r = pixel_color
                    print(f"点{i + 1}: ({px}, {py}) - RGB:({r}, {g}, {b})")
                else:
                    print(f"点{i + 1}: ({px}, {py}) - 坐标超出图像范围")

cv2.destroyAllWindows()

# 输出最终结果
if params['points']:
    for i, (x, y) in enumerate(params['points']):
        if 0 <= x < img_width and 0 <= y < img_height:
            pixel_color = original_image[y, x]
            b, g, r = pixel_color
            print(f"点{i + 1}: ({x}, {y}) - RGB:({r}, {g}, {b})")