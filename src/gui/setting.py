from typing import List, Any, Dict, Union

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QListWidget,
    QHBoxLayout,
    QTabWidget,
    QLabel, QPushButton,
    QListWidgetItem,
    QMessageBox
)
from loguru import logger

from plugins import plugin


class StartPluginThread(QThread):
    result = Signal(bool)
    def __init__(self, _callback: callable) -> None:
        """使用线程启动Plugin"""
        super().__init__()
        self.__callback = _callback

    def run(self) -> None:
        self.__callback()
        self.result.emit(True)


class PluginSettingWindow(QWidget):
    def __init__(self, parent=None) -> None:
        """plugin的设置界面"""
        super().__init__(parent)
        layout = QHBoxLayout(self)
        self.setLayout(layout)

        # plugin的列表
        self.loader: Union[plugin.pluginLoader, None] = None
        self.plugin_items: List[Dict[Any, plugin.plugin_dataType]] = []
        self.getPluginItems()
        self._callback: Union[plugin.pluginCallableType, None] = None
        self.pluginThread: Union[QThread, None] = None
        self.startPluginThread: Union[StartPluginThread, None] = None
        
        # 左侧列表
        self.pluginList = QListWidget()
        self.pluginList.itemClicked.connect(self.displayPluginDetails)
        self.populatePluginList()
        layout.addWidget(self.pluginList, 20)  # 分配左侧20%的空间
        
        # 右侧详情显示区
        self.detailsFrame = QWidget()
        self.detailsLayout = QVBoxLayout(self.detailsFrame)
        self.detailsLabel = QLabel()
        self.detailsLayout.addWidget(self.detailsLabel)
        layout.addWidget(self.detailsFrame, 80)  # 分配右侧80%的空间

    def initEvent(self) -> None:
        """Init event"""
        self.initAllPlugin()

    def initAllPlugin(self) -> None:
        """初始化所有plugin"""
        manager = plugin.pluginConfigManager()
        for plugin_item in self.plugin_items:
            for plugin_name, plugin_info in plugin_item.items():
                static = plugin_info.static
                if static is not None and static == 'on':
                    logger.info(f"setting将初始化plugin: {plugin_name}。")
                    self.onOrOffButton = QPushButton(plugin_info.static)
                    self.enableOrDisablePluginEvent(plugin_name)
    
    def getPluginItems(self):
        """获取所有plugin_items"""
        manager = plugin.pluginConfigManager()
        result = manager.readDataBypluginName()
        if result:
           self.plugin_items = result 
           logger.info(f"获取到的plugin_items: {self.plugin_items}")
    
    def populatePluginList(self):
        """填充plugin列表"""
        for plugin_item in self.plugin_items:
            for name in plugin_item.keys():
                list_item = QListWidgetItem(name)
                self.pluginList.addItem(list_item)

    def displayPluginDetails(self, item: QListWidgetItem):
        """显示选中plugin的详细信息"""
        # self.getPluginItems()   # 更新一下items内容
        logger.debug(f"显示选中plugin的详细信息: {item.text()}")
        for plugin_item in self.plugin_items:
            if item.text() not in plugin_item.keys():
                logger.debug(f"plugin_item not exist: {plugin_item}")
                continue
            self.setOnOrOffButtonEvent(text = item.text(), value = plugin_item[item.text()])
    
    def setOnOrOffButtonEvent(self, text: str, value: plugin.pluginDataType) -> None:
        """设置打开或改变按钮的事件"""
        static = "启用" if value.static == "off" else "关闭"
        self.startPluginThread = StartPluginThread(lambda: self.enableOrDisablePluginEvent(text))
        self.startPluginThread.result.connect(self.onOrOffButtonResultConnectEvent)
        self.updateDetails(value)
        if hasattr(self, "onOrOffButton"):
            self.onOrOffButton.deleteLater()
        self.onOrOffButton = QPushButton(static)
        self.onOrOffButton.clicked.connect(self.startPluginThread.start)
        self.detailsLayout.addWidget(self.onOrOffButton)
    
    def onOrOffButtonResultConnectEvent(self, result: bool) -> None:
        """
        onOrOffButton result connect event.
        :param result: bool 返回一个bool值用于判断是否启动成功
        :return None
        """
        message = QMessageBox()
        if not result:
            logger.error(f"plugin: {self.loader.plugin_name}, {self.onOrOffButton.text()}失败！")
            message.setText("失败！")
            message.setWindowTitle("Fail")
            message.setWindowIconText("Start plugin fail")
        else:
            message.setText("成功！")
            message.setWindowTitle("ok")
            message.setWindowIconText("Start plugin ok")
        message.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        message.exec()

    def enableOrDisablePluginEvent(self, plugin_name: str) -> None:
        """启用指定的plugin"""
        # 使用加载器加载plugin
        self.loader = plugin.pluginLoader(plugin_name)

        # 关闭plugin
        if self.onOrOffButton.text() == "关闭":
            if not self._callback:
                logger.warning(f"plugin: {plugin_name}没有停止！")
                return None
            if self.loader.getStaitc() is False:
                logger.warning(f"plugin: {plugin_name}未启用！")
                return None
            result = self._callback.stop()

            if not result:
                return None
            self.onOrOffButton.setText("启动")
            self.loader.off()
            self.loader.save()
            return None
        
        # 启用plugin
        self._callback: plugin.pluginCallableType = self.loader.on()
        if not self._callback:
            return None
        self._callback: plugin.pluginClassType = self._callback() # 将加载后的模块进行启动
        if self._callback is not None:
            self.pluginThread: QThread = self._callback.run()
            self.pluginThread.start()
            self.onOrOffButton.setText("关闭")
            self.loader.save()

    def updateDetails(self, plugin_data: plugin.pluginDataType):
        """更新右侧的详细信息显示"""
        logger.debug(f"更新右侧的详细信息显示: {plugin_data}")

        static = "启动" if plugin_data.static == "on" else "关闭"
        address = "\n\t".join(
            [key+':'+value for key, value in plugin_data.address.items() if value != "null"]
        )
        self.detailsLabel.setText(
            f"作者: {plugin_data.author}\n" +
            f"版本: {plugin_data.version}\n"+
            f"简介: {plugin_data.description}\n" +
            f"当前状态: {static}\n" + 
            f"开源地址: \n\t{address}" 
        )

class SettingsWidget(QWidget):
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
        self.thePluginSettingWindow = PluginSettingWindow()
        self.tabWidget.addTab(QWidget(), "基础")
        self.tabWidget.addTab(self.thePluginSettingWindow, "plugin")
