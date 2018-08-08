#! /usr/bin/env python
# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtWidgets
import MainWindow

def main(argv):
    app = QtWidgets.QApplication(argv)
    mainWindow = MainWindow.MainWindow()
    mainWindow.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main(sys.argv)
