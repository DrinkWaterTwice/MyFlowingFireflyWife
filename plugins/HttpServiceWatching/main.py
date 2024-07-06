import os
import json

from loguru import logger
from PySide6.QtCore import Signal, QThread
from PySide6.QtWidgets import QWidget
import requests
from plugins.HttpServiceWatching.infoWindow import HttpWatchingWidget
from PySide6.QtGui import QPixmap, QAction



from requests.exceptions import Timeout, HTTPError, ConnectionError, RequestException



from plugin import pluginClassType
from src.gui.main import window

CONFIG_FILE_DIR = os.path.join(os.getcwd(), "data", "config", "http_watching.json")
# DATA_AUDIO_DIR = os.path.join(os.getcwd(), "data", "config", "audio")


class HttpServiceWatchingQThread(QThread):
    result = Signal(bool)

    def __init__(self) -> None:
        super().__init__(parent=None)
        self.requestInterruption: bool = False     # 用于请求停止服务

        self.http_watching_window = HttpWatchingWidget()
        self.http_watching_window.hide()
        config_action = QAction("我的", self)
        config_action.triggered.connect(self.showWindow)
        window.menu.addAction(config_action)
        logger.info("HttpServiceWatchingQThread初始化完成。")


    def showWindow(self):
        self.http_watching_window.show()



    def run(self) -> None:
        result = {}
        while not self.requestInterruption:
            with open(CONFIG_FILE_DIR, "r+", encoding="utf-8") as rfp:
                data = json.loads(rfp.read())
                if not data:
                    logger.warning(f"读取配置文件：{CONFIG_FILE_DIR}时，出现错误。")
            http_service_list = data.get("http_address")
            time_per_request = data.get("time_per_request")
            for key in http_service_list:
                response = self.sendRequest(key)
                result[key] = response
                # logger.debug(f"请求结果：{response}")
            self.http_watching_window.updateResult(result)
            self.sleep(time_per_request)


    def sendRequest(self, key: str) -> str:
        """
        通过key值对配置文件的服务器数据进行读取并发送请求。
        :param key: str 需要请求的服务器关键字
        :return 请求结果
        """
        with open(CONFIG_FILE_DIR, "r+", encoding="utf-8") as rfp:
            data = json.loads(rfp.read())
            if not data:
                logger.warning(f"读取配置文件：{CONFIG_FILE_DIR}时，出现错误。")
                return "服务器未响应"
        # 进行请求
        address = data.get("http_address").get(key, None)
        if not address:
            logger.warning(f"未找到服务器地址: {key}。")
            logger.debug(f"配置文件：{data}")
            return "配置文件中未找到服务器地址"

        try:
            response = requests.get(address)
            return response.text
        except Timeout:
            logger.warning("请求超时")
            return "请求超时"
        except HTTPError as http_err:
            logger.warning(f"HTTP错误发生: {http_err}")
            return f"HTTP错误发生: {http_err}"
        except ConnectionError:
            logger.warning("连接到服务器时出现问题")
            return "连接到服务器时出现问题"
        except RequestException as err:
            logger.warning(f"请求出现了问题: {err}")
            return f"请求出现了问题: {err}"
        




class Main(pluginClassType):
    def __init__(self) -> None:
        super().__init__()
        self.th = HttpServiceWatchingQThread()

    def run(self) -> QThread:
        return self.th

    def stop(self) -> bool:
        self.th.requestInterruption = True
        self.th.wait()
        return True

    def settingWindow(self) -> QWidget:
        pass
