import sys

from PIL import ImageQt
from PyQt5 import QtCore, QtGui, QtWidgets

from AnsiGraphics import AnsiGraphics
from AnsiImage import AnsiImage
from AnsiPalette import AnsiPalette

class MainWindow(QtWidgets.QMainWindow):
    """
    Halcys Ansi Editor
    """
    def __init__(self):
        super(MainWindow, self).__init__()

        # Set up window properties
        self.title = "HANSE"
        self.setWindowTitle(self.title)
        self.resize(900, 600)

        # Create and link up GUI components
        self.createMenuBar()
        self.createComponents()
        self.createLayout()
        self.connectEvents()
        
        # Load font
        self.ansiGraphics = AnsiGraphics("fonts/vga.fnt")
        
        # Set up image
        self.ansiImage = AnsiImage()
        self.ansiImage.clear_image(80, 24)
        self.redisplayAnsi()
        
        # Set up palette
        self.palette = AnsiPalette(self.ansiGraphics)
        self.redisplayPalette()
        
        # Set up other stuff
        self.currentFileName = None
        self.pasteBuffer = None
        self.selStartX = 0
        self.selStartY = 0
        
    def createMenuBar(self):
        menuFile = self.menuBar().addMenu("File")

        self.actionNew = QtWidgets.QAction("New", self)
        self.actionOpen = QtWidgets.QAction("Open", self)
        self.actionSave = QtWidgets.QAction("Save", self)
        self.actionSaveAs = QtWidgets.QAction("Save As", self)
        self.actionExport = QtWidgets.QAction("Export as PNG", self)
        self.actionExit = QtWidgets.QAction("Exit", self)
        
        menuEdit = self.menuBar().addMenu("Edit")
        self.actionCopy = QtWidgets.QAction("Copy", self)
        self.actionPaste = QtWidgets.QAction("Paste", self)
        
        menuFile.addAction(self.actionNew)
        menuFile.addAction(self.actionOpen)
        menuFile.addSeparator()
        menuFile.addAction(self.actionSave)
        menuFile.addAction(self.actionSaveAs)
        menuFile.addAction(self.actionExport)
        menuFile.addSeparator()
        menuFile.addAction(self.actionExit)
        
        menuEdit.addAction(self.actionCopy)
        menuEdit.addAction(self.actionPaste)
        
    def createComponents(self):
        """
        Create window components
        """
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
        layoutHorizontal.addWidget(self.imageScroll)
        layoutHorizontal.addLayout(sidebarLayout)
        
        charPalLayout = QtWidgets.QHBoxLayout()
        charPalLayout.setAlignment(QtCore.Qt.AlignLeft)
        for i in range(0, 12):
            charPalLayout.addWidget(self.charPalLabels[i])
            charPalLayout.addWidget(self.charPalPixmaps[i])
        
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
        self.actionOpen.setShortcut(QtGui.QKeySequence("Ctrl+O"))
        
        self.actionSave.triggered.connect(self.saveFile)
        self.actionSave.setShortcut(QtGui.QKeySequence("Ctrl+S"))
        self.actionSaveAs.triggered.connect(self.saveFileAs)
        self.actionExport.triggered.connect(self.exportPNG)
        
        self.actionExit.triggered.connect(self.exit)
        self.actionExit.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
        
        self.actionCopy.triggered.connect(self.clipboardCopy)
        self.actionCopy.setShortcut(QtGui.QKeySequence("Ctrl+C"))
        
        self.actionPaste.triggered.connect(self.clipboardPaste)
        self.actionPaste.setShortcut(QtGui.QKeySequence("Ctrl+v"))
        
        self.imageScroll.keyPressEvent = self.keyPressEvent # For catching arrow keys globally
        self.charSel.mousePressEvent = self.charSelMousePress
        self.palSel.mousePressEvent = self.palSelMousePress
        self.imageView.mousePressEvent = self.imageMousePress
        self.imageView.mouseReleaseEvent = self.imageMouseRelease
        
    def charSelMousePress(self, event):
        """
        Mouse down on palette selection
        """
        new_idx = (event.y() // 16) * 16 + event.x() // 8
        self.palette.set_char_idx(new_idx)
        self.redisplayPalette()
    
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
            self.selStartX = event.x() // 8
            self.selStartY = event.y() // 16
            self.ansiImage.move_cursor(self.selStartX, self.selStartY, False)
            self.redisplayAnsi()
            
    def imageMouseRelease(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            selEndX = event.x() // 8
            selEndY = event.y() // 16
            
            if selEndX != self.selStartX or selEndY != self.selStartY:
                
                selDirX = 1
                if selEndX - self.selStartX < 0:
                    selDirX = -1
                    
                selDirY = 1
                if selEndY - self.selStartY < 0:
                    selDirY = -1
                    
                selection = []
                for x in range(self.selStartX, selEndX + 1, selDirX):
                    for y in range(self.selStartY, selEndY + 1, selDirY):
                        selection.append((x, y))
                self.ansiImage.set_selection(selection)
            else:
                self.ansiImage.set_selection()
            self.redisplayAnsi()
        
    def redisplayAnsi(self):
        """
        Redraws the ANSI label.
        """
        bitmap = self.ansiImage.to_bitmap(self.ansiGraphics, transparent = False, cursor = True)
        qtBitmap = ImageQt.ImageQt(bitmap)
        self.imageView.setPixmap(QtGui.QPixmap.fromImage(qtBitmap))
        self.imageView.setMinimumSize(qtBitmap.width(), qtBitmap.height())
        self.imageView.setMaximumSize(qtBitmap.width(), qtBitmap.height())
    
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
            
        if event.key() == QtCore.Qt.Key_Return:
            char = self.palette.get_char()
            self.ansiImage.set_cell(char = char[0], fore = char[1], back = char[2])
            if not self.ansiImage.move_cursor(1, 0):
                self.ansiImage.move_cursor(x = 0, relative = False)
                self.ansiImage.move_cursor(y = 1)
            handled = True
        
        # TODO: "Smart" home/end
        if event.key() == QtCore.Qt.Key_Home:
            self.ansiImage.move_cursor(x = 0, relative = False)
            handled = True
            
        if event.key() == QtCore.Qt.Key_End:
            self.ansiImage.move_cursor(x = 10000000, relative = False)
            handled = True
        
        if event.key() == QtCore.Qt.Key_Backspace:
            if self.ansiImage.move_cursor(-1, 0):
                self.ansiImage.set_cell(char = ord(' '))
            handled = True
        
        # Theoretically this could break, practically it should be fine.
        if event.key() >= QtCore.Qt.Key_F1 and event.key() <= QtCore.Qt.Key_F12:
            pal_idx = event.key() - QtCore.Qt.Key_F1
            char = self.palette.get_char(pal_idx, True)
            self.ansiImage.set_cell(char = char[0], fore = char[1], back = char[2])
            self.ansiImage.move_cursor(1, 0)
            handled = True
        
        if event.text() != None and len(event.text()) == 1 and handled == False:
            char = self.palette.get_char()
            char[0] = ord(event.text())
            if char[0] <= 255:
                self.ansiImage.set_cell(char = char[0], fore = char[1], back = char[2])
                self.ansiImage.move_cursor(1, 0)
            handled = True
            
        self.redisplayAnsi()
        self.updateTitle()
        
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
        self.currentFileName = None
        self.redisplayAnsi()
        self.updateTitle()
        
    def openFile(self):
        """
        Load an ansi file
        """
        self.currentFileName = QtWidgets.QFileDialog.getOpenFileName(self, caption = "Open ANSI file", filter="ANSI Files (*.ans)")[0]
        self.ansiImage.load_ans(self.currentFileName)
        self.redisplayAnsi()
        self.updateTitle()
        
    def saveFileAs(self):
        """
        Save an ansi file, with a certain name
        """
        self.currentFileName = QtWidgets.QFileDialog.getSaveFileName(self, caption = "Save ANSI file", filter="ANSI Files (*.ans)")[0]
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
        self.pasteBuffer = self.ansiImage.get_selected()
        
    def clipboardPaste(self):    
        """
        Paste at cursor
        """
        if self.pasteBuffer != None:
            self.ansiImage.paste(self.pasteBuffer)
            self.redisplayAnsi()
            
