from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout, QPushButton, QMessageBox
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, QStandardPaths
import os

class AlbumImageWindow(QDialog):
    def __init__(self, parent=None, image=None, icon=None, imagename=None):
        super().__init__(parent)
        # Resize the image while maintaining aspect ratio
        screen_size = self.parent().screen().availableGeometry()        
        
        # Default value for size
        size = 640  
        
        if screen_size.height() > 1200:
            size = 1200
        elif 1080 <= screen_size.height() < 1200:
            size = 1000
        elif 700 <= screen_size.height() < 800:
            size = 700

        new_width = size
        new_height = size
        
        if image.width() > new_height:
            new_width = image.width()
            new_height = image.width()
            
        self.image = image.scaled(new_width, new_height, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)

        self.image_name = imagename
        title = self.image_name.split('/')[-1]

        # Set up the dialog window
        self.setWindowTitle(f"{title} - ({new_width}x{new_height})px")
        if icon:
            self.setWindowIcon(QIcon(icon))

        # Create a label to display the image
        image_label = QLabel(self)
        save_button = QPushButton("Save Image to Disk")
        
        if self.image:
            image_label.setPixmap(self.image)

        # Optional: Align the image to the center
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Create and set the layout for the dialog
        layout = QVBoxLayout()
        layout.addWidget(image_label)
        layout.addWidget(save_button)
        self.setLayout(layout)

        # Optional: Set the size of the window to fit the image
        self.adjustSize()
        
        save_button.clicked.connect(self.save_image)

    def save_image(self):
        default_image_folder = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.PicturesLocation)

        # Define the file name and the full path
        file_name = self.image_name.split('/')[-1]

        # Check if the OS is Windows
        if os.name == 'nt':  # 'nt' stands for Windows
            file_name = self.image_name.split("\\")[-1] # တော်တော်သောက်လုပ်ရှပ်တဲ့ window  
        
        for ext in ['.mp3', '.ogg', '.asc']:
            if file_name.endswith(ext):
                file_name = file_name.removesuffix(ext)
                
        save_path = os.path.join(default_image_folder, file_name) + ".png"
        print(save_path)
        
        # Save the pixmap to the specified path in PNG format
        success = self.image.save(save_path, format='PNG')

        # Create a QMessageBox to notify the user
        msg_box = QMessageBox(self)
        if success:
            msg_box.setIcon(QMessageBox.Icon.Information)
            msg_box.setText(f"Image saved successfully at {save_path}")
            msg_box.setWindowTitle("Success")
        else:
            msg_box.setIcon(QMessageBox.Icon.Critical)
            msg_box.setText("Failed to save the image.")
            msg_box.setWindowTitle("Error")
        
        msg_box.exec()
