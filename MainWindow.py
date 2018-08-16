import sys

from PIL import ImageQt
from PyQt5 import QtCore, QtGui, QtWidgets, Qt

from AnsiGraphics import AnsiGraphics
from AnsiImage import AnsiImage
from AnsiPalette import AnsiPalette

from ToolSelection import ToolSelection

from SizeDialog import SizeDialog

import json
import os

class MainWindow(QtWidgets.QMainWindow):
    """
    Halcys Ansi Editor
    """
    def __init__(self):
        super(MainWindow, self).__init__()

        self.refImage = QtGui.QPixmap()

        # Set up window properties
        self.title = "HANSE"
        self.setWindowTitle(self.title)
        self.resize(1100, 600)

        # Set up other stuff
        self.currentFileName = None
        self.previewBuffer = None
        
        # Load font
        self.fonts = json.load(open(os.path.join('config', 'fonts.json'), 'r'))
        
        self.activeFont = 0
        self.ansiGraphics = AnsiGraphics(
            os.path.join('config', self.fonts[self.activeFont]['file']), 
            self.fonts[self.activeFont]['width'],
            self.fonts[self.activeFont]['height'],
        )
        
        # Set up palette
        self.palette = AnsiPalette(self.ansiGraphics, os.path.join("config", "palettes.ans"))
        
        # Create and link up GUI components
        self.createMenuBar()
        self.createComponents()
        self.createLayout()
        self.connectEvents()
        
        # Set up image
        self.newFile()
        
        # Make sure everything looks proper
        self.redisplayPalette()
        
        # Set up tools
        self.tools = []
        self.tools.append(ToolSelection(self, self.imageView, self.ansiImage))
        self.tools[0].activate()
        
        # The selection tool is Special because you can use it using the keyboard
        self.selectionTool = self.tools[0]
        
    def createMenuBar(self):
        menuFile = self.menuBar().addMenu("File")

        self.actionNew = QtWidgets.QAction("New", self)
        self.actionOpen = QtWidgets.QAction("Open", self)
        self.actionSave = QtWidgets.QAction("Save", self)
        self.actionSaveAs = QtWidgets.QAction("Save As", self)
        self.actionExport = QtWidgets.QAction("Export as PNG", self)
        self.actionExit = QtWidgets.QAction("Exit", self)
        
        menuEdit = self.menuBar().addMenu("Edit")
        self.actionSize = QtWidgets.QAction("Set size", self)
        self.actionUndo = QtWidgets.QAction("Undo", self)
        self.actionRedo = QtWidgets.QAction("Redo", self)
        self.actionCopy = QtWidgets.QAction("Copy", self)
        self.actionCut = QtWidgets.QAction("Cut", self)
        self.actionPaste = QtWidgets.QAction("Paste", self)
        
        self.toggleSkipSpace = QtWidgets.QAction("Skip space", self)
        self.toggleSkipSpace.setCheckable(True)
        self.toggleSkipSpace.setChecked(True)
        
        self.toggleWriteChar = QtWidgets.QAction("Write character", self)
        self.toggleWriteChar.setCheckable(True)
        self.toggleWriteChar.setChecked(True)
        
        self.toggleWriteFore = QtWidgets.QAction("Write foreground", self)
        self.toggleWriteFore.setCheckable(True)
        self.toggleWriteFore.setChecked(True)
        
        self.toggleWriteBack = QtWidgets.QAction("Write background", self)
        self.toggleWriteBack.setCheckable(True)
        self.toggleWriteBack.setChecked(True)
        
        menuView = self.menuBar().addMenu("View")
        self.toggleTransparent = QtWidgets.QAction("Transparent", self)
        self.toggleTransparent.setCheckable(True)
        self.toggleTransparent.setChecked(False)
        
        self.toggleHideCursor = QtWidgets.QAction("Hide cursor and selection", self)
        self.toggleHideCursor.setCheckable(True)
        self.toggleHideCursor.setChecked(False)
        
        self.actionReferenceImage = QtWidgets.QAction("Set reference image", self)
        
        self.toggleReferenceImage = QtWidgets.QAction("Show reference image", self)
        self.toggleReferenceImage.setCheckable(True)
        self.toggleReferenceImage.setChecked(True)
        
        self.toggleReferenceImageTop = QtWidgets.QAction("Reference image on top", self)
        self.toggleReferenceImageTop.setCheckable(True)
        self.toggleReferenceImageTop.setChecked(True)
        
        self.toggleSmallPreview = QtWidgets.QAction("Small preview", self)
        self.toggleSmallPreview.setCheckable(True)
        self.toggleSmallPreview.setChecked(False)
        
        menuFile.addAction(self.actionNew)
        menuFile.addAction(self.actionOpen)
        menuFile.addSeparator()
        menuFile.addAction(self.actionSave)
        menuFile.addAction(self.actionSaveAs)
        menuFile.addAction(self.actionExport)
        menuFile.addSeparator()
        menuFile.addAction(self.actionExit)
        
        menuEdit.addAction(self.actionSize)
        menuEdit.addSeparator()
        menuEdit.addAction(self.actionUndo)
        menuEdit.addAction(self.actionRedo)
        menuEdit.addSeparator()
        menuEdit.addAction(self.actionCopy)
        menuEdit.addAction(self.actionCut)
        menuEdit.addAction(self.actionPaste)
        menuEdit.addAction(self.toggleSkipSpace)
        
        menuEdit.addSeparator()
        menuEdit.addAction(self.toggleWriteChar)
        menuEdit.addAction(self.toggleWriteFore)
        menuEdit.addAction(self.toggleWriteBack)
        
        menuView.addAction(self.toggleTransparent)
        menuView.addAction(self.toggleHideCursor)
        menuView.addSeparator()
        menuView.addAction(self.actionReferenceImage)
        menuView.addAction(self.toggleReferenceImage)
        menuView.addAction(self.toggleReferenceImageTop)
        menuOpacity = menuView.addMenu("Reference opacity")
        menuView.addSeparator()
        menuView.addAction(self.toggleSmallPreview)
        menuView.addSeparator()
        menuFont = menuView.addMenu("Font")
        
        opacityActionGroup = QtWidgets.QActionGroup(self)
        opacityActionGroup.setExclusive(True)
        self.toggleOpacity = []
        for i in range(1, 10):
            opacityToggle = QtWidgets.QAction("0." + str(i), self)
            opacityToggle.setCheckable(True)
            if i == 3:
                opacityToggle.setChecked(True)
            else:
                opacityToggle.setChecked(False)
            opacityActionGroup.addAction(opacityToggle)
            menuOpacity.addAction(opacityToggle)
            self.toggleOpacity.append(opacityToggle)
        
        fontActionGroup = QtWidgets.QActionGroup(self)
        fontActionGroup.setExclusive(True)
        self.toggleFont = []
        for i in range(len(self.fonts)):
            fontToggle = QtWidgets.QAction(self.fonts[i]["name"], self)
            fontToggle.setCheckable(True)
            if i == 0:
                fontToggle.setChecked(True)
            else:
                fontToggle.setChecked(False)
            fontActionGroup.addAction(fontToggle)
            menuFont.addAction(fontToggle)
            self.toggleFont.append(fontToggle)
            
        self.menuCharacterSelect = QtWidgets.QMenu()
        self.actionsCharacterSelect = []
        self.hoveredCharSel = None
        
        characterSelectActionGroup = QtWidgets.QActionGroup(self)
        characterSelectActionGroup.setExclusive(True)
        for i in range(self.palette.char_sequence_count()):
            actionCharacterSelect = QtWidgets.QWidgetAction(self.menuCharacterSelect)
            actionCharacterSelect.setCheckable(True)
            if i == 5:
                actionCharacterSelect.setChecked(True)
            else:
                actionCharacterSelect.setChecked(False)
                
            charImage = QtGui.QPixmap.fromImage(ImageQt.ImageQt(self.palette.get_char_sequence_image(i)))
            charLabel = QtWidgets.QLabel()
            charLabel.setPixmap(charImage)
            charLabel.setMinimumSize(charLabel.pixmap().width() + 32, charLabel.pixmap().height() + 4)
            charLabel.paintEvent = (lambda event, x  = charLabel, y = actionCharacterSelect: self.paintCharSelMenu(event, x, y))
            charLabel.setMouseTracking(True)
            charLabel.mouseMoveEvent = (lambda event, x = charLabel: self.menuMouseMoved(event, x))
            actionCharacterSelect.setDefaultWidget(charLabel)
            
            self.menuCharacterSelect.addAction(actionCharacterSelect)
            characterSelectActionGroup.addAction(actionCharacterSelect)
            self.actionsCharacterSelect.append(actionCharacterSelect)
    
    def menuMouseMoved(self, event, label):
        """
        Repaint all the labels when the mouse moves
        not super efficient but w/e
        """
        self.hoveredCharSel = label
        for action in self.actionsCharacterSelect:
            action.defaultWidget().repaint()
    
    def paintCharSelMenu(self, event, label, action):
        """
        Super special "menu item with pixmap" repainter
        """        
        styleOptions = QtWidgets.QStyleOptionMenuItem()
        self.menuCharacterSelect.initStyleOption(styleOptions, action)
        if self.hoveredCharSel == label:
            styleOptions.state = styleOptions.state | QtWidgets.QStyle.State_Selected
        else:
            styleOptions.state = styleOptions.state & ~QtWidgets.QStyle.State_Selected
        styleOptions.rect = label.frameRect()
        
        painter = QtWidgets.QStylePainter(label)
        painter.drawControl(QtWidgets.QStyle.CE_MenuItem, styleOptions)
        painter.drawPixmap(30, 2, label.pixmap())
        painter.end()

    def createComponents(self):
        """
        Create window components
        """
        self.previewScroll = QtWidgets.QScrollArea()
        self.previewScroll.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.previewScroll.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        
        self.imagePreview = QtWidgets.QLabel()
        self.imagePreview.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.imagePreview.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignTop)
        
        self.imageScroll = QtWidgets.QScrollArea()
        self.imageScroll.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.imageScroll.setAlignment(QtCore.Qt.AlignCenter)
        
        self.imageView = QtWidgets.QLabel()
        self.imageView.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding)
        self.imageView.setAlignment(QtCore.Qt.AlignCenter)
        
        self.palSel = QtWidgets.QLabel()
        self.palSel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.palSel.setAlignment(QtCore.Qt.AlignCenter)
        
        self.charSel = QtWidgets.QLabel()
        self.charSel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self.charSel.setAlignment(QtCore.Qt.AlignCenter)
        
        self.charPalLabels = []
        self.charPalPixmaps = []
        for i in range(0, 12):
            charPalLabel = QtWidgets.QLabel("F" + str(i + 1))
            charPalLabel.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            self.charPalLabels.append(charPalLabel)
            
            charPalPixmap = QtWidgets.QLabel()
            charPalPixmap.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
            self.charPalPixmaps.append(charPalPixmap)
        
        self.buttonCharSelect = QtWidgets.QPushButton("▶")
        self.buttonCharSelect.setMaximumSize(30, 99999)
        
        self.buttonCharSelectNext = QtWidgets.QPushButton("▼")
        self.buttonCharSelectNext.setMaximumSize(30, 99999)
        self.buttonCharSelectPrev = QtWidgets.QPushButton("▲")
        self.buttonCharSelectPrev.setMaximumSize(30, 99999)
        
        self.cursorPositionLabel = QtWidgets.QLabel("Cursor: (0, 0)")
        self.cursorPositionLabel.setAlignment(QtCore.Qt.AlignRight)
        self.cursorPositionLabel.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        
        
    def createLayout(self):
        """
        Layout window components
        """
        mainLayout = QtWidgets.QVBoxLayout()
        layoutHorizontal = QtWidgets.QHBoxLayout()
        
        sidebarLayout = QtWidgets.QVBoxLayout()
        sidebarLayout.setAlignment(QtCore.Qt.AlignTop)
        sidebarLayout.addWidget(self.palSel)
        sidebarLayout.addWidget(self.charSel)
        
        
        self.imageScroll.setWidget(self.imageView)
        self.previewScroll.setWidget(self.imagePreview)
        
        layoutHorizontal.addWidget(self.previewScroll)
        layoutHorizontal.addWidget(self.imageScroll)
        layoutHorizontal.addLayout(sidebarLayout)
        
        charPalLayout = QtWidgets.QHBoxLayout()
        charPalLayout.setAlignment(QtCore.Qt.AlignLeft)
        for i in range(0, 12):
            charPalLayout.addWidget(self.charPalLabels[i])
            charPalLayout.addWidget(self.charPalPixmaps[i])
        
        charPalLayout.addWidget(self.buttonCharSelectPrev)
        charPalLayout.addWidget(self.buttonCharSelectNext)
        charPalLayout.addWidget(self.buttonCharSelect)
        charPalLayout.addWidget(self.cursorPositionLabel)
        
        mainLayout.addLayout(layoutHorizontal)
        mainLayout.addLayout(charPalLayout)
            
        centralWidget = QtWidgets.QWidget()
        centralWidget.setLayout(mainLayout)
        self.setCentralWidget(centralWidget)

    def connectEvents(self):
        """
        Connect UI actions to functionality
        """
        self.actionNew.triggered.connect(self.newFile)
        self.actionOpen.triggered.connect(self.openFile)
        self.actionOpen.setShortcut(QtGui.QKeySequence.Open)
        
        self.actionSave.triggered.connect(self.saveFile)
        self.actionSave.setShortcut(QtGui.QKeySequence.Save)
        self.actionSaveAs.triggered.connect(self.saveFileAs)
        self.actionExport.triggered.connect(self.exportPNG)
        
        self.actionExit.triggered.connect(self.exit)
        self.actionExit.setShortcut(QtGui.QKeySequence.Quit)
        
        self.actionSize.triggered.connect(self.resizeCanvas)
        
        self.actionUndo.triggered.connect(self.undo)
        self.actionUndo.setShortcut(QtGui.QKeySequence.Undo)
        
        self.actionRedo.triggered.connect(self.redo)
        self.actionRedo.setShortcuts([QtGui.QKeySequence.Redo, QtGui.QKeySequence("Ctrl+Y")])
        
        self.actionCopy.triggered.connect(self.clipboardCopy)
        self.actionCopy.setShortcut(QtGui.QKeySequence.Copy)
        
        self.actionCut.triggered.connect(self.clipboardCut)
        self.actionCut.setShortcut(QtGui.QKeySequence.Cut)
        
        self.actionPaste.triggered.connect(self.clipboardPaste)
        self.actionPaste.setShortcut(QtGui.QKeySequence.Paste)
        
        self.toggleWriteChar.triggered.connect(self.changeWriteStatus)
        self.toggleWriteFore.triggered.connect(self.changeWriteStatus)
        self.toggleWriteBack.triggered.connect(self.changeWriteStatus)
        
        self.toggleTransparent.triggered.connect(self.changeTransparent)
        self.toggleHideCursor.triggered.connect(self.changeHideCursor)
        
        self.buttonCharSelect.clicked.connect(self.showCharSelect)
        self.buttonCharSelectPrev.clicked.connect(lambda: (self.palette.select_char_sequence(-1, True), self.redisplayPalette()))        
        self.buttonCharSelectNext.clicked.connect(lambda: (self.palette.select_char_sequence(1, True), self.redisplayPalette()))
        
        self.imageScroll.keyPressEvent = self.keyPressEvent
        self.imageScroll.keyReleaseEvent = self.keyReleaseEvent
        self.charSel.mousePressEvent = self.charSelMousePress
        self.charSel.mouseDoubleClickEvent = self.charSelDoubleClick
        
        self.palSel.mousePressEvent = self.palSelMousePress
        
        self.actionReferenceImage.triggered.connect(self.loadReferenceImage)
        self.toggleReferenceImage.triggered.connect(self.redisplayAnsi)
        self.toggleReferenceImageTop.triggered.connect(self.redisplayAnsi)
        for i in range(1, 10):
            self.toggleOpacity[i - 1].triggered.connect(self.redisplayAnsi)
        
        for i in range(len(self.toggleFont)):
            self.toggleFont[i].triggered.connect(self.changeFont)
        
        self.imageView.paintEvent = self.repaintImage
        
        self.toggleSmallPreview.triggered.connect(self.redisplayAnsi)
        
        for action in self.actionsCharacterSelect:
            action.triggered.connect(self.setCharSequence)
        
    def charSelMousePress(self, event):
        """
        Mouse down on character selection
        """
        new_idx = (event.y() // self.ansiImage.get_char_size()[1]) * 16 + event.x() // self.ansiImage.get_char_size()[0]
        self.palette.set_char_idx(new_idx)
        self.redisplayPalette()
    
    def charSelDoubleClick(self, event):
        """
        Double clicked character selection
        """
        char = self.palette.get_char()
        self.addUndo(self.ansiImage.set_cell(char = char[0], fore = char[1], back = char[2]))
        self.ansiImage.move_cursor(1, 0)
        self.redisplayAnsi()
        
    def palSelMousePress(self, event):
        """
        Mouse down on palette selection
        """
        new_idx = (event.y() // self.ansiImage.get_char_size()[1]) * 8 + event.x() // self.ansiImage.get_char_size()[1]
        
        if event.button() == QtCore.Qt.LeftButton:
            self.palette.set_fore(new_idx)
            
        if event.button() == QtCore.Qt.RightButton:
            self.palette.set_back(new_idx)
            
        self.redisplayPalette()
                
    def updateCursorPositionLabel(self, text = None):
        """
        Update the cursor position label text
        """
        if text == None:
            x, y = self.ansiImage.get_cursor()
            if self.selectionTool.selStartX == None and self.selectionTool.selStartY == None:
                self.cursorPositionLabel.setText("Cursor: ({0}, {1})".format(x, y))
        else:
            self.cursorPositionLabel.setText(text)
        
    def repaintImage(self, event):
        """
        Repaint event - does a partial repaint of the image view label and preview label.
        """
        repaintCoords = [
            event.rect().x(), 
            event.rect().y(), 
            event.rect().x() + event.rect().width(), 
            event.rect().y() + event.rect().height()
        ]
        
        transparent = self.toggleTransparent.isChecked()
        cursor = not self.toggleHideCursor.isChecked()
        paint_x, paint_y, bitmap, size_x, size_y = self.ansiImage.to_bitmap(transparent = transparent, cursor = cursor, area = repaintCoords)
        qtPixmap = QtGui.QPixmap.fromImage(ImageQt.ImageQt(bitmap))
        
        painter = QtGui.QPainter(self.imageView)
        
        refOpacity = 0.0
        for i in range(1, 10):
            if self.toggleOpacity[i - 1].isChecked():
                refOpacity = float(i) / 10.0

        if self.toggleReferenceImage.isChecked() == True and self.toggleReferenceImageTop.isChecked() == False:
            painter.setOpacity(refOpacity)
            painter.drawPixmap(0, 0, size_x, size_y, self.refImage)
            painter.setOpacity(1.0)
            
        painter.drawPixmap(paint_x, paint_y, qtPixmap)
        
        if self.toggleReferenceImage.isChecked() == True and self.toggleReferenceImageTop.isChecked() == True:
            painter.setOpacity(refOpacity)
            painter.drawPixmap(0, 0, size_x, size_y, self.refImage)
            
        painter.end()
        
        previewScale = 4
        if self.toggleSmallPreview.isChecked():
            previewScale = 8
            
        preview_size_x = size_x // previewScale
        preview_size_y = size_y // previewScale
        if self.previewBuffer == None or self.previewBuffer.width() != preview_size_x or self.previewBuffer.height() != preview_size_y:
            self.previewBuffer = QtGui.QPixmap(preview_size_x, preview_size_y)
            previewBitmap = self.ansiImage.to_bitmap(transparent = transparent, cursor = cursor)
            previewPixmap = QtGui.QPixmap.fromImage(ImageQt.ImageQt(previewBitmap))
            preview_x = 0
            preview_y = 0
        else:
            preview_x = paint_x // previewScale
            preview_y = paint_y // previewScale
            previewPixmap = qtPixmap
        
        previewPixmap = previewPixmap.scaled(previewPixmap.width() // previewScale, previewPixmap.height() // previewScale, transformMode = QtCore.Qt.SmoothTransformation)
        previewPainter = QtGui.QPainter(self.previewBuffer)
        previewPainter.drawPixmap(preview_x, preview_y, previewPixmap.width(), previewPixmap.height(), previewPixmap)
        previewPainter.end()
        
        self.imagePreview.setPixmap(self.previewBuffer)
        
        self.imagePreview.setMinimumSize(size_x // previewScale, size_y // previewScale)
        self.imagePreview.setMaximumSize(size_x // previewScale, size_y // previewScale)
        
        self.previewScroll.setMinimumSize(size_x // previewScale + 45, 1)
        self.previewScroll.setMaximumSize(size_x // previewScale, 90001)
        
        self.imageView.setMinimumSize(size_x, size_y)
        self.imageView.setMaximumSize(size_x, size_y)
        self.updateCursorPositionLabel()
        
    def redisplayAnsi(self):
        """
        Redraws the ANSI label.
        """
        self.imageView.repaint()
        self.imagePreview.repaint()
        
    def redisplayPalette(self):
        """
        Redisplays the palette labels
        """
        bitmap = self.palette.get_palette_image()
        qtBitmap = ImageQt.ImageQt(bitmap)
        self.palSel.setPixmap(QtGui.QPixmap.fromImage(qtBitmap))
        self.palSel.setMinimumSize(qtBitmap.width(), qtBitmap.height())
        
        bitmap = self.palette.get_character_image(16)
        qtBitmap = ImageQt.ImageQt(bitmap)
        self.charSel.setPixmap(QtGui.QPixmap.fromImage(qtBitmap))
        self.charSel.setMinimumSize(qtBitmap.width(), qtBitmap.height())
        
        for i in range(0, 12):
            bitmap = self.palette.get_char_image(i, from_seq = True)
            qtBitmap = ImageQt.ImageQt(bitmap)
            self.charPalPixmaps[i].setPixmap(QtGui.QPixmap.fromImage(qtBitmap))
            self.charPalPixmaps[i].setMinimumSize(qtBitmap.width(), qtBitmap.height())
            
    def keyPressEvent(self, event):
        """
        Global key input handler
        """
        handled = False
        
        if event.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_Left, QtCore.Qt.Key_Down, QtCore.Qt.Key_Up]:
            # Selection start
            if (event.modifiers() & QtCore.Qt.ShiftModifier == QtCore.Qt.ShiftModifier):
                selX, selY = self.ansiImage.get_cursor()
                append = event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier
                remove = event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier
                self.selectionTool.beginSelection(selX, selY, append, remove)
            else:
                # Palette change
                if event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier:
                    if event.key() == QtCore.Qt.Key_Right:
                        if event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier:
                            self.palette.set_back(1, True)
                        else:
                            self.palette.set_fore(1, True)
                            
                    if event.key() == QtCore.Qt.Key_Left:
                        if event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier:
                            self.palette.set_back(-1, True)
                        else:
                            self.palette.set_fore(-1, True)
                    
                    if event.key() == QtCore.Qt.Key_Down:
                        self.palette.select_char_sequence(1, True)
                    if event.key() == QtCore.Qt.Key_Up:
                        self.palette.select_char_sequence(-1, True)
                    self.redisplayPalette()
                    handled = True
                    
        # Cursor move
        if event.key() == QtCore.Qt.Key_Right and not handled:
            self.ansiImage.move_cursor(1, 0, True)
            handled = True
            
        if event.key() == QtCore.Qt.Key_Left  and not handled:
            self.ansiImage.move_cursor(-1, 0, True)
            handled = True
            
        if event.key() == QtCore.Qt.Key_Down  and not handled:
            self.ansiImage.move_cursor(0, 1, True)
            handled = True
            
        if event.key() == QtCore.Qt.Key_Up  and not handled:
            self.ansiImage.move_cursor(0, -1, True)
            handle = True
        
        # Selection resume
        if event.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_Left, QtCore.Qt.Key_Down, QtCore.Qt.Key_Up]:
            if (event.modifiers() & QtCore.Qt.ShiftModifier == QtCore.Qt.ShiftModifier):
                selX, selY = self.ansiImage.get_cursor()
                append = event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier
                remove = event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier
                self.selectionTool.updateSelection(selX, selY, True, append, remove)
        
        # Enter key insertion
        if event.key() == QtCore.Qt.Key_Return:
            char = self.palette.get_char()
            self.addUndo(self.ansiImage.set_cell(char = char[0], fore = char[1], back = char[2]))
            if not self.ansiImage.move_cursor(1, 0):
                self.ansiImage.move_cursor(x = 0, relative = False)
                self.ansiImage.move_cursor(y = 1)
            handled = True
    
        # Smart home/end
        if event.key() == QtCore.Qt.Key_Home:
            line_end = self.ansiImage.get_line_end()
            if self.ansiImage.get_cursor()[0] > line_end + 1:
                self.ansiImage.move_cursor(x = line_end + 1, relative = False)
            else:
                self.ansiImage.move_cursor(x = 0, relative = False)
            handled = True
        
        if event.key() == QtCore.Qt.Key_End:
            line_end = self.ansiImage.get_line_end()
            if self.ansiImage.get_cursor()[0] < line_end + 1:
                self.ansiImage.move_cursor(x = line_end + 1, relative = False)
            else:
                self.ansiImage.move_cursor(x = 10000000, relative = False)
            handled = True
        
        # Ins and Del
        if event.key() == QtCore.Qt.Key_Insert:
            if (event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier):
                if (event.modifiers() & QtCore.Qt.ShiftModifier == QtCore.Qt.ShiftModifier):
                    inverse = []
                    for col in range(self.ansiImage.get_size()[0]):
                        inverse.extend(self.ansiImage.shift_column(x = col))
                    self.addUndo(inverse)
                else:
                    self.addUndo(self.ansiImage.shift_column())
            else:
                if (event.modifiers() & QtCore.Qt.ShiftModifier == QtCore.Qt.ShiftModifier):
                    inverse = []
                    for line in range(self.ansiImage.get_size()[1]):
                        inverse.extend(self.ansiImage.shift_line(y = line))
                    self.addUndo(inverse)
                else:
                    self.addUndo(self.ansiImage.shift_line())
            handled = True
            
        if event.key() == QtCore.Qt.Key_Delete:
            if self.ansiImage.has_selection():
                self.addUndo(self.ansiImage.fill_selection())
            else:
                if (event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier):
                    if (event.modifiers() & QtCore.Qt.ShiftModifier == QtCore.Qt.ShiftModifier):
                        inverse = []
                        for col in range(self.ansiImage.get_size()[0]):
                            inverse.extend(self.ansiImage.shift_column(x = col, how_much = -1))
                        self.addUndo(inverse)
                    else:
                        self.addUndo(self.ansiImage.shift_column(how_much = -1))
                else:
                    if (event.modifiers() & QtCore.Qt.ShiftModifier == QtCore.Qt.ShiftModifier):
                        inverse = []
                        for line in range(self.ansiImage.get_size()[1]):
                            inverse.extend(self.ansiImage.shift_line(y = line, how_much = -1))
                        self.addUndo(inverse)
                    else:
                        self.addUndo(self.ansiImage.shift_line(how_much = -1))
            handled = True
            
        # Backspace delete
        if event.key() == QtCore.Qt.Key_Backspace:
            if self.ansiImage.move_cursor(-1, 0):
                self.addUndo(self.ansiImage.set_cell(char = ord(' '), fore = 0, back = 0))
            handled = True
        
        # F1-12 insert
        # Theoretically this could break, practically it should be fine.
        if event.key() >= QtCore.Qt.Key_F1 and event.key() <= QtCore.Qt.Key_F12:
            pal_idx = event.key() - QtCore.Qt.Key_F1
            char = self.palette.get_char(pal_idx, True)
            self.addUndo(self.ansiImage.set_cell(char = char[0], fore = char[1], back = char[2]))
            self.ansiImage.move_cursor(1, 0)
            handled = True
        
        # Text-generating keys
        if event.text() != None and len(event.text()) == 1 and handled == False:
            char = self.palette.get_char()
            char[0] = ord(event.text())
            if char[0] <= 255:
                self.addUndo(self.ansiImage.set_cell(char = char[0], fore = char[1], back = char[2]))
                self.ansiImage.move_cursor(1, 0)
            handled = True
            
        self.redisplayAnsi()
        self.updateTitle()
     
    def keyReleaseEvent(self, event):
        """
        Global key input handler - key up edition
        """ 
        if event.key() == QtCore.Qt.Key_Shift:
            if self.selectionTool.selStartX != None and self.selectionTool.selStartY != None:
                selEndX, selEndY = self.ansiImage.get_cursor()
                append = (event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier)
                remove = (event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier)
                self.selectionTool.updateSelection(selEndX, selEndY, False, append, remove)

    def updateTitle(self):
        """
        Update title to reflect file name and file dirty condition
        """
        self.title = "HANSE"
        if self.currentFileName != None:
            self.title += " - " + self.currentFileName
        if self.ansiImage.dirty() == True:
            self.title += " *"
            
        self.setWindowTitle(self.title)
        
    def newFile(self):
        """
        Create blank 80x24 document
        """
        self.ansiImage = AnsiImage(self.ansiGraphics)
        self.ansiImage.clear_image(80, 24)
            
        self.undoStack = []
        self.redoStack = []
        self.currentFileName = None
        self.previewBuffer = None
        
        self.redisplayAnsi()
        self.updateTitle()
        
    def openFile(self):
        """
        Load an ansi file
        """
        loadFileName = QtWidgets.QFileDialog.getOpenFileName(self, caption = "Open ANSI file", filter="ANSI Files (*.ans);;Arbitrary width ANSI Files (*.ans);;All Files (*.*)")
        wideMode = False
        if loadFileName[1] == 'Arbitrary width ANSI Files (*.ans)':
            wideMode = True
        loadFileName = loadFileName[0]
        
        if len(loadFileName) != 0:
            self.currentFileName = loadFileName
            self.ansiImage.load_ans(self.currentFileName, wideMode)            
            self.previewBuffer = None
            
            self.redisplayAnsi()
            self.updateTitle()
        
    def saveFileAs(self):
        """
        Save an ansi file, with a certain name
        """
        saveFileName = QtWidgets.QFileDialog.getSaveFileName(self, caption = "Save ANSI file", filter="ANSI Files (*.ans);;All Files (*.*)")
        if saveFileName[1] == 'ANSI Files (*.ans)' and not saveFileName[0].endswith(".ans"):
            saveFileName = saveFileName[0] + ".ans" 
        else:
            saveFileName = saveFileName[0]
        if len(saveFileName) != 0:
            self.currentFileName = saveFileName
            self.saveFile()
    
    def saveFile(self):
        """
        Save an ansi file
        """
        if self.currentFileName == None:
            self.saveFileAs()
        else:
            self.ansiImage.save_ans(self.currentFileName)
        self.ansiImage.dirty(False)
        self.updateTitle()
      
    def exportPNG(self):
        """
        Export file as rendered PNG image
        """
        exportFileName = QtWidgets.QFileDialog.getSaveFileName(self, caption = "Export PNG", filter="PNG File (*.png)")[0]
        bitmap = self.ansiImage.to_bitmap(transparent = False, cursor = False)
        bitmap.save(exportFileName, "PNG")
        
    def exit(self):
        """
        Close everything and exit.
        """
        sys.exit(0)
        
    def clipboardCopy(self):
        """
        Copy to (right now internal) clipboard
        """
        pasteBuffer = self.ansiImage.get_selected(self.toggleSkipSpace.isChecked())
        
        # Text representation for external use
        extent_x = 0
        extent_y = 0
        for (x, y, char) in pasteBuffer:
            extent_x = max(extent_x, x)
            extent_y = max(extent_y, y)
            
        stringData = []
        for y in range(extent_y + 1):
            lineData = []
            for x in range(extent_x + 1):
                lineData.append(" ")
            stringData.append(lineData)
            
        for (x, y, char) in pasteBuffer:
            #print(x, y, len(stringData), len(stringData[0]))
            stringData[y][x] = char[0]
        
        stringRepresentation = ""
        try:
            for y in range(extent_y):
                stringRepresentation += bytes(stringData[y]).decode('cp866') + "\n"
        except:
            pass
        
        # Internal json representation
        byteData = QtCore.QByteArray(json.dumps(pasteBuffer).encode('utf-8'))
        mimeData = QtCore.QMimeData()
        mimeData.setData('text/hansejson', byteData)
        mimeData.setText(stringRepresentation)
        
        # All to clipboard
        clipboard = Qt.QApplication.clipboard()
        clipboard.setMimeData(mimeData)
        
    def clipboardCut(self):
        """
        Copy, then delete
        """
        self.clipboardCopy()
        self.addUndo(self.ansiImage.fill_selection())
        self.redisplayAnsi()
    
    def clipboardPaste(self):    
        """
        Paste at cursor
        """
        clipboard = Qt.QApplication.clipboard()
        mimeData = clipboard.mimeData()
        
        # This can fail in a myriad ways - if it does, that's fine.
        try:
            pasteBuffer = None
            if mimeData.hasFormat('text/hansejson'):
                pasteBuffer = json.loads(mimeData.data('text/hansejson').data().decode('utf-8'))
            else:
                if mimeData.hasText():
                    pasteText = mimeData.text()
                    lines = pasteText.split("\n")
                    pasteBuffer = []
                    for y, line in enumerate(lines):
                        for x, char in enumerate(line):
                            pasteBuffer.append((x, y, (char.encode('cp866')[0], self.palette.fore(), self.palette.back())))
                
            if pasteBuffer != None:
                self.addUndo(self.ansiImage.paste(pasteBuffer))
                self.redisplayAnsi()
        except:
            pass
        
        
    def changeWriteStatus(self):
        """
        Change which channels we are writing to.
        """
        self.ansiImage.set_write_allowed(
            self.toggleWriteChar.isChecked(),
            self.toggleWriteFore.isChecked(),
            self.toggleWriteBack.isChecked()
        )
        
    def resizeCanvas(self):
        """
        Get size via dialog and resize
        """
        cur_width, cur_height =  self.ansiImage.get_size()
        sizeDialog = SizeDialog(cur_width, cur_height)
        if sizeDialog.exec() == 1:
            new_width = sizeDialog.spinBoxWidth.value()
            new_height = sizeDialog.spinBoxHeight.value()
            self.addUndo((-1, self.ansiImage.change_size(new_width, new_height)))
            self.redisplayAnsi()
            
    def addUndo(self, operation):
        """
        Add an undo step (and clean out the redo stack)
        """
        self.undoStack.append(operation)
        self.redoStack = []
        
    def undo(self):
        """
        Undo last action
        """
        if len(self.undoStack) != 0:
            undoAction = self.undoStack.pop()
            if undoAction[0] == -1:
                undoAction = undoAction[1]
                self.redoStack.append((-1, self.ansiImage.change_size(undoAction[0], undoAction[1], undoAction[2])))
            else:
                self.redoStack.append(self.ansiImage.paste(undoAction, x = 0, y = 0))
            self.redisplayAnsi()
            
    def redo(self):
        """
        Undo last undo
        """
        if len(self.redoStack) != 0:
            redoAction = self.redoStack.pop()
            if redoAction[0] == -1:
                redoAction = redoAction[1]
                self.undoStack.append((-1, self.ansiImage.change_size(redoAction[0], redoAction[1], redoAction[2])))
            else:
                self.undoStack.append(self.ansiImage.paste(redoAction, x = 0, y = 0))
            self.redisplayAnsi()

    def changeTransparent(self):
        """
        Just call the redisplay function - it knows what to do.
        """
        self.redisplayAnsi()
     
    def changeHideCursor(self):
        """
        Just call the redisplay function - it knows what to do.
        """
        self.redisplayAnsi()
    
    def loadReferenceImage(self):
        """
        Sets up a reference image
        """
        refFileName = QtWidgets.QFileDialog.getOpenFileName(self, caption = "Open reference image", filter="Image Files (*.png)")[0]
        try:
            self.refImage.load(refFileName)
            self.redisplayAnsi()
        except:
            pass
    
    def changeFont(self):
        """
        Change the font
        """
        for i in range(len(self.toggleFont)):
            if self.toggleFont[i].isChecked():
                self.activeFont = i
            
        self.ansiGraphics = AnsiGraphics(
            os.path.join('config', self.fonts[self.activeFont]['file']), 
            self.fonts[self.activeFont]['width'],
            self.fonts[self.activeFont]['height'],
        )
        
        self.palette.change_graphics(self.ansiGraphics)
        self.ansiImage.change_graphics(self.ansiGraphics)
        self.previewBuffer = None
        self.redisplayAnsi()
        self.redisplayPalette()
        
    def showCharSelect(self):
        """
        Allow the user to select a new set of characters
        """
        self.hoveredCharSel = None
        self.menuCharacterSelect.exec(QtGui.QCursor.pos())
        
    def setCharSequence(self):
        """
        Change the selected character sequence
        """
        idx = 0
        for num, action in enumerate(self.actionsCharacterSelect):
            if action.isChecked():
                idx = num
        self.palette.select_char_sequence(idx)
        self.redisplayPalette()
        
