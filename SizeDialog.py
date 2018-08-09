from PyQt5 import QtCore, QtGui, QtWidgets

class SizeDialog(QtWidgets.QDialog):
    def __init__(self, width, height):
        super(SizeDialog, self).__init__()
        self.setModal(True)
        self.setWindowTitle("Enter new size...")
        self.setSizeGripEnabled(False)
        
        self.labelWidth = QtWidgets.QLabel("Width")
        self.labelWidth.setMinimumSize(50, 1)
        
        self.spinBoxWidth = QtWidgets.QSpinBox()
        self.spinBoxWidth.setMinimum(1)
        self.spinBoxWidth.setMaximum(9999)
        self.spinBoxWidth.setValue(width)
        
        self.labelHeight = QtWidgets.QLabel("Height")
        self.labelHeight.setMinimumSize(50, 1)
        
        self.spinBoxHeight = QtWidgets.QSpinBox()
        self.spinBoxHeight.setMinimum(1)
        self.spinBoxHeight.setMaximum(99999)
        self.spinBoxHeight.setValue(height)
        
        self.cancelButton = QtWidgets.QPushButton("Cancel")
        self.cancelButton.clicked.connect(self.reject)
        
        self.acceptButton = QtWidgets.QPushButton("Ok!")
        self.acceptButton.clicked.connect(self.accept)
        
        widthLayout = QtWidgets.QHBoxLayout()
        widthLayout.addWidget(self.labelWidth)
        widthLayout.addWidget(self.spinBoxWidth)             
             
        heightLayout = QtWidgets.QHBoxLayout()
        heightLayout.addWidget(self.labelHeight)
        heightLayout.addWidget(self.spinBoxHeight)
        
        buttonLayout = QtWidgets.QHBoxLayout()
        buttonLayout.addWidget(self.cancelButton)
        buttonLayout.addWidget(self.acceptButton)
        buttonLayout.setAlignment(QtCore.Qt.AlignRight)
        
        mainLayout = QtWidgets.QVBoxLayout()
        mainLayout.addLayout(widthLayout)
        mainLayout.addLayout(heightLayout)
        mainLayout.addLayout(buttonLayout)
        
        self.setLayout(mainLayout)
    
