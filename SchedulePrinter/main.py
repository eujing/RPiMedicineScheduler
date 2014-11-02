import sys
from PyQt4 import QtGui, QtCore
import pyqrcode
import json
if sys.platform == "win32":
    import win32print
    import win32ui
from PIL import Image, ImageWin
import subprocess


class Window(QtGui.QWidget):

    def __init__(self, x, y, w, h, title):
        super(Window, self).__init__()

        self.initUI()
        self.setGeometry(x, y, w, h)
        self.setWindowTitle(title)

    def addButton(self, text, x, y, callback, tooltip=""):
        b = QtGui.QPushButton(text, self)
        b.setToolTip(tooltip)
        b.resize(b.sizeHint())
        b.move(x, y)
        b.clicked.connect(callback)

    def initUI(self):
        grid = QtGui.QGridLayout()
        grid.setSpacing(10)

        lName = QtGui.QLabel("Name")
        lDosage = QtGui.QLabel("Dosage")
        lSlot = QtGui.QLabel("Slot")
        lHours = QtGui.QLabel("Hours")
        lDays = QtGui.QLabel("Days")
        lSpecial = QtGui.QLabel("Special")
        self.image = QtGui.QLabel()

        self.eName = QtGui.QLineEdit()
        self.eDosage = QtGui.QLineEdit()
        self.eSlot = QtGui.QComboBox()
        self.eSlot.addItems([str(i) for i in range(4)])
        self.eHours = QtGui.QLineEdit()
        self.eDays = QtGui.QLineEdit()
        self.eSpecial = QtGui.QLineEdit()

        bGenerate = QtGui.QPushButton("Generate")
        bPrint = QtGui.QPushButton("Print")

        grid.addWidget(lName, 1, 0)
        grid.addWidget(self.eName, 1, 1, 1, 3)
        grid.addWidget(lDosage, 2, 0)
        grid.addWidget(self.eDosage, 2, 1, 1, 3)
        grid.addWidget(lSlot, 3, 0)
        grid.addWidget(self.eSlot, 3, 1, 1, 3)
        grid.addWidget(lHours, 4, 0)
        grid.addWidget(self.eHours, 4, 1, 1, 3)
        grid.addWidget(lDays, 5, 0)
        grid.addWidget(self.eDays, 5, 1, 1, 3)
        grid.addWidget(lSpecial, 6, 0)
        grid.addWidget(self.eSpecial, 6, 1, 1, 3)
        grid.addWidget(bGenerate, 7, 2, 1, 2)
        grid.addWidget(bPrint, 7, 4, 1, 2)
        grid.addWidget(self.image, 1, 4, 6, 6)

        self.setLayout(grid)

        bGenerate.clicked.connect(self.generateQR)
        bPrint.clicked.connect(self.printQR)

    def setImage(self, fileName):
        pic = QtGui.QPixmap(fileName)
        pic = pic.scaled(self.image.size(), QtCore.Qt.KeepAspectRatio)
        self.image.setPixmap(pic)

    def generateQR(self):
        data = {
            "name": str(self.eName.text()),
            "slot": int(self.eSlot.currentText()),
            "dosage": str(self.eDosage.text()),
            "hour": str(self.eHours.text())
        }
        if self.eSpecial.text() != "":
            data["special"] = str(self.eSpecial.text())
        qrImage = pyqrcode.MakeQRImage(json.dumps(data), errorCorrectLevel=pyqrcode.QRErrorCorrectLevel.M)
        qrImage.save("tmp.jpg")
        self.setImage("tmp.jpg")

    def printQR(self):
        if sys.platform == "win32":
            HORZRES = 8
            VERTRES = 10

            LOGPIXELSX = 88
            LOGPIXELSY = 90

            PHYSICALWIDTH = 110
            PHYSICALHEIGHT = 111

            PHYSICALOFFSETX = 112
            PHYSICALOFFSETY = 113

            printer_name = win32print.GetDefaultPrinter()
            file_name = "tmp.jpg"

            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)
            printable_area = hDC.GetDeviceCaps(
                HORZRES), hDC.GetDeviceCaps(VERTRES)
            printer_size = hDC.GetDeviceCaps(
                PHYSICALWIDTH), hDC.GetDeviceCaps(PHYSICALHEIGHT)
            printer_margins = hDC.GetDeviceCaps(
                PHYSICALOFFSETX), hDC.GetDeviceCaps(PHYSICALOFFSETY)

            bmp = Image.open(file_name)
            if bmp.size[0] > bmp.size[1]:
                bmp = bmp.rotate(90)

            ratios = [1.0 * printable_area[0] / bmp.size[0],
                      1.0 * printable_area[1] / bmp.size[1]]
            scale = min(ratios)

            hDC.StartDoc(file_name)
            hDC.startPage()

            dib = ImageWin.Dib(bmp)
            scaled_width, scaled_height = [int(scale * i) for i in bmp.size]
            x1 = int((printer_size[0] - scaled_width) / 2)
            y1 = int((printer_size[1] - scaled_height) / 2)
            x2 = x1 + scaled_width
            y2 = y1 + scaled_height
            dib.draw(hDC.GetHandleOutput(), (x1, y1, x2, y2))

            hDC.EndPage()
            hDC.EndDoc()
            hDC.DeleteDC()

        elif sys.platform == "linux2":
            subprocess.Popen(["lpr", "tmp.jpg"])


def main():
    app = QtGui.QApplication(sys.argv)
    win = Window(100, 100, 450, 240, "Schedule Printer")

    win.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
