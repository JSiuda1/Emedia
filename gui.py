import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QScrollArea
from PyQt6.QtWidgets import QWidget, QTabWidget, QGroupBox, QMessageBox
from PyQt6.QtWidgets import QLineEdit, QPushButton, QFileDialog, QTextEdit, QFormLayout
from PyQt6.QtGui import QCloseEvent ,QPixmap
from PyQt6.QtCore import QSize, Qt
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
        """Create layout with tab"""
        layout = QGridLayout()
        self.setLayout(layout)

        label1 = self._layoutFile()

        test = QWidget()
        test.setLayout(label1)
        self.tabwidget = QTabWidget()
        self.tabwidget.addTab(test, "Image")

        self.tabwidget.addTab(self._chunksLayout(), "Chunks")

        layout.addWidget(self.tabwidget, 0, 0)
        layout.addWidget(self._layoutSaveFile(), 1, 0)

    def _layoutSaveFile(self):
        """Create save file layout"""
        layout = QGridLayout()
        box = QGroupBox()
        label = QLabel("File name")
        layout.addWidget(label, 0, 0)

        self.save_file_name = QLineEdit()
        layout.addWidget(self.save_file_name, 0, 1, 1, 3)

        self.save_file_button = QPushButton("Save")
        self.save_file_button.setDisabled(True)
        self.save_file_button.clicked.connect(self.saveImage)
        layout.addWidget(self.save_file_button, 0, 4)

        box.setLayout(layout)

        return box

    def _layoutFile(self):
        """Create file layout"""
        layout = QGridLayout()
        label = QLabel("Png file")
        layout.addWidget(label, 0, 0)

        self.path_to_file = QLineEdit()
        self.path_to_file.setReadOnly(True)
        layout.addWidget(self.path_to_file, 0, 1, 1, 3)

        browse_button = QPushButton("Browse")
        browse_button.clicked.connect(self.openFileShowDialog)
        layout.addWidget(browse_button, 0, 4)

        self.image_label = QLabel()
        layout.addWidget(self.image_label, 1, 0, 1, 5)

        return layout

    def _chunksLayout(self, png_file : PngFile = None):
        """Create chunks layout"""
        formLayout = QVBoxLayout()
        groupBox = QGroupBox()

        self.list_of_chunk_box = []

        if png_file is None:
            label = QTextEdit("Image not loaded")
            formLayout.addWidget(label)
        else:
            for chunk in png_file.chunks:
                box = QGroupBox(chunk.type)

                chunksLayout = QVBoxLayout()

                if chunk.is_critical() is True:
                    label = QLabel(f"Chunk type: Critical")
                else:
                    label = QLabel(f"Chunk type: Ancillary")
                    box.setCheckable(True)

                chunksLayout.addWidget(label)

                label = QLabel(f"Length: {chunk.chunk_length}")
                chunksLayout.addWidget(label)

                if len(chunk.byte_data) > 20:
                    label = QLabel(f"Byte data: {chunk.byte_data[:20]}...")
                else:
                    label = QLabel(f"Byte data: {chunk.byte_data}")

                chunksLayout.addWidget(label)

                for key, value in chunk.data.items():
                    label = QLabel(f"{key}: {value}")
                    chunksLayout.addWidget(label)

                box.setLayout(chunksLayout)
                formLayout.addWidget(box)
                self.list_of_chunk_box.append(box)


        groupBox.setLayout(formLayout)

        scroll = QScrollArea()
        scroll.setWidget(groupBox)
        scroll.setWidgetResizable(True)
        return scroll
        # # layout = QVBoxLayout(self)
        # # layout.addWidget(scroll)
        # # return layout

    def _updateImgae(self, img_file):
        """Update image in file layout"""
        im = QPixmap(img_file)
        high_rez = QSize(600, 600)

        # self.image_label(im)
        im = im.scaled(high_rez)
        self.image_label.setPixmap(im)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)


    def openFileShowDialog(self):
        """Open file dialog window"""
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
        self.save_file_button.setDisabled(False)

        self.tabwidget.addTab(self._chunksLayout(self.png_file), "Chunks")

        self.save_file_button.setEnabled(True)


    def saveImage(self):
        """On save image button"""
        path = os.path.join('output', f"{self.save_file_name.text()}.png")
        logging.info("Saving to %s", path)

        if os.path.isfile(path) is True:
            choice = QMessageBox.question(
                self,
                "File exists",
                f"Do you want to overwrite file {self.save_file_name.text()}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

            if choice == QMessageBox.StandardButton.No:
                print("Abort")
                return

        file = open(path, "wb")
        file.write(self.png_file.HEADER)
        itter = 0
        for chunk in self.png_file.chunks:
            if chunk.is_critical() is True:
                file.write(chunk.create_chunk())
            else:
                if self.list_of_chunk_box[itter].isChecked():
                    file.write(chunk.create_chunk())

            itter += 1

        file.close()




