"""PyQt5 entrypoint wrapping qt_main for a single main file to run."""
import sys
from PyQt5.QtWidgets import QTableWidget, QTableWidgetItem,QApplication
from qt_main import MainWindow
from PyQt5.QtGui import QFont


def main():
    app = QApplication(sys.argv)
    app.setFont(QFont('Tahoma', 9))
    w = MainWindow()
    w.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()