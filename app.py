from PyQt5.QtWidgets import QMainWindow, QLabel, QScrollArea, QPushButton, QVBoxLayout, QFileDialog, QHBoxLayout, QGridLayout, QColorDialog, QTextEdit, QSlider, QAction
from PyQt5.QtGui import QPixmap, QImage, QColor, QTextCursor, QTextCharFormat, QTransform
from PyQt5.QtCore import Qt
from PIL import Image, ImageDraw
import numpy as np
from util import *

class ColorFillApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image = None
        self.log_count = 12
        self.history = []
        self.redo_stack = []
        self.current_color = (255, 0, 0)  # 默认红色
        self.tolerance = 36  # 默认容差
        self.log_messages = []  # 存储日志的列表
        self.current_tool = None  # 当前工具
        self.scale_factor = 1.0
        self.original_pixmap = None

        self.debug = False

        self.initUI()
        self.resize(1920, 1080)

    def initUI(self):
        self.setWindowTitle("Archmark v0.0")
        self.setGeometry(100, 100, 1200, 800)

        # 创建QLabel并包裹在QScrollArea中
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        # self.image_label.setFixedSize(1024, 768)  # 初始化为固定大小
        self.image_label.wheelEvent = self.on_wheel_event
        
        # 创建QScrollArea，允许图像滚动查看
        scroll_area = QScrollArea(self)
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)

        # 按钮
        self.undo_btn = QPushButton("撤销")
        self.undo_btn.clicked.connect(self.undo)
        self.redo_btn = QPushButton("重做")
        self.redo_btn.clicked.connect(self.redo)

        # 功能按钮
        paint_bucket_button = QPushButton("[工具] 普通的颜料桶")
        paint_bucket_button.clicked.connect(self.select_paint_bucket)
        mode_bucket_button = QPushButton("[工具] 模式匹配颜料桶")
        mode_bucket_button.clicked.connect(self.select_mode_bucket)

        # 当前功能
        self.tool_label = QLabel(f"当前工具：暂无")

        # 容差滑块
        self.tolerance_label = QLabel(f"容差: {self.tolerance}")
        self.tolerance_slider = QSlider(Qt.Horizontal)
        self.tolerance_slider.setRange(0, 255)
        self.tolerance_slider.setValue(50)
        self.tolerance_slider.setTickPosition(QSlider.TicksBelow)
        self.tolerance_slider.valueChanged.connect(self.update_tolerance)

        # 当前颜色显示标签
        self.color_display = QLabel(self)
        self.color_display.setFixedSize(50, 50)
        self.update_color_display(self.current_color)  # 初始化颜色显示

        # 创建颜色选择栏
        self.color_palette = self.create_color_palette()

        # 日志输出
        self.log_display = QTextEdit(self)
        self.log_display.setReadOnly(True)  # 设置为只读，不允许用户修改日志
        # self.log_display.setFixedHeight(150)  # 设置合适的高度  

        # 布局
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.undo_btn)
        control_layout.addWidget(self.redo_btn)

        # 工具
        tool_layout = QVBoxLayout()
        tool_layout.addWidget(paint_bucket_button)
        tool_layout.addWidget(mode_bucket_button)
        tool_layout.addWidget(self.tool_label)

        color_layout = QVBoxLayout()
        color_layout.addWidget(self.tolerance_label)
        color_layout.addWidget(self.tolerance_slider)
        color_layout.addWidget(QLabel("当前颜色"))
        color_layout.addWidget(self.color_display)
        color_layout.addWidget(QLabel("选择颜色"))
        color_layout.addLayout(self.color_palette)

        sidebar_layout = QVBoxLayout()
        sidebar_layout.addLayout(control_layout)
        sidebar_layout.addLayout(tool_layout)
        sidebar_layout.addLayout(color_layout)

        # 布局修改
        log_layout = QVBoxLayout()
        log_layout.addWidget(QLabel("日志"))
        log_layout.addWidget(self.log_display)

        # 主布局
        main_layout = QHBoxLayout()
        main_layout.addWidget(scroll_area, 3)
        main_layout.addLayout(sidebar_layout, 1)
        main_layout.addLayout(log_layout, 1)  # 将日志区域添加到布局中

        central_widget = QLabel()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        self.create_menu()

        self.image_label.mousePressEvent = self.mouse_click_event  # 绑定点击事件
    
    def create_menu(self):
        """ 创建菜单栏和保存动作 """
        menubar = self.menuBar()
        file_menu = menubar.addMenu("文件 Files")
        
        save_action = QAction("保存 Save", self)
        save_action.triggered.connect(self.save_image)

        load_action = QAction("导入文件(PDF或者图片) Import File", self)
        load_action.triggered.connect(self.open_file)
        
        file_menu.addAction(load_action)
        file_menu.addAction(save_action)
        
    def select_paint_bucket(self):
        """ 选择颜料桶工具 """
        self.current_tool = 'paint_bucket'
        self.printLog("已选择很普通的颜料桶工具", color="blue", isBold=True)
        self.tool_label.setText("当前工具：普通颜料桶")
    
    def select_mode_bucket(self):
        """ 选择模式颜料桶工具 """
        self.current_tool = 'mode_bucket'
        self.printLog("已选择比较厉害的模式颜料桶工具", color="blue", isBold=True)
        self.tool_label.setText("当前工具：模式颜料桶")

    def create_color_palette(self):
        """ 创建颜色调色盘，返回一个 QGridLayout """
        color_palette = QGridLayout()
        colors = [
            (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
            (0, 255, 255), (255, 0, 255), (255, 165, 0), (128, 0, 128),
            (0, 128, 128), (0, 0, 0), (255, 255, 255), (192, 192, 192)
        ]
        for i, color in enumerate(colors):
            button = QPushButton()
            button.setStyleSheet(f"background-color: rgb{color};")
            button.clicked.connect(lambda _, c=color: self.set_color(c))
            color_palette.addWidget(button, i // 4, i % 4)

        return color_palette

    def set_color(self, color):
        """ 设置当前选择的颜色 """
        self.current_color = color
        self.update_color_display(self.current_color)

    def update_color_display(self, color):
        """ 更新当前颜色的显示框 """
        self.color_display.setStyleSheet(f"background-color: rgb{color};")
    
    def update_tolerance(self):
        self.tolerance = self.tolerance_slider.value()
        self.tolerance_label.setText(f"容差: {self.tolerance}")

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "打开文件", "", "PDF Files (*.pdf);;Image Files (*.png *.jpg *.bmp)")
        if file_path:
            if file_path.endswith(".pdf"):
                self.image = self.rasterize_pdf(file_path)
            else:
                self.image = Image.open(file_path)
            self.scale_factor = 1.0
            self.display_image()

    def rasterize_pdf(self, file_path):
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
        image = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        return image

    def display_image(self):
        if self.image:
            qt_image = self.pil_to_qimage(self.image)
            mypixmap = QPixmap.fromImage(qt_image)
            # self.image_label.setPixmap(mypixmap)
            self.original_pixmap = mypixmap

            transform = QTransform()
            transform.scale(self.scale_factor, self.scale_factor)
            scaled_pixmap = self.original_pixmap.transformed(transform)
            self.image_label.setPixmap(scaled_pixmap)

    def pil_to_qimage(self, image):
        image = image.convert("RGBA")
        data = image.tobytes("raw", "RGBA")
        qimage = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
        return qimage
    
    def save_image(self):
        """ 保存当前图像到指定路径 """
        if self.image is not None:
            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", "", "PNG 图片 (*.png);;JPEG 图片 (*.jpg *.jpeg);;所有文件 (*.*)")

            if file_path:
                # 如果文件路径不为空，保存图片
                self.image.save(file_path)  # 使用PIL.Image.save保存图片
                print(f"图片已保存到: {file_path}")
                self.printLog(f"图片已保存到: {file_path}", color="green", isBold=True)
            else:
                print("保存操作被取消")
                self.printLog("保存操作被取消", color="red", isBold=True)
        else:
            print("没有图像可保存")
            self.printLog("没有图像可保存", color="red", isBold=True)

    def mouse_click_event(self, event):
        if self.image:
            # 获取点击位置
            x = int(event.pos().x() / self.scale_factor)
            y = int(event.pos().y() / self.scale_factor)
            if self.current_tool == 'paint_bucket':
                
                self.printLog(f"点击位置 ({x}, {y}), 当前颜色: {self.current_color}, 容差: {self.tolerance}, 正在填色中")
                self.fill_color(x, y)
            if self.current_tool == 'mode_bucket':
                # 获取点击位置
                self.mode_paint_bucket(x, y)
    
    def on_wheel_event(self, event):
        """ 处理鼠标滚轮事件，实现缩放 """
        # 获取鼠标滚轮的角度，决定是放大还是缩小
        delta = event.angleDelta().y()  # 正值表示滚动向上（放大），负值表示滚动向下（缩小）

        # 设置缩放因子
        if delta > 0:  # 放大
            self.scale_factor *= 1.1
        else:  # 缩小
            self.scale_factor /= 1.1

        # 更新QLabel显示的图像
        self.update_image_display()

    def update_image_display(self):
        """ 使用QTransform来缩放QPixmap而不改变原始图片 """
        if self.original_pixmap:
            # 创建一个QTransform对象来实现缩放
            transform = QTransform()
            transform.scale(self.scale_factor, self.scale_factor)

            # 应用缩放变换
            scaled_pixmap = self.original_pixmap.transformed(transform)

            # 更新QLabel显示的图像
            self.image_label.setPixmap(scaled_pixmap)

    def fill_color(self, x, y):
        if self.image:
            # 保存当前图像状态，用于撤销
            self.history.append(self.image.copy())
            self.redo_stack.clear()  # 清除重做栈

            img = self.image.copy()  # 使用副本
            target_color = img.getpixel((x, y))  # 获取点击点颜色

            print(f"点击位置 ({x}, {y}), 当前颜色: {target_color}, 填充颜色: {self.current_color}")

            # 使用 Pillow 的 floodfill 方法
            ImageDraw.floodfill(
                img, (x, y), self.current_color, thresh=self.tolerance
            )
            self.printLog(f"填色成功！当前填充颜色: {self.current_color}", color="green", isBold=True)

            # 更新图像并显示
            self.image = img
            self.display_image()

    def undo(self):
        if self.history:
            self.redo_stack.append(self.image)
            self.image = self.history.pop()
            self.display_image()
            self.printLog(f"已撤销", color="blue", isBold=True)

    def redo(self):
        if self.redo_stack:
            self.history.append(self.image)
            self.image = self.redo_stack.pop()
            self.display_image()
            self.printLog(f"已重做", color="blue", isBold=True)

    def printLog(self, message, color="black", isBold=False):
        """ 打印日志信息，并支持自定义颜色 """
        # 为每条日志设置HTML格式
        if isBold is True:
            message = f'<b>{message}</b>'
        log_message_html = f'<font color="{color}">{message}</font><br>'
        
        # 添加新日志到列表
        self.log_messages.append(log_message_html)
        
        # 如果日志太多，删除最旧的日志
        if len(self.log_messages) > self.log_count:
            self.log_messages.pop(0)

        # 更新显示的日志，将所有日志条目连接为单一HTML字符串
        log_html = "".join(self.log_messages)
        self.log_display.setHtml(log_html)


# mode bucket
    def mode_paint_bucket(self, x, y, iou_threshold=0.6):
        """ 模式颜料桶功能 """
        fixed_tolerance = 30.0
        if self.image:
            # 保存当前图像状态，用于撤销
            self.history.append(self.image.copy())
            self.redo_stack.clear()  # 清除重做栈
            self.printLog(f"模式颜料桶正在运行中，请暂时不要进行别的操作...", color="red", isBold=True)
            QApplication.processEvents()

            img = self.image.copy()  # 使用副本

            width, height = img.size

            # 创建访问标记数组
            visited = np.zeros((height, width), dtype=bool)

            # 1. 使用get_flood_mask获取初次填色的区域掩码
            initial_mask, _ = get_flood_mask(img, x, y, fixed_tolerance)

            # 2. 获取填充区域的边界框
            top, bottom, left, right = get_bounding_box(initial_mask)
            mask_height, mask_width = bottom - top + 1, right - left + 1
            print(f"Initial fill bounding box: {(left, top, right, bottom)}")

            # 3. 使用访问标记数组避免重复枚举
            for i in range(width - mask_width):
                for j in range(height - mask_height):
                    # 跳过已经访问过的位置
                    if visited[j, i]:
                        continue

                    # 4. 尝试从当前位置获取填充掩码，并获取新的区域掩码
                    temp_mask, fill_pixels = get_flood_mask(img, i, j, fixed_tolerance)
                    visited = np.logical_or(visited, temp_mask)

                    # 5. 计算IOU值
                    iou = calculate_iou(initial_mask, temp_mask, self.debug)
                    # print(f"[debug] iou = {iou}") # debug
                    
                    # 6. 标记 vis 数组，而且如果IOU大于阈值，则填充该区域
                    # for dx in range(mask_width):
                    #     for dy in range(mask_height):
                    #         # if 0 <= j + dy < height and 0 <= i + dx < width:
                    #         if temp_mask[j + dy, i + dx] == 1:
                    #             visited[j + dy, i + dx] = 1
                    
                    if iou > iou_threshold:
                        # ImageDraw.floodfill(
                        #     img, central_point, self.current_color, thresh=fixed_tolerance
                        # )
                        pixels = img.load()
                        for px, py in fill_pixels:
                            pixels[px, py] = self.current_color
                        print(f"发现一处模式匹配，已填色")
                        self.printLog(f"发现一处模式匹配，已填色: {self.current_color}")
                        self.printLog(f"模式颜料桶正在运行中，请暂时不要进行别的操作...", color="red", isBold=True)
                        QApplication.processEvents()
                        self.image = img
                        self.display_image()
            
            print(f"点击位置 ({x}, {y}), 填充颜色: {self.current_color}")

            self.printLog(f"模式颜料桶填色成功！当前填充颜色: {self.current_color}", color="green", isBold=True)

            # 更新图像并显示
            self.image = img
            self.display_image()



if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ColorFillApp()
    window.show()
    sys.exit(app.exec_())
