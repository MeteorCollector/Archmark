from PyQt5.QtWidgets import QMainWindow, QLabel, QScrollArea, QPushButton, QVBoxLayout, QFileDialog, QHBoxLayout, QGridLayout, QColorDialog
from PyQt5.QtGui import QPixmap, QImage, QColor
from PyQt5.QtCore import Qt
from PIL import Image, ImageDraw

class ColorFillApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.image = None
        self.history = []
        self.redo_stack = []
        self.current_color = (255, 0, 0)  # 默认红色
        self.tolerance = 50  # 默认容差
        self.initUI()

    def initUI(self):
        self.setWindowTitle("批量填色程序")
        self.setGeometry(100, 100, 1200, 800)

        # 创建QLabel并包裹在QScrollArea中
        self.image_label = QLabel(self)
        self.image_label.setAlignment(Qt.AlignCenter)
        
        # 创建QScrollArea，允许图像滚动查看
        scroll_area = QScrollArea(self)
        scroll_area.setWidget(self.image_label)
        scroll_area.setWidgetResizable(True)

        # 按钮
        self.open_btn = QPushButton("打开文件")
        self.open_btn.clicked.connect(self.open_file)
        self.undo_btn = QPushButton("撤销")
        self.undo_btn.clicked.connect(self.undo)
        self.redo_btn = QPushButton("重做")
        self.redo_btn.clicked.connect(self.redo)

        # 当前颜色显示标签
        self.color_display = QLabel(self)
        self.color_display.setFixedSize(50, 50)
        self.update_color_display(self.current_color)  # 初始化颜色显示

        # 创建颜色选择栏
        self.color_palette = self.create_color_palette()

        # 布局
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.open_btn)
        control_layout.addWidget(self.undo_btn)
        control_layout.addWidget(self.redo_btn)

        color_layout = QVBoxLayout()
        color_layout.addWidget(QLabel("当前颜色"))
        color_layout.addWidget(self.color_display)
        color_layout.addWidget(QLabel("选择颜色"))
        color_layout.addLayout(self.color_palette)

        main_layout = QHBoxLayout()
        main_layout.addWidget(scroll_area, 3)
        main_layout.addLayout(control_layout, 1)
        main_layout.addLayout(color_layout, 1)

        central_widget = QLabel()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.image_label.mousePressEvent = self.mouse_click_event  # 绑定点击事件

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

    def open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "打开文件", "", "PDF Files (*.pdf);;Image Files (*.png *.jpg *.bmp)")
        if file_path:
            if file_path.endswith(".pdf"):
                self.image = self.rasterize_pdf(file_path)
            else:
                self.image = Image.open(file_path)
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
            self.image_label.setPixmap(QPixmap.fromImage(qt_image))

    def pil_to_qimage(self, image):
        image = image.convert("RGBA")
        data = image.tobytes("raw", "RGBA")
        qimage = QImage(data, image.width, image.height, QImage.Format_RGBA8888)
        return qimage

    def mouse_click_event(self, event):
        if self.image:
            # 获取点击位置
            x = event.pos().x()
            y = event.pos().y()
            self.fill_color(x, y)

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

            # 更新图像并显示
            self.image = img
            self.display_image()

    def undo(self):
        if self.history:
            self.redo_stack.append(self.image)
            self.image = self.history.pop()
            self.display_image()

    def redo(self):
        if self.redo_stack:
            self.history.append(self.image)
            self.image = self.redo_stack.pop()
            self.display_image()

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = ColorFillApp()
    window.show()
    sys.exit(app.exec_())
