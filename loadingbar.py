from PyQt6.QtWidgets import QProgressDialog, QApplication


class LoadingBar(QProgressDialog):
    def __init__(self, parent, n):
        super().__init__(parent)
        self.setRange(0, n)
        self.setLabelText("Processing Music Files...")
        # self.setCancelButton(None)  # Remove the cancel button if not needed
        self.setWindowTitle("Initializing Database")
        self.setModal(True)
        self.setMinimumDuration(0)  # Ensure the dialog appears immediately

    def update_loadingbar(self, value):
        self.setValue(value)
        QApplication.processEvents()  # Process events to update the UI
