import numpy as np
import math
from collections import deque
import matplotlib.pyplot as plt
from PIL import Image
import os
import random

def calculate_iou(region1, region2, debug=False):
    # 获取每个掩码的边界框
    top1, bottom1, left1, right1 = get_bounding_box(region1)
    top2, bottom2, left2, right2 = get_bounding_box(region2)
    if top1 == bottom1 or top2 == bottom2 or left1 == right1 or left2 == right2:
        return 0.0
    
    # print(f"[debug] top1 = {top1}, bottom1 = {bottom1}, left1 = {left1}, right1 = {right1}")
    # print(f"[debug] top2 = {top2}, bottom2 = {bottom2}, left2 = {left2}, right2 = {right2}")

    # 裁切掩码到有效区域
    region1_cropped = region1[top1:bottom1+1, left1:right1+1]
    region2_cropped = region2[top2:bottom2+1, left2:right2+1]

    # 计算两个掩码的大小差异
    cropped_height = max(region1_cropped.shape[0], region2_cropped.shape[0])
    cropped_width = max(region1_cropped.shape[1], region2_cropped.shape[1])

    # 创建新掩码，填充至相同尺寸
    region1_resized = np.zeros((cropped_height, cropped_width), dtype=np.uint8)
    region2_resized = np.zeros((cropped_height, cropped_width), dtype=np.uint8)

    # 将裁切后的区域填充到新掩码中
    region1_resized[:region1_cropped.shape[0], :region1_cropped.shape[1]] = region1_cropped
    region2_resized[:region2_cropped.shape[0], :region2_cropped.shape[1]] = region2_cropped

    # 计算交集和并集
    intersection = np.sum(np.logical_and(region1_resized, region2_resized))
    union = np.sum(np.logical_or(region1_resized, region2_resized))

    iou_value = intersection / union if union != 0 else 0

    # 如果是调试模式，保存掩码图像
    if debug:
        # 创建目录
        debug_dir = './test/debug'
        os.makedirs(debug_dir, exist_ok=True)

        # 文件名：iou数值 + region1/region2/union
        filename = os.path.join(debug_dir, f"{iou_value:.6f}_iou.png")

        # 创建并保存图片
        fig, axes = plt.subplots(4, 1, figsize=(15, 15))
        axes[0].imshow(np.logical_not(region1), cmap='gray')
        axes[0].set_title('Region 1')
        axes[0].axis('off')

        axes[1].imshow(np.logical_not(region2), cmap='gray')
        axes[1].set_title('Region 2')
        axes[1].axis('off')

        union_mask = np.logical_not(np.logical_or(region1_resized, region2_resized)).astype(np.uint8)
        axes[2].imshow(union_mask, cmap='gray')
        axes[2].set_title('Union')
        axes[2].axis('off')

        union_mask = np.logical_not(np.logical_and(region1_resized, region2_resized)).astype(np.uint8)
        axes[3].imshow(union_mask, cmap='gray')
        axes[3].set_title('Intersection')
        axes[3].axis('off')

        # 保存图像
        plt.tight_layout()
        plt.savefig(filename)
        plt.close(fig)

    return iou_value

def color_similarity(c1, c2, threshold=50):
    r_diff = c1[0] - c2[0]
    g_diff = c1[1] - c2[1]
    b_diff = c1[2] - c2[2]
    distance = math.sqrt(r_diff**2 + g_diff**2 + b_diff**2)
    return distance < threshold

def get_flood_mask(img, x, y, tolerance):
    """ 获取Flood Fill区域的掩码，用于标记填充区域，使用BFS代替递归 """
    width, height = img.size
    pixels = img.load()

    # 获取点击位置的颜色
    target_color = pixels[x, y]
    fill_pixels = []

    # 创建一个mask标记当前填充区域
    mask = np.zeros((height, width), dtype=np.uint8)
    visited = np.zeros((height, width), dtype=bool)
    
    # 使用BFS实现填充
    queue = deque([(x, y)])  # 队列初始化，存储待处理的像素位置
    visited[y, x] = True  # 标记起始点已访问
    mask[y, x] = 1  # 标记起始点为填充区域

    # BFS填充
    while queue:
        cx, cy = queue.popleft()  # 从队列中取出当前处理的像素位置

        # 检查四个方向的邻居
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = cx + dx, cy + dy

            # 检查边界
            if 0 <= nx < width and 0 <= ny < height:
                if not visited[ny, nx] and color_similarity(pixels[nx, ny], target_color, tolerance):
                    visited[ny, nx] = True  # 标记为已访问
                    mask[ny, nx] = 1  # 标记为填充区域
                    queue.append((nx, ny))  # 将邻居加入队列，等待处理
                    fill_pixels.append((nx, ny))
    
    # 随机选取 k 个点，计算它们的距离
    # def distance_to_edge(x, y):
    #     """ 计算坐标 (x, y) 到四个边缘的最小距离 """
    #     return min(x, width - x - 1, y, height - y - 1)

    # # 随机选择 k 个像素点
    # random_pixels = random.sample(fill_pixels, min(k, len(fill_pixels)))

    # 计算距离边缘最远的像素
    # max_distance = -1
    # central_pixel = None
    # for px, py in random_pixels:
    #     dist = distance_to_edge(px, py)
    #     if dist > max_distance:
    #         max_distance = dist
    #         central_pixel = (px, py)

    return mask, fill_pixels

def get_bounding_box(mask):
    """ 获取填充区域的最小矩形边界 """
    rows = np.any(mask, axis=1)
    cols = np.any(mask, axis=0)
    top, bottom = np.argmax(rows), len(rows) - np.argmax(rows[::-1]) - 1
    left, right = np.argmax(cols), len(cols) - np.argmax(cols[::-1]) - 1
    return top, bottom, left, right