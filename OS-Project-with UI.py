import sys
import os
import shutil
from pathlib import Path
import zipfile
from PyQt6.QtWidgets import (QApplication, QMainWindow, QPushButton, QVBoxLayout, 
                            QHBoxLayout, QWidget, QLabel, QFileDialog, QProgressBar, 
                            QTextEdit)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

class FileOrganizerThread(QThread):
    progress_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, source_drive, destination_drive):
        super().__init__()
        self.source_drive = source_drive
        self.destination_drive = destination_drive
        
    def run(self):
        try:
            final_folder = os.path.join(self.destination_drive, "final_folder")
            
            categories = {
                "texts": [".txt", ".doc", ".docx", ".pdf", ".rtf"],
                "images": [".jpg", ".jpeg", ".png", ".gif", ".bmp"],
                "videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv"]
            }
            
            # ساخت پوشه‌ها
            category_paths = {}
            for category in categories:
                category_path = os.path.join(self.source_drive, category)
                os.makedirs(category_path, exist_ok=True)
                category_paths[category] = category_path
                self.progress_signal.emit(f"ساخت پوشه {category}")
            
            # دسته‌بندی فایل‌ها
            for root, dirs, files in os.walk(self.source_drive):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_extension = os.path.splitext(file)[1].lower()
                    
                    for category, extensions in categories.items():
                        if file_extension in extensions:
                            try:
                                shutil.copy2(file_path, category_paths[category])
                                self.progress_signal.emit(f"کپی فایل: {file}")
                            except Exception as e:
                                self.progress_signal.emit(f"خطا در کپی فایل {file}: {str(e)}")
                            break
            
            # ساخت پوشه نهایی
            os.makedirs(final_folder, exist_ok=True)
            self.progress_signal.emit("ساخت پوشه نهایی در مقصد")
            
            # انتقال پوشه‌ها
            for category in categories:
                source_folder = category_paths[category]
                dest_folder = os.path.join(final_folder, category)
                try:
                    shutil.copytree(source_folder, dest_folder, dirs_exist_ok=True)
                    self.progress_signal.emit(f"انتقال پوشه {category}")
                except Exception as e:
                    self.progress_signal.emit(f"خطا در انتقال پوشه {category}: {str(e)}")
            
            # ساخت فایل zip
            zip_path = os.path.join(self.destination_drive, "final_folder.zip")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(final_folder):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, final_folder)
                        zipf.write(file_path, arcname)
                        self.progress_signal.emit(f"فشرده‌سازی فایل: {file}")
            
            self.finished_signal.emit(True, "عملیات با موفقیت انجام شد!")
            
        except Exception as e:
            self.finished_signal.emit(False, f"خطای کلی: {str(e)}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("سازمان‌دهنده فایل‌ها")
        self.setMinimumSize(600, 400)
        
        # ویجت اصلی
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # انتخاب مسیر مبدا
        source_layout = QHBoxLayout()
        self.source_label = QLabel("مسیر مبدا:")
        self.source_path = QLabel("انتخاب نشده")
        source_button = QPushButton("انتخاب مسیر")
        source_button.clicked.connect(lambda: self.select_path("source"))
        source_layout.addWidget(self.source_label)
        source_layout.addWidget(self.source_path)
        source_layout.addWidget(source_button)
        layout.addLayout(source_layout)
        
        # انتخاب مسیر مقصد
        dest_layout = QHBoxLayout()
        self.dest_label = QLabel("مسیر مقصد:")
        self.dest_path = QLabel("انتخاب نشده")
        dest_button = QPushButton("انتخاب مسیر")
        dest_button.clicked.connect(lambda: self.select_path("destination"))
        dest_layout.addWidget(self.dest_label)
        dest_layout.addWidget(self.dest_path)
        dest_layout.addWidget(dest_button)
        layout.addLayout(dest_layout)
        
        # دکمه شروع
        self.start_button = QPushButton("شروع عملیات")
        self.start_button.clicked.connect(self.start_organization)
        layout.addWidget(self.start_button)
        
        # نمایش پیشرفت
        self.progress_text = QTextEdit()
        self.progress_text.setReadOnly(True)
        layout.addWidget(self.progress_text)
        
        self.source_dir = ""
        self.dest_dir = ""
        
    def select_path(self, path_type):
        folder = QFileDialog.getExistingDirectory(self, "انتخاب پوشه")
        if folder:
            if path_type == "source":
                self.source_dir = folder
                self.source_path.setText(folder)
            else:
                self.dest_dir = folder
                self.dest_path.setText(folder)
                
    def start_organization(self):
        if not self.source_dir or not self.dest_dir:
            self.progress_text.append("لطفا هر دو مسیر را انتخاب کنید!")
            return
            
        self.start_button.setEnabled(False)
        self.progress_text.clear()
        
        self.worker = FileOrganizerThread(self.source_dir, self.dest_dir)
        self.worker.progress_signal.connect(self.update_progress)
        self.worker.finished_signal.connect(self.organization_finished)
        self.worker.start()
        
    def update_progress(self, message):
        self.progress_text.append(message)
        
    def organization_finished(self, success, message):
        self.progress_text.append(message)
        self.start_button.setEnabled(True)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
