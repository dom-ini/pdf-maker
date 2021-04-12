from typing import List, Union
from datetime import datetime
from pathlib import Path

from PIL import Image
from PyPDF2 import PdfFileMerger, PdfFileReader
from PyQt5.QtCore import Qt, QAbstractAnimation, QVariantAnimation, QEvent
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

import resources


class AnimatedPushButton(QPushButton):
    """
    Custom class for QPushButton, created for transition effect on hover
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation = QVariantAnimation(
            startValue=QColor("#0069d9"),
            endValue=QColor("#007bff"),
            valueChanged=self.update_stylesheet,
            duration=150,
        )
        self.setCursor(QCursor(Qt.PointingHandCursor))

    def update_stylesheet(self, color: QColor) -> None:
        self.setStyleSheet('QPushButton{ background-color: %s;}' % (color.name()))

    def enterEvent(self, event: QEvent) -> None:
        self.animation.setDirection(QAbstractAnimation.Backward)
        self.animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event: QEvent) -> None:
        self.animation.setDirection(QAbstractAnimation.Forward)
        self.animation.start()
        super().leaveEvent(event)


class PDFMaker(QWidget):
    """
    Main application
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        # variables for testing purposes
        self.testingMode = False
        self.baseDir = Path(__file__).parent.absolute()

        self.IMG_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.tif'}

        self.chosenFiles = []  # used for storing paths to files to be converted/merged
        self.outputDir = None

        self.initUI()
        self.createActions()
        self.connectSignals()

    def initUI(self) -> None:
        """
        Sets up the layout
        """
        self.toolBar = QToolBar()

        self.filesList = QListWidget()
        self.filesList.setContextMenuPolicy(Qt.ActionsContextMenu)
        self.filesList.setDragEnabled(True)
        self.filesList.setDefaultDropAction(Qt.MoveAction)
        self.filesList.setDragDropOverwriteMode(False)
        self.filesList.setDragDropMode(QAbstractItemView.InternalMove)
        self.filesList.setSelectionMode(QAbstractItemView.ExtendedSelection)

        self.chooseFilesPush = AnimatedPushButton('Choose files...')
        self.chooseFilesLine = QLineEdit('No Files Selected')
        self.chooseFilesLine.setReadOnly(True)
        self.chooseFilesLine.setFocusPolicy(Qt.NoFocus)

        self.optimizeSizeCheck = QCheckBox('Optimize file size')

        self.outputLabel = QLabel('Output directory:')
        self.outputLine = QLineEdit()
        self.outputLine.setReadOnly(True)
        self.outputLine.setFocusPolicy(Qt.NoFocus)
        self.outputPush = AnimatedPushButton('Browse...')

        self.customNameCheck = QCheckBox('Custom file name')
        self.customNameLine = QLineEdit()
        self.customNameLine.setDisabled(True)

        self.makePDFPush = AnimatedPushButton('Convert to PDF')

        self.progressBar = QProgressBar()
        self.progressBar.setHidden(True)

        selectedLayout = QHBoxLayout()
        selectedLayout.addWidget(self.chooseFilesLine)
        selectedLayout.addWidget(self.chooseFilesPush)

        outputLayout = QHBoxLayout()
        outputLayout.addWidget(self.outputLabel)
        outputLayout.addWidget(self.outputLine)
        outputLayout.addWidget(self.outputPush)

        customNameLayout = QHBoxLayout()
        customNameLayout.addWidget(self.customNameCheck)
        customNameLayout.addWidget(self.customNameLine)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.toolBar)
        mainLayout.addWidget(self.filesList)
        mainLayout.addLayout(selectedLayout)
        mainLayout.addWidget(self.optimizeSizeCheck)
        mainLayout.addLayout(outputLayout)
        mainLayout.addLayout(customNameLayout)
        mainLayout.addWidget(self.makePDFPush)
        mainLayout.addWidget(self.progressBar)

        # window settings
        self.setLayout(mainLayout)
        self.setFixedSize(500, 500)
        self.setWindowTitle('PDF Maker')
        self.setWindowIcon(QIcon(':icon.svg'))
        with open('style/main.qss') as f:
            self.setStyleSheet(f.read())
        self.show()

    def createActions(self) -> None:
        """
        Sets up actions for manipulating the order of chosen files
        """
        self.moveDownAction = QAction(QIcon(':goDown.svg'), 'Move Down', self)
        self.moveToBottomAction = QAction(QIcon(':goToBottom.svg'), 'Move To Bottom', self)
        self.moveUpAction = QAction(QIcon(':goUp.svg'), 'Move Up', self)
        self.moveToTopAction = QAction(QIcon(':goToTop.svg'), 'Move To Top', self)
        self.addItemAction = QAction(QIcon(':addItem.svg'), 'Add', self)
        self.deleteItemAction = QAction(QIcon(':deleteItem.svg'), 'Delete', self)

        actions = [self.moveToTopAction, self.moveUpAction, self.moveDownAction, self.moveToBottomAction,
                   self.addItemAction, self.deleteItemAction]

        # separator between move buttons and delete button
        separator = QAction(self)
        separator.setSeparator(True)

        # populate toolbar and context menu
        for action in actions:
            if action == self.addItemAction:
                self.toolBar.addSeparator()
                self.filesList.addAction(separator)
            self.toolBar.addAction(action)
            self.filesList.addAction(action)

        # keyboard shortcuts
        self.moveDownAction.setShortcut('Alt+Down')
        self.moveToBottomAction.setShortcut('Alt+Shift+Down')
        self.moveUpAction.setShortcut('Alt+Up')
        self.moveToTopAction.setShortcut('Alt+Shift+Up')
        self.addItemAction.setShortcut('Insert')
        self.deleteItemAction.setShortcut('Delete')

    def connectSignals(self) -> None:
        """
        Connects actions with functions
        """
        self.chooseFilesPush.clicked.connect(self.chooseFilesHandler)
        self.outputPush.clicked.connect(self.chooseOutputDir)
        self.makePDFPush.clicked.connect(self.makePDF)

        self.moveDownAction.triggered.connect(
            lambda: self.moveItem(self.filesList.selectedItems(), down_direction=True)
        )
        self.moveToBottomAction.triggered.connect(
            lambda: self.moveItem(self.filesList.selectedItems(), down_direction=True, to_edge=True)
        )
        self.moveUpAction.triggered.connect(
            lambda: self.moveItem(self.filesList.selectedItems(), down_direction=False)
        )
        self.moveToTopAction.triggered.connect(
            lambda: self.moveItem(self.filesList.selectedItems(), down_direction=False, to_edge=True)
        )
        self.deleteItemAction.triggered.connect(lambda: self.deleteItem(self.filesList.selectedItems()))
        self.addItemAction.triggered.connect(self.addItem)

        self.customNameCheck.stateChanged.connect(self.customNameEnable)

    def customNameEnable(self):
        """
        Enables the custom name line edit if corresponding checkbox is ticked
        """
        enable = True if self.customNameCheck.isChecked() else False
        self.customNameLine.setEnabled(enable)

    def moveItem(self, items: List[QListWidgetItem], down_direction: bool, to_edge: bool = False) -> None:
        """
        Allows to move items in ListWidget up and down

        :param items: list of currently selected items
        :param down_direction: True if the items are to be moved down, False if up
        :param to_edge: True if the items are to be moved to the top/bottom, False if they are to be moved by only one
        index
        """
        if not items:
            return
        # list of row numbers of corresponding items
        rows = [self.filesList.indexFromItem(item).row() for item in items]
        rows.sort(reverse=down_direction)
        rowCount = self.filesList.count()

        # if the items are already at the edge, don't move them further in that direction
        if (rows[0] >= rowCount - 1 and down_direction) or (rows[0] <= 0 and not down_direction):
            return
        for i, row in enumerate(rows):
            item = self.filesList.takeItem(row)
            if i == 0:
                itemToScroll = item
            if not to_edge:
                # move item(s) by one index
                if down_direction:
                    self.filesList.insertItem(row + 1, item)
                else:
                    self.filesList.insertItem(row - 1, item)
            else:
                # move item(s) to bottom/top
                if down_direction:
                    self.filesList.insertItem(rowCount - i - 1, item)
                else:
                    self.filesList.insertItem(0 + i, item)
            item.setSelected(True)
        else:
            self.filesList.scrollToItem(itemToScroll)

    def deleteItem(self, items: List[QListWidgetItem]) -> None:
        """
        Deletes given items from ListWidget and from paths' list

        :param items: items to be deleted
        """
        if not items:
            return
        itemsToDelete = []
        for item in items:
            itemsToDelete.append(item.text())
            self.filesList.takeItem(self.filesList.row(item))
        self.chosenFiles = list(filter(lambda x: x.name not in itemsToDelete, self.chosenFiles))
        self.updateFilesLabel()
        itemsToDelete.clear()

    def addItem(self) -> None:
        """
        Adds items chosen from file dialog to ListWidget and to paths' list
        """
        if not self.chosenFiles:
            return self.chooseFilesHandler()
        if self.chosenFiles[0].suffix.lower() == '.pdf':
            filtr = 'PDF Files (*.pdf)'
        elif self.chosenFiles[0].suffix.lower() in self.IMG_EXTENSIONS:
            filtr = 'Image Files (*.png *.jpg *.jpeg *.tif)'
        else:
            filtr = None
        if not filtr:
            return
        filenames = self.chooseFilesDialog(filtr=filtr)
        for file in filenames:
            path = Path(file)
            self.chosenFiles.append(path)
            self.filesList.addItem(QListWidgetItem(path.name))
        self.updateFilesLabel()

    def chooseFilesDialog(self, filtr: str = '') -> List[str]:
        """
        Allows the user to pick the files with the file dialog

        :param filtr: which files extensions should be available to pick
        :return: list of paths to chosen files
        """
        if not self.testingMode:
            filenames, filter_ = QFileDialog.getOpenFileNames(self, caption='Choose files', filter=filtr)
        else:
            # for testing purposes, the file dialog is omitted
            filenames = list(self.baseDir.joinpath(f'test_files/png').glob('*.png'))
        return filenames

    def chooseFilesHandler(self) -> None:
        """
        Main handler for selecting files - adds them to ListWidget and filepaths' list
        """
        self.filesList.clear()
        filenames = self.chooseFilesDialog(filtr='Image Files (*.png *.jpg *.jpeg *.tif);;PDF Files (*.pdf)')
        self.chosenFiles = [Path(x) for x in filenames]
        self.updateFilesLabel()
        self.filesList.addItems(list(map(lambda x: x.name, self.chosenFiles)))  # populate ListWidget

        if self.chosenFiles and self.chosenFiles[0].suffix.lower() == '.pdf':  # if only pdf files are selected
            self.makePDFPush.setText('Join PDFs')
            self.optimizeSizeCheck.setHidden(True)
        else:
            self.makePDFPush.setText('Convert to PDF')
            self.optimizeSizeCheck.setHidden(False)

    def updateFilesLabel(self) -> None:
        """
        Change text on selected files' LineEdit depending on the number of chosen files
        """
        if not self.chosenFiles:
            selectedFilesText = 'No Files Selected'
        elif len(self.chosenFiles) > 1:
            selectedFilesText = f'{len(self.chosenFiles)} Files Selected'
        else:
            selectedFilesText = f'Selected: {self.chosenFiles[0].name}'
        self.chooseFilesLine.setText(selectedFilesText)

    def chooseOutputDir(self) -> None:
        """
        Allows the user to pick the output directory of created file
        """
        directory = QFileDialog.getExistingDirectory(caption='Choose output directory')
        self.outputDir = Path(directory) if directory else None
        self.outputLine.setText(directory)

    def makePDF(self) -> Union[None, int]:
        """
        Main handler for PDF creating

        :return: the result of MessageBox execution
        """
        hasCustomName = self.customNameCheck.isChecked()
        customName = self.customNameLine.text().strip()
        if not self.chosenFiles:
            return self.showMessageBox('No files were selected!', is_error=True)
        elif not self.outputDir:
            return self.showMessageBox('Output directory were not specified!', is_error=True)
        elif hasCustomName and customName and self.outputDir.joinpath(f'{customName}.pdf').exists():
            return self.showMessageBox('File already exists!', is_error=True)
        self.orderFiles()
        # if custom name checkbox is ticked, but name is not given, it will give the default one
        filename = f'{customName}.pdf' if hasCustomName and customName \
            else f'pdf-maker-{datetime.now().strftime("%Y-%m-%d %H%M%S%f")}.pdf'
        savePath = self.outputDir.joinpath(filename)

        # extension validation is already performed during file choosing, this is additional
        if self.chosenFiles[0].suffix.lower() in self.IMG_EXTENSIONS:
            self.imageToPDF(savePath)
        elif self.chosenFiles[0].suffix.lower() == '.pdf':
            self.joinPDFs(savePath)
        self.resetProgressBar()

    def imageToPDF(self, savePath: Path) -> Union[None, int]:
        """
        Merges images and converts them to PDF file

        :param savePath: path to where the file is to be created
        :return: the result of MessageBox execution
        """
        self.progressBar.setHidden(False)

        MAX_DIM = 2000  # used when checkbox to optimize file size is ticked, it's the maximal dimension image can have
        pages = []  # list to store converted images, used further for saving them into one file
        for i, file in enumerate(self.chosenFiles, start=1):
            try:
                with Image.open(file) as img:
                    if self.optimizeSizeCheck.isChecked() and (img.size[0] > MAX_DIM or img.size[1] > MAX_DIM):
                        # resize image while maintaining the aspect ratio
                        ratio = img.size[0] / img.size[1]
                        if ratio > 1:
                            newSize = (MAX_DIM, round(MAX_DIM / ratio))
                        else:
                            newSize = (round(MAX_DIM * ratio), MAX_DIM)
                        img = img.resize(newSize, Image.LANCZOS)
                    mask = img.split()[3] if img.mode == 'RGBA' else None  # dealing with transparency in RGBA images
                    converted = Image.new('RGB', img.size, (255, 255, 255))
                    converted.paste(img, mask=mask)
                    pages.append(converted)
                    self.progressBar.setValue(int((i / len(self.chosenFiles)) * 95))
            except IOError:
                self.resetProgressBar()
                return self.showMessageBox('Something went wrong!', is_error=True)
        mainImg = pages.pop(0)
        if not pages:
            mainImg.save(savePath, optimize=True)
        else:
            mainImg.save(savePath, save_all=True, append_images=pages, optimize=True)
        self.progressBar.setValue(100)
        return self.showMessageBox(f'PDF created at: {self.outputDir.resolve()}', is_error=False)

    def joinPDFs(self, savePath: Path) -> Union[None, int]:
        """
        Merges the PDF files into one

        :param savePath: path to where the file is to be saved
        :return: the result of MessageBox execution
        """
        if len(self.chosenFiles) < 2:
            return self.showMessageBox('Select more than one PDF file!', is_error=True)
        self.progressBar.setHidden(False)
        merged = PdfFileMerger()
        for i, file in enumerate(self.chosenFiles, start=1):
            merged.append(PdfFileReader(str(file)))
            self.progressBar.setValue(int((i / len(self.chosenFiles)) * 95))
        merged.write(str(savePath))
        self.progressBar.setValue(100)
        return self.showMessageBox(f'PDF merged at: {self.outputDir.resolve()}', is_error=False)

    def orderFiles(self) -> None:
        """
        Sets items in filepaths' list in the same order as in ListWidget (to preserve user-defined order in the created
        PDF file)
        """
        for i in range(self.filesList.count()):
            for j in range(i, len(self.chosenFiles)):
                if self.filesList.item(i).text() == self.chosenFiles[j].name:
                    if i != j:
                        self.chosenFiles[i], self.chosenFiles[j] = self.chosenFiles[j], self.chosenFiles[i]
                    break

    def showMessageBox(self, message: str, is_error: bool) -> int:
        """
        Displays the message box with specified message

        :param message: text to be displayed in dialog
        :param is_error: if True, dialog's title and icon will indicate an error
        :return: result of dialog execution
        """
        msg = QMessageBox()
        icon = QMessageBox.Critical if is_error else QMessageBox.Information
        title = 'Error' if is_error else 'Success'
        msg.setWindowIcon(QIcon(':icon.svg'))
        msg.setIcon(icon)
        msg.setText(message)
        msg.setWindowTitle(title)
        msg.setStandardButtons(QMessageBox.Ok)
        return msg.exec()

    def resetProgressBar(self) -> None:
        """
        Hides and sets progress bar's value to 0
        """
        self.progressBar.setHidden(True)
        self.progressBar.setValue(0)


if __name__ == '__main__':
    import sys
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    pdf_maker = PDFMaker()
    sys.exit(app.exec())
