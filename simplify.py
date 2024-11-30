import sys
import fitz  # PyMuPDF
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QPushButton, QLineEdit, QLabel, QFileDialog, QHBoxLayout, QMessageBox, QScrollArea
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtCore import Qt
import json

class PDFEditor(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("PDF 编辑器")
        self.setGeometry(100, 100, 800, 600)

        self.pdf_path = None
        self.current_page = 0
        self.doc = None
        self.image = None

        # 创建UI元素
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 创建Scroll Area以支持滚动
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)  # 允许自适应大小

        # 创建PDF显示区域（QLabel）
        self.pdf_view = QLabel(self)
        self.pdf_view.setAlignment(Qt.AlignCenter)

        # 将QLabel添加到QScrollArea中
        self.scroll_area.setWidget(self.pdf_view)

        layout.addWidget(self.scroll_area)

        # 控件布局
        control_layout = QHBoxLayout()

        # 导入PDF按钮
        self.import_button = QPushButton("导入PDF", self)
        self.import_button.clicked.connect(self.import_pdf)
        control_layout.addWidget(self.import_button)

        # 最小线条长度输入框
        self.length_label = QLabel("最小线条长度:", self)
        control_layout.addWidget(self.length_label)

        self.length_entry = QLineEdit(self)
        control_layout.addWidget(self.length_entry)

        # 删除线条按钮
        self.delete_button = QPushButton("删除短线条", self)
        self.delete_button.clicked.connect(self.delete_short_lines)
        control_layout.addWidget(self.delete_button)

        # 下一页按钮
        self.next_button = QPushButton("下一页", self)
        self.next_button.clicked.connect(self.next_page)
        control_layout.addWidget(self.next_button)

        # 上一页按钮
        self.prev_button = QPushButton("上一页", self)
        self.prev_button.clicked.connect(self.prev_page)
        control_layout.addWidget(self.prev_button)

        layout.addLayout(control_layout)
        
        # 设置主窗口的布局
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    def import_pdf(self):
        # 打开文件选择对话框
        file_dialog = QFileDialog(self)
        self.pdf_path, _ = file_dialog.getOpenFileName(self, "选择PDF文件", "", "PDF Files (*.pdf)")
        if self.pdf_path:
            self.doc = fitz.open(self.pdf_path)
            self.current_page = 0  # 重置为第一页
            self.show_page(self.current_page)

    def show_page(self, page_num):
        # 获取指定页面
        page = self.doc.load_page(page_num)
        
        # 渲染页面为图像
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 放大渲染，确保清晰度
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

        # 将图像显示在QLabel上
        self.image = QPixmap.fromImage(img)
        self.pdf_view.setPixmap(self.image)
    
    def show_tmp_page(self, page):
        # 渲染页面为图像
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 放大渲染，确保清晰度
        img = QImage(pix.samples, pix.width, pix.height, pix.stride, QImage.Format_RGB888)

        # 将图像显示在QLabel上
        self.image = QPixmap.fromImage(img)
        self.pdf_view.setPixmap(self.image)

    def next_page(self):
        # 切换到下一页
        if self.doc and self.current_page < len(self.doc) - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def prev_page(self):
        # 切换到上一页
        if self.doc and self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

    def delete_short_lines(self):
        self.save_drawings_to_json() # debug
        if not self.doc:
            self.show_message("错误", "请先导入PDF文件！")
            return

        try:
            # 获取最小线条长度
            min_length = float(self.length_entry.text())
        except ValueError:
            self.show_message("错误", "请输入有效的最小线条长度！")
            return

        page = self.doc.load_page(self.current_page)
        original_drawings = page.get_drawings()

        # 遍历页面上的图形
        for path in original_drawings:
            # 遍历路径中的每条线
            for line in path["items"]:
                if line[0] == "l":  # 判断是否是线条（"l"表示line）
                    # 提取起始点和终点的坐标
                    x1, y1 = line[1].x, line[1].y
                    x2, y2 = line[2].x, line[2].y

                    # 计算线条长度
                    length = ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5
                    
                    # 如果线条长度小于最小长度，则删除该线条
                    if length < min_length:
                        path["items"].remove(line)

        # 清除旧内容并绘制更新后的图形
        page.clean_contents()

        # 使用我们实现的 draw_path 函数来绘制更新后的路径
        page = self.draw_path(page, original_drawings)

        # 更新显示页面
        # self.show_page(self.current_page)
        self.show_tmp_page(page)


        # 提示删除成功
        self.show_message("完成", "短线条删除成功！")

    def draw_path(self, page, paths):
        """
        这个方法用于绘制给定的路径（items）到页面中。
        """
        shape = page.new_shape()

        # 遍历路径中的每一项，并绘制它们
        for path in paths:
            for item in path["items"]:
                if item[0] == "l":  # 线条
                    shape.draw_line(item[1], item[2])
                elif item[0] == "re":  # 矩形
                    shape.draw_rect(item[1])
                elif item[0] == "qu":  # 四边形
                    shape.draw_quad(item[1])
                elif item[0] == "c":  # 贝塞尔曲线
                    shape.draw_bezier(item[1], item[2], item[3], item[4])
                else:
                    raise ValueError("Unhandled drawing item", item)

            # 设置路径的样式
            shape.finish(
                # fill=path.get("fill"), 
                # color=path.get("color"), 
                # dashes=path.get("dashes"), 
                # even_odd=path.get("even_odd", True),
                # closePath=path.get("closePath"), 
                # lineJoin=path.get("lineJoin"), 
                # lineCap=max(path.get("lineCap", [0])), 
                # width=path.get("width", 1),
                # stroke_opacity=path.get("stroke_opacity", 1),
                # fill_opacity=path.get("fill_opacity", 1),
            )

        shape.commit()
        return page

    def save_drawings_to_json(self):
        if not self.doc:
            self.show_message("错误", "请先导入PDF文件！")
            return

        page = self.doc.load_page(self.current_page)
        
        # 获取页面的所有绘制内容
        drawings = page.get_drawings()

        # 创建一个列表，用于存储转换后的路径数据
        drawing_data = []

        # 遍历所有路径，将其转换为可序列化的格式
        for path in drawings:
            path_data = {}
            path_data["fill"] = path.get("fill", None)
            path_data["color"] = path.get("color", None)
            path_data["dashes"] = path.get("dashes", None)
            path_data["even_odd"] = path.get("even_odd", True)
            path_data["closePath"] = path.get("closePath", False)
            path_data["lineJoin"] = path.get("lineJoin", None)
            path_data["lineCap"] = path.get("lineCap", None)
            path_data["width"] = path.get("width", None)
            path_data["stroke_opacity"] = path.get("stroke_opacity", 1)
            path_data["fill_opacity"] = path.get("fill_opacity", 1)
            
            # 将路径项转换为可以序列化的格式
            items = []
            for item in path["items"]:
                if item[0] == "l":
                    # 线条，转换为字典格式
                    line = {
                        "type": "line",
                        "start": {"x": item[1].x, "y": item[1].y},
                        "end": {"x": item[2].x, "y": item[2].y}
                    }
                    items.append(line)
                elif item[0] == "re":
                    # 矩形，转换为字典格式
                    rect = {
                        "type": "rectangle",
                        "rect": {"x": item[1].x, "y": item[1].y, "width": item[1].width, "height": item[1].height}
                    }
                    items.append(rect)
                elif item[0] == "qu":
                    # 四边形，转换为字典格式
                    quad = {
                        "type": "quad",
                        "points": [{"x": p.x, "y": p.y} for p in item[1]]
                    }
                    items.append(quad)
                elif item[0] == "c":
                    # 贝塞尔曲线，转换为字典格式
                    bezier = {
                        "type": "bezier",
                        "control_points": [{"x": p.x, "y": p.y} for p in item[1:5]]
                    }
                    items.append(bezier)

            # 将路径项添加到路径数据中
            path_data["items"] = items
            drawing_data.append(path_data)

        # 将数据写入JSON文件
        with open("drawing.json", "w", encoding="utf-8") as f:
            json.dump(drawing_data, f, ensure_ascii=False, indent=4)

        # 提示用户文件已保存
        self.show_message("完成", "绘制数据已保存到 drawing.json 文件！")

    def show_message(self, title, message):
        # 显示信息框
        QMessageBox.information(self, title, message)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = PDFEditor()
    window.show()
    sys.exit(app.exec_())
