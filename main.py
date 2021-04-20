import sys
from PyQt5.QtWidgets import QApplication,QMainWindow
from view.mainWin import win
import quamash,asyncio

if __name__ == '__main__':
    app = QApplication(sys.argv)
    with quamash.QEventLoop(app) as loop: 
        asyncio.set_event_loop(loop)
        mWin = win(loop)
        mWin.show()
        loop.run_forever()
    sys.exit(app.exec_())