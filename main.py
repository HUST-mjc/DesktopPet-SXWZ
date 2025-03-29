import os
import sys
import random
import webbrowser  # 用于打开浏览器
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *

# 获取资源文件的绝对路径（适用于打包后的 .exe 文件）
def resource_path(relative_path):
    """获取资源文件的绝对路径（适用于打包后的 .exe 文件）"""
    # 获取 .exe 文件所在的目录
    base_path = os.path.dirname(sys.executable)
    return os.path.join(base_path, relative_path)

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))


class ImageLoader(QThread):
    """异步加载图片的线程"""
    image_loaded = pyqtSignal(QImage)

    def __init__(self, image_path):
        super().__init__()
        self.image_path = image_path

    def run(self):
        image = QImage()
        if image.load(self.image_path):
            self.image_loaded.emit(image)


class DesktopPet(QWidget):
    def __init__(self, pet_name, image_folder=None, parent=None, **kwargs):
        super(DesktopPet, self).__init__(parent)
        self.pet_name = pet_name
        # 构建图片文件夹的绝对路径
        self.image_folder = resource_path(os.path.join("resources", image_folder)) if image_folder else None
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.SubWindow)
        self.setAutoFillBackground(False)
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.repaint()
        self.pet_images = self.randomLoadPetImages()
        self.current_image_index = 0
        self.image = QLabel(self)
        self.current_scale = 1.0  # 初始化缩放比例
        if self.pet_images:
            self.setImage(self.pet_images[0])
        else:
            # 如果没有图片，使用默认图片
            default_image_path = resource_path(os.path.join("resources", "default.png"))
            default_image = self.loadAndScaleImage(default_image_path)
            if default_image:
                self.pet_images.append(default_image)
                self.setImage(default_image)
            else:
                print(f"未找到默认图片: {default_image_path}")
        self.is_follow_mouse = False
        self.mouse_drag_pos = self.pos()
        self.randomPosition()
        self.show()
        
        # 新增属性：直播间和个人主页链接
        self.live_url = None
        self.space_url = None
        self.selector = None  # 保存 PetSelector 的引用

    def keyPressEvent(self, event):
        # 检测空格键按下事件
        if event.key() == Qt.Key_Space:
            self.nextImage()
        # 检测 ESC 键按下事件
        elif event.key() == Qt.Key_Escape:
            self.quit()

    def wheelEvent(self, event):
        # 鼠标滚轮事件用于调整图片大小
        if event.angleDelta().y() > 0:
            # 向上滚动，放大图片
            self.current_scale += 0.1
        else:
            # 向下滚动，缩小图片
            self.current_scale -= 0.1
            if self.current_scale < 0.1:
                self.current_scale = 0.1  # 最小缩放比例为 10%
        
        # 更新图片显示
        if self.pet_images:
            current_image = self.pet_images[self.current_image_index]
            scaled_image = current_image.scaled(
                int(current_image.width() * self.current_scale),
                int(current_image.height() * self.current_scale),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image.setPixmap(QPixmap.fromImage(scaled_image))
            self.resize(scaled_image.width(), scaled_image.height())
            self.randomPosition()  # 重新定位以确保图片在屏幕内

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_follow_mouse = True
            self.mouse_drag_pos = event.globalPos() - self.pos()
            event.accept()
            self.setCursor(QCursor(Qt.OpenHandCursor))

    def mouseMoveEvent(self, event):
        if Qt.LeftButton and self.is_follow_mouse:
            self.move(event.globalPos() - self.mouse_drag_pos)
            event.accept()

    def mouseReleaseEvent(self, event):
        self.is_follow_mouse = False
        self.setCursor(QCursor(Qt.ArrowCursor))

    def nextImage(self):
        if self.pet_images:
            self.current_image_index = (self.current_image_index + 1) % len(self.pet_images)
            self.setImage(self.pet_images[self.current_image_index])

    def randomLoadPetImages(self):
        images = []
        if self.image_folder and os.path.exists(self.image_folder):
            # 获取文件夹中的所有文件
            image_files = [f for f in os.listdir(self.image_folder) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif'))]
            if image_files:
                for image_file in image_files:
                    image_path = os.path.join(self.image_folder, image_file)
                    image = self.loadAndScaleImage(image_path)
                    if image:
                        images.append(image)
            else:
                print(f"指定文件夹中没有图片文件: {self.image_folder}")
        else:
            print(f"指定文件夹不存在: {self.image_folder}")
        return images

    def loadAndScaleImage(self, image_path):
        image = QImage()
        if image.load(image_path):
            # 计算缩放比例，确保图片在宠物窗口内
            base_width = 400
            base_height = 410
            image_width = image.width()
            image_height = image.height()
            
            # 计算缩放比例
            scale_width = base_width / image_width
            scale_height = base_height / image_height
            scale = min(scale_width, scale_height)
            
            # 缩放图片
            scaled_image = image.scaled(
                int(image_width * scale),
                int(image_height * scale),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            return scaled_image
        else:
            print(f"无法加载图片: {image_path}")
        return None

    def setImage(self, image):
        if image:
            scaled_image = image.scaled(
                int(image.width() * self.current_scale),
                int(image.height() * self.current_scale),
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            self.image.setPixmap(QPixmap.fromImage(scaled_image))
            self.resize(scaled_image.width(), scaled_image.height())

    def randomPosition(self):
        screen = QApplication.primaryScreen()
        screen_geometry = screen.geometry()
        screen_width = screen_geometry.width()
        screen_height = screen_geometry.height()
        pet_width = self.width()
        pet_height = self.height()
    
        # 确保宠物在屏幕范围内
        max_x = screen_width - pet_width
        max_y = screen_height - pet_height
    
        # 生成随机位置（整数）
        width = random.randint(0, max_x)
        height = random.randint(0, max_y)
    
        self.move(width, height)

    def quit(self):
        self.close()

    # 修改右键菜单功能
    def contextMenuEvent(self, event):
        context_menu = QMenu(self)
        open_live_action = context_menu.addAction("打开直播间")
        open_space_action = context_menu.addAction("打开个人主页")
        return_main_action = context_menu.addAction("返回主界面")  # 修改为返回主界面

        # 连接槽函数
        open_live_action.triggered.connect(self.open_live)
        open_space_action.triggered.connect(self.open_space)
        return_main_action.triggered.connect(self.return_to_main)  # 修改为返回主界面

        # 显示菜单
        context_menu.exec_(event.globalPos())

    # 打开直播间
    def open_live(self):
        if self.live_url:
            webbrowser.open(self.live_url)
        else:
            print("未设置直播间链接")

    # 打开个人主页
    def open_space(self):
        if self.space_url:
            webbrowser.open(self.space_url)
        else:
            print("未设置个人主页链接")

    # 设置直播间和个人主页链接
    def set_urls(self, live_url, space_url):
        self.live_url = live_url
        self.space_url = space_url

    # 返回主界面
    def return_to_main(self):
        print("返回主界面")  # 调试输出
        self.hide()  # 隐藏当前宠物窗口
        self.show_pet_selector()  # 显示主界面

    # 显示选择宠物的界面
    def show_pet_selector(self):
        self.selector = PetSelector()  # 保存 PetSelector 的引用
        self.selector.show()


class PetSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.pets = []
        self.set_background_image()  # 设置背景图片

    def initUI(self):
        self.setWindowTitle("欢迎来到禧运楼")
        self.setGeometry(300, 300, 800, 400)  # 调整窗口大小以适应横向排列的按钮

        # 创建按钮
        self.btn_bekki = QPushButton("恬豆包", self)  # 四
        self.btn_yoyi = QPushButton("酥酥又", self)    # 禧
        self.btn_queenie = QPushButton("小沐标", self)  # 丸
        self.btn_lian = QPushButton("向心梨", self)    # 子
        self.btn_two = QPushButton("请选择你的CP", self)
        self.btn_four = QPushButton("丸不灭", self)

        # 设置按钮透明背景和悬停效果
        button_style = """
        QPushButton {
            color: transparent;  /* 默认文字透明 */
            border: none;
            font-family: "楷体";  /* 设置字体为楷体 */
            font-size: 50px;  /* 字体大小 */
        }
        QPushButton:hover {
            color: #ffb3bf;  /* 悬停时文字颜色 */
        }
        """

        # 为每个按钮设置背景图片和透明效果
        self.set_button_image(self.btn_bekki, "四.png")
        self.set_button_image(self.btn_yoyi, "禧.png")
        self.set_button_image(self.btn_queenie, "丸.png")
        self.set_button_image(self.btn_lian, "子.png")

        # 应用样式到所有按钮
        self.btn_bekki.setStyleSheet(button_style)
        self.btn_yoyi.setStyleSheet(button_style)
        self.btn_queenie.setStyleSheet(button_style)
        self.btn_lian.setStyleSheet(button_style)

        # 设置"选择你的CP"和"丸不灭"按钮的样式
        semi_transparent_style = """
        QPushButton {
            background-color: rgba(255, 255, 255, 128);  /* 白色半透明背景 */
            color: rgba(128, 0, 128, 0.2);  /* 紫色20%透明文字 */
            border: none;
            font-family: "楷体";  /* 设置字体为楷体 */
            font-size: 50px;  /* 字体大小 */
        }
        QPushButton:hover {
            background-color: rgba(255, 255, 255, 192);  /* 悬停时背景颜色 */
        }
        """
        self.btn_two.setStyleSheet(semi_transparent_style)
        self.btn_four.setStyleSheet(semi_transparent_style)

        # 设置"选择你的CP"和"丸不灭"按钮的大小
        self.btn_two.setFixedSize(318, 159)
        self.btn_four.setFixedSize(318, 159)

        # 创建开始和买单按钮
        self.btn_start = QPushButton("开始", self)
        self.btn_close = QPushButton("买单", self)

        # 设置开始和买单按钮的样式
        start_button_style = """
        QPushButton {
            background-color: pink;  /* 粉色背景 */
            color: black;  /* 文字颜色 */
            border: none;
            font-family: "楷体";  /* 设置字体为楷体 */
            font-size: 50px;  /* 字体大小 */
        }
        QPushButton:hover {
            background-color: lightpink;  /* 悬停时背景颜色 */
        }
        """
        self.btn_start.setStyleSheet(start_button_style)
        self.btn_close.setStyleSheet(start_button_style)

        # 设置开始和买单按钮的大小
        self.btn_start.setFixedSize(200, 200)
        self.btn_close.setFixedSize(200, 200)

        # 横向排列按钮
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.btn_bekki)
        h_layout.addWidget(self.btn_yoyi)
        h_layout.addWidget(self.btn_queenie)
        h_layout.addWidget(self.btn_lian)

        # 垂直布局包含横向按钮和开始、买单按钮
        v_layout = QVBoxLayout()
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.btn_two, alignment=Qt.AlignCenter)
        v_layout.addWidget(self.btn_four, alignment=Qt.AlignCenter)

        # 创建底部布局
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.btn_start)
        bottom_layout.addWidget(self.btn_close)

        # 添加底部布局到主布局
        v_layout.addLayout(bottom_layout)

        self.setLayout(v_layout)

        # 连接信号
        self.btn_queenie.clicked.connect(lambda: self.select_pet("Queenie"))
        self.btn_yoyi.clicked.connect(lambda: self.select_pet("Yoyi"))
        self.btn_bekki.clicked.connect(lambda: self.select_pet("Bekki"))
        self.btn_lian.clicked.connect(lambda: self.select_pet("Lian"))
        self.btn_two.clicked.connect(self.select_two_pets)
        self.btn_four.clicked.connect(self.select_four_pets)
        self.btn_start.clicked.connect(self.start_pets)
        self.btn_close.clicked.connect(self.close_all_pets)

    def set_background_image(self):
        # 构建背景图片的绝对路径
        background_image_path = resource_path(os.path.join("resources", "Back.jpg"))
        
        # 检查图片是否存在
        if not os.path.exists(background_image_path):
            print(f"背景图片不存在: {background_image_path}")
            return

        # 加载背景图片
        background_image = QImage(background_image_path)
        if not background_image.isNull():
            # 获取图片的宽度和高度
            width = background_image.width()
            height = background_image.height()

            # 设置窗口大小为图片大小
            self.resize(width, height)

            # 设置背景图片
            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(background_image))
            self.setPalette(palette)
            self.setAutoFillBackground(True)
        else:
            print(f"无法加载背景图片: {background_image_path}")

    def set_button_image(self, button, image_name):
        """设置按钮的背景图片，并等比缩小到25%"""
        # 构建图片路径
        image_path = resource_path(os.path.join("resources", image_name))
        
        # 检查图片是否存在
        if not os.path.exists(image_path):
            print(f"图片不存在: {image_path}")
            return

        # 加载图片
        image = QImage(image_path)
        if image.isNull():
            print(f"无法加载图片: {image_path}")
            return

        # 获取图片的原始宽度和高度
        original_width = image.width()
        original_height = image.height()

        # 计算25%的尺寸
        scaled_width = int(original_width * 0.25)
        scaled_height = int(original_height * 0.25)

        # 设置按钮大小
        button.setFixedSize(scaled_width, scaled_height)

        # 创建一个 QLabel 来显示图片
        label = QLabel(button)
        label.setPixmap(QPixmap.fromImage(image).scaled(scaled_width, scaled_height))
        label.setScaledContents(True)
        label.setGeometry(0, 0, scaled_width, scaled_height)

    def select_pet(self, pet_name):
        self.selected_pet = pet_name

    def select_two_pets(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("请选择你的CP")
        dialog.setGeometry(300, 300, 300, 200)

        # 创建复选框
        self.checkbox_queenie = QCheckBox("沐霂是MUMU呀", dialog)
        self.checkbox_yoyi = QCheckBox("又一充电中", dialog)
        self.checkbox_bekki = QCheckBox("恬豆发芽了", dialog)
        self.checkbox_lian = QCheckBox("梨安不迷路", dialog)

        # 创建按钮
        btn_ok = QPushButton("确定", dialog)

        # 为按钮设置统一的样式
        button_style = """
            background-color: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            text-align: center;
            font-size: 16px;
        """
        btn_ok.setStyleSheet(button_style)

        # 布局
        layout = QVBoxLayout()
        layout.addWidget(self.checkbox_queenie)
        layout.addWidget(self.checkbox_yoyi)
        layout.addWidget(self.checkbox_bekki)
        layout.addWidget(self.checkbox_lian)
        layout.addWidget(btn_ok)
        dialog.setLayout(layout)

        # 连接信号
        btn_ok.clicked.connect(lambda: self.create_two_pets(dialog))

        dialog.exec_()

    def create_two_pets(self, dialog):
        selected_pets = []
        if self.checkbox_queenie.isChecked():
            selected_pets.append(("Queenie", resource_path(os.path.join("resources", "Queenie"))))
        if self.checkbox_yoyi.isChecked():
            selected_pets.append(("Yoyi", resource_path(os.path.join("resources", "Yoyi"))))
        if self.checkbox_bekki.isChecked():
            selected_pets.append(("Bekki", resource_path(os.path.join("resources", "Bekki"))))
        if self.checkbox_lian.isChecked():
            selected_pets.append(("Lian", resource_path(os.path.join("resources", "Lian"))))

        if len(selected_pets) != 2:
            QMessageBox.warning(self, "警告", "请选择两位成员")
            return

        self.selected_pets = selected_pets
        dialog.close()

    def select_four_pets(self):
        self.selected_pets = [
            ("Bekki", resource_path(os.path.join("resources", "Bekki"))),
            ("Lian", resource_path(os.path.join("resources", "Lian"))),
            ("Yoyi", resource_path(os.path.join("resources", "Yoyi"))),
            ("Queenie", resource_path(os.path.join("resources", "Queenie")))
        ]

    def start_pets(self):
        if hasattr(self, 'selected_pet'):
            if self.selected_pet == "Bekki":
                pet = DesktopPet("Bekki", resource_path(os.path.join("resources", "Bekki")))
                pet.set_urls("https://live.bilibili.com/23771189/", "https://space.bilibili.com/1660392980/")
                self.pets = [pet]
            elif self.selected_pet == "Lian":
                pet = DesktopPet("Lian", resource_path(os.path.join("resources", "Lian")))
                pet.set_urls("https://live.bilibili.com/23770996/", "https://space.bilibili.com/1900141897/")
                self.pets = [pet]
            elif self.selected_pet == "Yoyi":
                pet = DesktopPet("Yoyi", resource_path(os.path.join("resources", "Yoyi")))
                pet.set_urls("https://live.bilibili.com/23771092/", "https://space.bilibili.com/1217754423/")
                self.pets = [pet]
            elif self.selected_pet == "Queenie":
                pet = DesktopPet("Queenie", resource_path(os.path.join("resources", "Queenie")))
                pet.set_urls("https://live.bilibili.com/23771139/", "https://space.bilibili.com/1878154667/")
                self.pets = [pet]
        elif hasattr(self, 'selected_pets'):
            self.pets = []
            for pet_name, pet_folder in self.selected_pets:
                pet = DesktopPet(pet_name, pet_folder)
                # 设置对应的直播间和个人主页链接
                if pet_name == "Bekki":
                    pet.set_urls("https://live.bilibili.com/23771189/", "https://space.bilibili.com/1660392980/")
                elif pet_name == "Lian":
                    pet.set_urls("https://live.bilibili.com/23770996/", "https://space.bilibili.com/1900141897/")
                elif pet_name == "Yoyi":
                    pet.set_urls("https://live.bilibili.com/23771092/", "https://space.bilibili.com/1217754423/")
                elif pet_name == "Queenie":
                    pet.set_urls("https://live.bilibili.com/23771139/", "https://space.bilibili.com/1878154667/")
                self.pets.append(pet)
        self.hide()

    def close_all_pets(self):
        for pet in self.pets:
            pet.quit()
        self.close()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    selector = PetSelector()
    selector.show()
    sys.exit(app.exec_())