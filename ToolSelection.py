from PyQt5 import QtCore, QtGui, QtWidgets, Qt

class ToolSelection():
    """
    Basic "selection" tool
    """
    def __init__(self, window, imageView, image):
        self.window = window
        self.imageView = imageView
        self.image = image
        
        self.selStartX = None
        self.selStartY = None
        
    def activate(self):
        """
        Turn this tool on
        """
        self.imageView.mousePressEvent = self.mousePress
        self.imageView.mouseMoveEvent = self.mouseMoveRelease
        self.imageView.mouseReleaseEvent = self.mouseMoveRelease
        
    def mousePress(self, event):
        """
        Mouse down on image -> Begin selection
        """
        if event.button() == QtCore.Qt.LeftButton:
            selStartX = event.x() // self.image.get_char_size()[0]
            selStartY = event.y() // self.image.get_char_size()[1]
            append = event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier
            remove = event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier
            self.image.move_cursor(selStartX, selStartY, False)
            self.beginSelection(selStartX, selStartY, append, remove)
            
        if event.button() == QtCore.Qt.RightButton:
            new_pal_char = self.image.get_cell(event.x() // self.image.get_char_size()[0], event.y() // self.image.get_char_size()[1])
            self.window.palette.set_char_idx(new_pal_char[0])
            self.window.palette.set_fore(new_pal_char[1])
            self.window.palette.set_back(new_pal_char[2])
            self.window.redisplayPalette()
       
            
    def mouseMoveRelease(self, event):
        """
        Changes or commits selection
        """
        if event.buttons() == QtCore.Qt.LeftButton or event.button() == QtCore.Qt.LeftButton:
            selEndX = event.x() // self.image.get_char_size()[0]
            selEndY = event.y() // self.image.get_char_size()[1]
            
            preliminary = not (event.button() == QtCore.Qt.LeftButton)
            append = (event.modifiers() & QtCore.Qt.ControlModifier == QtCore.Qt.ControlModifier)
            remove = (event.modifiers() & QtCore.Qt.AltModifier == QtCore.Qt.AltModifier)
            if selEndX == self.selStartX and selEndY == self.selStartY and not append:
                self.updateSelection(selEndX, selEndY, preliminary, append, remove)
                self.image.set_selection()
                self.window.redisplayAnsi()
            else:
                self.updateSelection(selEndX, selEndY, preliminary, append, remove)
                
    def beginSelection(self, selStartX, selStartY, append, remove):
        """
        Start the selection process
        """
        if self.selStartX != None or self.selStartY != None:
            return
            
        self.selStartX = selStartX
        self.selStartY = selStartY
        self.image.set_selection([(self.selStartX, self.selStartY)], append = append, remove = remove)
        self.window.redisplayAnsi()
    
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
            
            
            self.image.set_selection(selection, append = append, remove = remove, preliminary = preliminary)
            self.window.redisplayAnsi()
        else:
            self.image.set_selection([(selEndX, selEndY)], append = append, remove = remove, preliminary = preliminary)
            self.window.redisplayAnsi()
            
        if preliminary:
            self.window.updateCursorPositionLabel("Selecting: ({0}, {1}) to ({2}, {3}) = {4} x {5}".format(
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
