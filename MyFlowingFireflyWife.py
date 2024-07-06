import sys
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QAction
from src.gui import main



if __name__ == '__main__':
    app = QApplication(sys.argv)

    # 系统托盘图标
    trayIcon = QSystemTrayIcon(QIcon("data/assets/images/firefly/learn.png"), app)
    trayIcon.setToolTip("流萤小程序")
    trayMenu = QMenu()

    # 添加一个退出动作到托盘菜单
    exitAction = QAction("退出", app)
    exitAction.triggered.connect(app.quit)
    trayMenu.addAction(exitAction)



    trayIcon.setContextMenu(trayMenu)
    trayIcon.show()

    # GUI初始化
    main.logger.add("log\\latest.log", rotation="500 MB")
    mainWindow = main.main(app)  # 假设main.main(app)返回的是主窗口实例



    # 确保当主窗口关闭时，程序仍然在系统托盘运行
    mainWindow.closeEvent = lambda event: (event.ignore(), mainWindow.hide(), trayIcon.showMessage("Your App", "Your App is still running. Right-click the tray icon to exit."))

    # 双击托盘图标恢复窗口
    trayIcon.activated.connect(lambda reason: mainWindow.show() if reason == QSystemTrayIcon.ActivationReason.DoubleClick else None)

    sys.exit(app.exec())

