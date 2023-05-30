import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QLabel
from PyQt6.QtWidgets import QGridLayout, QHBoxLayout, QVBoxLayout, QScrollArea
from PyQt6.QtWidgets import QWidget, QTabWidget, QGroupBox, QMessageBox, QCheckBox
from PyQt6.QtWidgets import QLineEdit, QPushButton, QFileDialog, QTextEdit, QFormLayout
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import QSize, Qt
from pngFile import PngFile
import pyqtgraph as pg


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
        self.tabwidget.addTab(self._fftLayout(), "FFT")

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

        self.save_check_box_ancillary = QCheckBox("Remove ancillary chunks")
        layout.addWidget(self.save_check_box_ancillary, 1, 0, 1, 2)

        # self.save_text_status = QLabel("Test")
        # layout.addWidget(self.save_text_status, 1, 4)

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
                    if key == "Decoded data":
                        label = QLabel(f"{key}: {str(value)[:40]}...")
                    else:
                        label = QLabel(f"{key}: {value}")
                    chunksLayout.addWidget(label)


                if chunk.type == "PLTE":
                    plte_colors = chunk.get_RGB()
                    for i in range(len(plte_colors[0])):
                        color = (plte_colors[0][i], plte_colors[1][i], plte_colors[2][i])
                        label = QLabel(f"{color}")
                        chunksLayout.addWidget(label)
                        label = QLabel()
                        label.setStyleSheet(f"background-color: rgb{color};")
                        chunksLayout.addWidget(label)

                if chunk.type == "hIST":
                    test = QVBoxLayout()
                    histogram = chunk.get_histogram()
                    plte = png_file.get_chunk("PLTE")
                    brushes = []
                    plte_colors = plte.get_RGB()
                    for i, red in enumerate(plte_colors[0]):
                        brushes.append((red, plte_colors[1][i], plte_colors[2][i]))

                    # add histogram
                    plot = pg.plot()
                    bargraph = pg.BarGraphItem(x =  [i for i in range(len(histogram))], height = histogram, width = 0.6, brushes = brushes)
                    plot.addItem(bargraph)
                    chunksLayout.addWidget(plot)

                box.setLayout(chunksLayout)
                formLayout.addWidget(box)
                self.list_of_chunk_box.append(box)


        groupBox.setLayout(formLayout)

        scroll = QScrollArea()
        scroll.setWidget(groupBox)
        scroll.setWidgetResizable(True)
        return scroll

    def __createPlot(self, title: str, data):
        graphWidget = pg.PlotWidget()

        graphWidget.setLabel("left", "test")
        graphWidget.setLabel("bottom", "Frequency", "Hz")
        graphWidget.setTitle(title)
        graphWidget.showGrid(True, True, 0.5)
        graphWidget.setBackground((30, 30, 30))

        # if title.endswith("Green"):
        #     color = (0, 255, 0)
        # elif title.endswith("Blue"):
        #     color = (0, 0, 255)
        # else:
        #     color = (255, 0, 0)

        # pen = pg.mkPen(color=color, width = 3)
        graphWidget.plot(data)

        return graphWidget

    def __createImageFFT(self, title: str, data):
        plot = pg.PlotItem()
        plot.setTitle(title)

        imv = pg.ImageView(view = plot)
        imv = pg.ImageView()
        imv.setImage(data)
        print(data)
        imv.ui.histogram.hide()
        imv.ui.roiBtn.hide()
        imv.ui.menuBtn.hide()

        return imv

    def _fftLayout(self, png_file : PngFile = None):
        """Create chunks layout"""
        formLayout = QVBoxLayout()
        groupBox = QGroupBox()

        self.list_of_chunk_box = []

        if png_file is None:
            label = QTextEdit("Image not loaded")
            formLayout.addWidget(label)
        else:
            fft_list = self.png_file.get_fft()
            fft_titles = ["FFT maginitude", "FFT phase"]

            for i, fft_data in enumerate(fft_list):
                fft_plot_widget = self.__createImageFFT(fft_titles[i], fft_data)
                formLayout.addWidget(fft_plot_widget)

        groupBox.setLayout(formLayout)

        scroll = QScrollArea()
        scroll.setWidget(groupBox)
        scroll.setWidgetResizable(True)
        return scroll

    def _updateImgae(self, img_file):
        """Update image in file layout"""
        im = QPixmap(img_file)
        high_rez = QSize(550, 550)

        im = im.scaled(high_rez)
        self.image_label.setPixmap(im)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)


    def openFileShowDialog(self):
        """Open file dialog window"""
        home_dir = str(Path().resolve())
        fname = QFileDialog.getOpenFileName(directory=home_dir)

        if not fname[0]:
            return

        if fname[0].endswith(".png") is not True:
            logging.error("Invalid file format")
            QMessageBox.warning(self, "Invalid file format", "File should end with .png")
            return

        self.path_to_file.clear()
        self.path_to_file.insert(fname[0])
        logging.info(f"File {fname[0]}")

        self.png_file = PngFile(fname[0])
        # try:
        #     self.png_file = PngFile(fname[0])
        # except Exception as e: print("diiii %s", e)
           # QMessageBox.critical(self, "Error", "Error during file encoding")
           # return
        self._updateImgae(fname[0])
        try:
            self.png_file = PngFile(fname[0])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Error during file encodinn:\n{str(e)}")
            return

        self.tabwidget.removeTab(2)
        self.tabwidget.removeTab(1)
        self.save_file_button.setDisabled(False)
        self.tabwidget.addTab(self._chunksLayout(self.png_file), "Chunks")
        self.tabwidget.addTab(self._fftLayout(self.png_file), "FFT")

        self.save_file_button.setEnabled(True)

    def _save_only_critical_chunks(self, file):
            for chunk in self.png_file.chunks:
                if chunk.is_critical() is True:
                    file.write(chunk.create_chunk())

    def _save_choosen_chunks(self, file):
        itter = 0
        for chunk in self.png_file.chunks:
            if chunk.is_critical() is True:
                file.write(chunk.create_chunk())
            else:
                if self.list_of_chunk_box[itter].isChecked():
                    file.write(chunk.create_chunk())

            itter += 1

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

        if self.save_check_box_ancillary.isChecked() is True:
            self._save_only_critical_chunks(file)
        else:
            self._save_choosen_chunks(file)

        file.close()




