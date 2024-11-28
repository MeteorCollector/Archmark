import numpy as np
import math

def calculate_iou(region1, region2):
    # 获取每个掩码的边界框
    top1, bottom1, left1, right1 = get_bounding_box(region1)
    top2, bottom2, left2, right2 = get_bounding_box(region2)

    # 裁切掩码到有效区域
    region1_cropped = region1[top1:bottom1, left1:right1]
    region2_cropped = region2[top2:bottom2, left2:right2]

    # 计算交集和并集
    intersection = np.sum(np.logical_and(region1_cropped, region2_cropped))
    union = np.sum(np.logical_or(region1_cropped, region2_cropped))
    return intersection / union if union != 0 else 0

def color_similarity(c1, c2, threshold=50):
    r_diff = c1[0] - c2[0]
    g_diff = c1[1] - c2[1]
    b_diff = c1[2] - c2[2]
    distance = math.sqrt(r_diff**2 + g_diff**2 + b_diff**2)
    return distance < threshold

def get_flood_mask(img, x, y, tolerance, visited):
    """ 获取Flood Fill区域的掩码，用于标记填充区域 """
    width, height = img.size
    pixels = img.load()

    # 获取点击位置的颜色
    target_color = pixels[x, y]

    # 创建一个mask标记当前填充区域
    mask = np.zeros((height, width), dtype=np.uint8)
    
    def fill(x, y):
        if x < 0 or y < 0 or x >= width or y >= height:
            return
        if visited[y, x] or mask[y, x] == 1:
            return

        current_color = pixels[x, y]
        if color_similarity(current_color, target_color, tolerance):
            mask[y, x] = 1
            visited[y, x] = True
            # 递归填充上下左右的邻居
            fill(x + 1, y)
            fill(x - 1, y)
            fill(x, y + 1)
            fill(x, y - 1)

    # 从起始点开始填充
    fill(x, y)
    return mask

def get_bounding_box(mask):
    """ 获取填充区域的最小矩形边界 """
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    top, bottom = np.argmax(rows), len(rows) - np.argmax(rows[::-1]) - 1
    left, right = np.argmax(cols), len(cols) - np.argmax(cols[::-1]) - 1
    return top, bottom, left, right