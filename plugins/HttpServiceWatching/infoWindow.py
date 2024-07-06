from typing import List, Any, Dict, Union
import json, os
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QHBoxLayout,
    QTabWidget,
    QLabel, QPushButton,
    QListWidgetItem,
    QMessageBox,
    QScrollArea,
    QDialog,
    QLineEdit
)



from loguru import logger

from plugins import plugin



class HttpWatchingWindow(QWidget):
    def __init__(self, parent=None) -> None:
        """plugin的设置界面"""
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.setLayout(layout)
        self.http_service_list = None
        self.http_service_result = None
        self.config = {}

        # 创建一个垂直子布局用于防止左侧列表和左侧按钮控件
        left_layout = QVBoxLayout()
        layout.addLayout(left_layout, 20)
        
        # 左侧列表
        self.address_list = QListWidget()
        self.address_list.itemClicked.connect(self.displayHttpServiceDetails)
        # layout.addWidget(self.address_list, 20)  # 分配左侧20%的空间
        left_layout.addWidget(self.address_list)


        
        # 底部增加一个按钮

        self.create_button = QPushButton("新增")
        self.create_button.clicked.connect(self.createHttpService)
        self.remove_button = QPushButton("删除")
        self.remove_button.clicked.connect(lambda: self.removeHttpService(self.address_list.currentItem().text()))
        left_layout.addWidget(self.create_button)
        left_layout.addWidget(self.remove_button)
        
        # 设置样式
        self.address_list.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0; /* 背景颜色 */
                color: #333; /* 文本颜色 */
            }
            QListWidget::item {
                text-align: center; /* 设置文本居中 */
                padding: 5px; /* 设置填充 */
                
            }
            QListWidget::item:selected {
                background-color: #589df6; /* 选中项的背景颜色 */
                color: white; /* 选中项的文本颜色 */
            }
        """)

        
        # 右侧详情显示区
        self.detailsFrame = QWidget()
        self.detailsLayout = QVBoxLayout(self.detailsFrame)
        self.detailsLabel = QLabel()
        self.detailsLayout.addWidget(self.detailsLabel)
        
        # 创建滚动区域并设置其内容为detailsFrame
        self.scrollArea = QScrollArea()
        self.scrollArea.setWidgetResizable(True)  # 允许滚动区域自适应内容大小
        self.scrollArea.setWidget(self.detailsFrame)  # 设置滚动区域的内容
        
        layout.addWidget(self.scrollArea, 80)  # 分配右侧80%的空间，使用滚动区域代替直接使用detailsFrame
        
        self.loadConfig()
        self.address_list.addItems(self.http_service_list)

    def loadConfig(self):
        config_file_dir = os.path.join(os.getcwd(), "data", "config", "http_watching.json")
        with open(config_file_dir, "r+", encoding="utf-8") as rfp:
            data = json.loads(rfp.read())
            if not data:
                logger.warning(f"读取配置文件：{config_file_dir}时，出现错误。")
        self.http_service_list = data.get("http_address")
        self.config = data
        # 初始化http_result列表的值
        self.http_service_result = {}
        for key in self.http_service_list:
            self.http_service_result[key] = "未知"

    def createHttpService(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("创建HTTP服务")
        layout = QVBoxLayout(dialog)

        # 名称输入
        nameLabel = QLabel("名称:", dialog)
        nameInput = QLineEdit(dialog)
        layout.addWidget(nameLabel)
        layout.addWidget(nameInput)

        # URL输入
        urlLabel = QLabel("URL:", dialog)
        urlInput = QLineEdit(dialog)
        layout.addWidget(urlLabel)
        layout.addWidget(urlInput)

        # 创建按钮
        createButton = QPushButton("创建", dialog)
        layout.addWidget(createButton)
        createButton.clicked.connect(lambda: self.addHttpService(nameInput.text(), urlInput.text(), dialog))

        dialog.setLayout(layout)
        dialog.exec_()

    def addHttpService(self, name, url, dialog):
        if not name or not url:
            QMessageBox.warning(self, "警告", "名称和URL不能为空！")
            return
        self.config["http_address"][name] = url
        with open(os.path.join(os.getcwd(), "data", "config", "http_watching.json"), "w+", encoding="utf-8") as wfp:
            wfp.write(json.dumps(self.config))
        self.http_service_list[name] = url
        self.address_list.addItem(name)
        self.http_service_result[name] = "未知"

        # 排序
        self.address_list.sortItems()
        

        dialog.accept()

    def removeHttpService(self, name):
        if not name:
            return
        logger.debug(f"删除{name}")
        logger.debug(f"删除前：{self.config}")
        self.config["http_address"].pop(name)

    
        with open(os.path.join(os.getcwd(), "data", "config", "http_watching.json"), "w+", encoding="utf-8") as wfp:
            wfp.write(json.dumps(self.config))
        self.address_list.takeItem(self.address_list.currentRow())
        self.http_service_result.pop(name)

        
    def displayHttpServiceDetails(self, item: QListWidgetItem):
        """
        显示http服务的详细信息
        :param item: QListWidgetItem
        """
        if not item:
            return 
        self.detailsLabel.setText(self.http_service_result.get(item.text(), "未知"))
class HttpWatchingWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        self.setLayout(layout)
        self.setWindowTitle("设置")
        self.resize(600, 400)
        
        # 创建一个QTabWidget用于管理左右两侧布局
        self.tabWidget = QTabWidget()
        layout.addWidget(self.tabWidget)
        
        # 选项菜单
        self.thePluginSettingWindow = HttpWatchingWindow()
        
        self.tabWidget.addTab(self.thePluginSettingWindow, "http")
        self.tabWidget.addTab(QWidget(), "基础")
        logger.info("HttpWatchingWidget初始化完成。")

    def updateResult(self, result: dict):
        self.thePluginSettingWindow.http_service_result = result
        self.thePluginSettingWindow.displayHttpServiceDetails(self.thePluginSettingWindow.address_list.currentItem())
        # logger.debug(f"更新结果：{result}")