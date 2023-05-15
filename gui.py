from pathlib import Path
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QScrollArea
from PyQt6.QtWidgets import QWidget, QTabWidget, QGroupBox
from PyQt6.QtWidgets import QLineEdit, QPushButton, QFileDialog, QTextEdit, QFormLayout
from PyQt6.QtGui import QCloseEvent ,QPixmap
from PyQt6.QtCore import QSize, Qt
import logging
from pngFile import PngFile


class MainWindow(QWidget):
    def __init__(self):
        super(MainWindow, self).__init__()
        self.png_file : PngFile = None
        self.setWindowTitle("Emedia")
        self.setFixedHeight(720)
        self.setFixedWidth(720)
        self._createLayoutTab()

    def _createLayoutTab(self):
        layout = QGridLayout()
        self.setLayout(layout)

        label1 = self._layoutFile()

        test = QWidget()
        test.setLayout(label1)
        self.tabwidget = QTabWidget()
        self.tabwidget.addTab(test, "Image")

        self.tabwidget.addTab(self._chunksLayout(), "Chunks")

        layout.addWidget(self.tabwidget, 0, 0)


    def _layoutFile(self):
        layout = QGridLayout()
        label = QLabel("Png file")
        layout.addWidget(label, 0, 0)

        self.path_to_file = QLineEdit()
        self.path_to_file.setReadOnly(True)
        layout.addWidget(self.path_to_file, 0, 1, 1, 3)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.showDialog)
        layout.addWidget(browse_button, 0, 4)

        self.image_label = QLabel()
        layout.addWidget(self.image_label, 1, 0, 1, 5)

        return layout

    def _chunksLayout(self, png_file : PngFile = None):
        formLayout = QVBoxLayout()
        groupBox = QGroupBox()

        if png_file is None:
            label = QTextEdit("Image not loaded")
            formLayout.addWidget(label)
        else:
            for chunk in png_file.chunks:
                test = QGroupBox(chunk.type)
                chunksLayout = QVBoxLayout()
                label = QLabel(f"Length: {chunk.length}")
                chunksLayout.addWidget(label)

                if len(chunk.byte_data) > 20:
                    label = QLabel(f"Byte data: {chunk.byte_data[:20]}...")
                else:
                    label = QLabel(f"Byte data: {chunk.byte_data}")

                chunksLayout.addWidget(label)

                for key, value in chunk.data.items():
                    label = QLabel(f"{key}: {value}")
                    chunksLayout.addWidget(label)

                test.setLayout(chunksLayout)
                formLayout.addWidget(test)


        groupBox.setLayout(formLayout)

        scroll = QScrollArea()
        scroll.setWidget(groupBox)
        scroll.setWidgetResizable(True)
        return scroll
        # # layout = QVBoxLayout(self)
        # # layout.addWidget(scroll)
        # # return layout

    def _updateImgae(self, img_file):
        im = QPixmap(img_file)
        high_rez = QSize(600, 600)

        # self.image_label(im)
        im = im.scaled(high_rez)
        self.image_label.setPixmap(im)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)


    def showDialog(self):
        home_dir = str(Path().resolve())
        fname = QFileDialog.getOpenFileName(directory=home_dir)

        if not fname[0]:
            logging.error("error")
            return

        if fname[0].endswith(".png") is not True:
            logging.error("Invalid file format")
            return

        self.path_to_file.clear()
        self.path_to_file.insert(fname[0])
        logging.info(f"File {fname[0]}")
        self._updateImgae(fname[0])
        self.png_file = PngFile(fname[0])
        self.tabwidget.removeTab(1)

        self.tabwidget.addTab(self._chunksLayout(self.png_file), "Chunks")
