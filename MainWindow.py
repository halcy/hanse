import sys

from PIL import ImageQt
from PyQt5 import QtCore, QtGui, QtWidgets, Qt

from AnsiGraphics import AnsiGraphics
from AnsiImage import AnsiImage
from AnsiPalette import AnsiPalette

from SizeDialog import SizeDialog
import json

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
        self.resize(970, 600)

        # Set up other stuff
        self.currentFileName = None
        self.selStartX = None
        self.selStartY = None
        self.previewBuffer = None
        
        # Create and link up GUI components
        self.createMenuBar()
        self.createComponents()
        self.createLayout()
        self.connectEvents()
        
        # Load font
        self.ansiGraphics = AnsiGraphics("fonts/vga.fnt")
        
        # Set up image
        self.newFile()
        
        # Set up palette
        self.palette = AnsiPalette(self.ansiGraphics)
        self.redisplayPalette()
        
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
        
        menuView.addAction(self.toggleTransparent)
        menuView.addAction(self.toggleHideCursor)
        menuView.addSeparator()
        menuView.addAction(self.actionReferenceImage)
        menuView.addAction(self.toggleReferenceImage)
        menuView.addAction(self.toggleReferenceImageTop)
        menuOpacity = menuView.addMenu("Reference opacity")
        
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
        
        self.toggleTransparent.triggered.connect(self.changeTransparent)
        self.toggleHideCursor.triggered.connect(self.changeHideCursor)
        
        self.imageScroll.keyPressEvent = self.keyPressEvent
        self.imageScroll.keyReleaseEvent = self.keyReleaseEvent
        self.charSel.mousePressEvent = self.charSelMousePress
        self.charSel.mouseDoubleClickEvent = self.charSelDoubleClick
        
        self.palSel.mousePressEvent = self.palSelMousePress
        self.imageView.mousePressEvent = self.imageMousePress
        self.imageView.mouseMoveEvent = self.imageMouseMoveRelease
        self.imageView.mouseReleaseEvent = self.imageMouseMoveRelease
        
        self.actionReferenceImage.triggered.connect(self.loadReferenceImage)
        self.toggleReferenceImage.triggered.connect(self.redisplayAnsi)
        self.toggleReferenceImageTop.triggered.connect(self.redisplayAnsi)
        for i in range(1, 10):
            self.toggleOpacity[i - 1].triggered.connect(self.redisplayAnsi)
        
        self.imageView.paintEvent = self.repaintImage
        
    def charSelMousePress(self, event):
        """
        Mouse down on character selection
        """
        new_idx = (event.y() // 16) * 16 + event.x() // 8
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
        new_idx = (event.y() // 16) * 8 + event.x() // 16
        
        if event.button() == QtCore.Qt.LeftButton:
            self.palette.set_fore(new_idx)
            
        if event.button() == QtCore.Qt.RightButton:
            self.palette.set_back(new_idx)
            
        self.redisplayPalette()
    
    def imageMousePress(self, event):
        """
        Mouse down on image
        """
        if event.button() == QtCore.Qt.LeftButton:
            selStartX = event.x() // 8
            selStartY = event.y() // 16
            append = event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier
            remove = event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier
            self.ansiImage.move_cursor(selStartX, selStartY, False)
            self.beginSelection(selStartX, selStartY, append, remove)
            
        if event.button() == QtCore.Qt.RightButton:
            new_pal_char = self.ansiImage.get_cell(event.x() // 8, event.y() // 16)
            self.palette.set_char_idx(new_pal_char[0])
            self.palette.set_fore(new_pal_char[1])
            self.palette.set_back(new_pal_char[2])
            self.redisplayPalette()
            
    def imageMouseMoveRelease(self, event):
        """
        Changes or commits selection
        """
        if event.buttons() == QtCore.Qt.LeftButton or event.button() == QtCore.Qt.LeftButton:
            selEndX = event.x() // 8
            selEndY = event.y() // 16
            
            preliminary = not (event.button() == QtCore.Qt.LeftButton)
            append = (event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier)
            remove = (event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier)
            if selEndX == self.selStartX and selEndY == self.selStartY and not append:
                self.updateSelection(selEndX, selEndY, preliminary, append, remove)
                self.ansiImage.set_selection()
                self.redisplayAnsi()
            else:
                self.updateSelection(selEndX, selEndY, preliminary, append, remove)
                
    def beginSelection(self, selStartX, selStartY, append, remove):
        if self.selStartX != None or self.selStartY != None:
            return
            
        self.selStartX = selStartX
        self.selStartY = selStartY
        self.ansiImage.set_selection([(self.selStartX, self.selStartY)], append = append, remove = remove)
        self.redisplayAnsi()
    
    def updateSelection(self, selEndX, selEndY, preliminary, append, remove):
        """
        Updates the ongoing selection process
        """
        selDirX = 1
        if selEndX - self.selStartX < 0:
            selDirX = -1
            
        selDirY = 1
        if selEndY - self.selStartY < 0:
            selDirY = -1

        if selEndY - self.selStartY == 0 and selEndX - self.selStartX == 0:
            selDirX = 1
            selDirY = 1   
            
        if selEndX != self.selStartX or selEndY != self.selStartY:  
            selection = []
            for x in range(self.selStartX, selEndX + selDirX, selDirX):
                for y in range(self.selStartY, selEndY + selDirY, selDirY):
                    selection.append((x, y))
            
            
            self.ansiImage.set_selection(selection, append = append, remove = remove, preliminary = preliminary)
            self.redisplayAnsi()
        else:
            self.ansiImage.set_selection([(selEndX, selEndY)], append = append, remove = remove, preliminary = preliminary)
            self.redisplayAnsi()
            
        if preliminary:
            self.updateCursorPositionLabel("Selecting: ({0}, {1}) to ({2}, {3}) = {4} x {5}".format(
                self.selStartX, 
                self.selStartY,
                selEndX,
                selEndY,
                abs(self.selStartX - selEndX - selDirX),
                abs(self.selStartY - selEndY - selDirY)
            ))
        else:
            self.selStartX = None
            self.selStartY = None
        
        if selEndX == self.selStartX and selEndY == self.selStartY and not preliminary:
            self.selStartX = None
            self.selStartY = None
                
    def updateCursorPositionLabel(self, text = None):
        """
        Update the cursor position label text
        """
        if text == None:
            x, y = self.ansiImage.get_cursor()
            if self.selStartX == None and self.selStartY == None:
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
        paint_x, paint_y, bitmap, size_x, size_y = self.ansiImage.to_bitmap(self.ansiGraphics, transparent = transparent, cursor = cursor, area = repaintCoords)
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
        
        preview_size_x = size_x // 8
        preview_size_y = size_y // 8
        if self.previewBuffer == None or self.previewBuffer.width() != preview_size_x or self.previewBuffer.height() != preview_size_y:
            self.previewBuffer = QtGui.QPixmap(preview_size_x, preview_size_y)
            previewBitmap = self.ansiImage.to_bitmap(self.ansiGraphics, transparent = transparent, cursor = cursor)
            previewPixmap = QtGui.QPixmap.fromImage(ImageQt.ImageQt(previewBitmap))
            preview_x = 0
            preview_y = 0
        else:
            preview_x = paint_x // 8
            preview_y = paint_y // 8
            previewPixmap = qtPixmap
            
        previewPainter = QtGui.QPainter(self.previewBuffer)
        previewPainter.drawPixmap(preview_x, preview_y, previewPixmap.width() // 8, previewPixmap.height() // 8, previewPixmap)
        previewPainter.end()
        
        self.imagePreview.setPixmap(self.previewBuffer)
        
        self.imagePreview.setMinimumSize(size_x // 8, size_y // 8)
        self.imagePreview.setMaximumSize(size_x // 8, size_y // 8)
        
        self.previewScroll.setMinimumSize(size_x // 8 + 45, 1)
        self.previewScroll.setMaximumSize(size_x // 8, 90001)
        
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
        
        # Selection start
        if event.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_Left, QtCore.Qt.Key_Down, QtCore.Qt.Key_Up]:
            if (event.modifiers() & QtCore.Qt.ShiftModifier == QtCore.Qt.ShiftModifier):
                selX, selY = self.ansiImage.get_cursor()
                append = event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier
                remove = event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier
                self.beginSelection(selX, selY, append, remove)

        # Cursor move
        if event.key() == QtCore.Qt.Key_Right:
            self.ansiImage.move_cursor(1, 0, True)
            handled = True
            
        if event.key() == QtCore.Qt.Key_Left:
            self.ansiImage.move_cursor(-1, 0, True)
            handled = True
            
        if event.key() == QtCore.Qt.Key_Down:
            self.ansiImage.move_cursor(0, 1, True)
            handled = True
            
        if event.key() == QtCore.Qt.Key_Up:
            self.ansiImage.move_cursor(0, -1, True)
            handle = True
        
        # Selection resume
        if event.key() in [QtCore.Qt.Key_Right, QtCore.Qt.Key_Left, QtCore.Qt.Key_Down, QtCore.Qt.Key_Up]:
            if (event.modifiers() & QtCore.Qt.ShiftModifier == QtCore.Qt.ShiftModifier):
                selX, selY = self.ansiImage.get_cursor()
                append = event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier
                remove = event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier
                self.updateSelection(selX, selY, True, append, remove)
        
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
            if self.selStartX != None and self.selStartY != None:
                selEndX, selEndY = self.ansiImage.get_cursor()
                append = (event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier)
                remove = (event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier)
                self.updateSelection(selEndX, selEndY, False, append, remove)

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
        self.ansiImage = AnsiImage()
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
        bitmap = self.ansiImage.to_bitmap(self.ansiGraphics, transparent = False, cursor = False)
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
        pasteBuffer = self.ansiImage.get_selected()
        
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
        for y in range(extent_y):
            stringRepresentation += bytes(stringData[y]).decode('cp866') + "\n"
            
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
        refFileName = QtWidgets.QFileDialog.getOpenFileName(self, caption = "Open reference image", filter="Image Files (*.png)")[0]
        try:
            self.refImage.load(refFileName)
            self.redisplayAnsi()
        except:
            pass
        
