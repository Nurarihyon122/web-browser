import sys
import os
import json
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QWidget, QTabWidget, QTableWidget, QTableWidgetItem, QDialog, QListWidget
)
from PyQt5.QtWebEngineWidgets import QWebEngineView
from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QIcon


class BookmarkDialog(QDialog):
    def __init__(self, bookmarks):
        super().__init__()
        self.setWindowTitle("Bookmarks")
        self.setGeometry(200, 200, 400, 400)

        # Create a layout for the dialog
        layout = QVBoxLayout()

        # Create a list widget to display bookmarks
        self.bookmarks_list = QListWidget()
        for bookmark in bookmarks:
            self.bookmarks_list.addItem(bookmark)

        layout.addWidget(self.bookmarks_list)
        self.setLayout(layout)


class CustomBrowser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set the main window properties
        self.setWindowTitle("Monarch Browser")
        self.setWindowIcon(QIcon("./monarch.png"))  # Add your custom icon here
        self.setGeometry(100, 100, 1200, 800)

        # Initialize bookmarks
        self.bookmarks_file = "bookmarks.json"
        self.bookmarks = self.load_bookmarks()

        # Initialize history database
        self.history_db = "history.db"
        self.init_history_db()

        # Create a central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # Create a vertical layout
        self.layout = QVBoxLayout()
        self.central_widget.setLayout(self.layout)

        # Create a tab widget
        self.tab_widget = QTabWidget()
        self.layout.addWidget(self.tab_widget)

        # Add initial tab
        self.add_new_tab()

        # Create a navigation bar
        self.top_layout = QHBoxLayout()

        self.url_bar = QLineEdit()
        self.url_bar.setPlaceholderText("Search or enter URL")
        self.url_bar.returnPressed.connect(self.load_url)
        self.top_layout.addWidget(self.url_bar)

        self.back_button = QPushButton("⬅")  # Back arrow
        self.back_button.clicked.connect(self.go_back)
        self.top_layout.addWidget(self.back_button)

        self.forward_button = QPushButton("➡")  # Forward arrow
        self.forward_button.clicked.connect(self.go_forward)
        self.top_layout.addWidget(self.forward_button)

        self.reload_button = QPushButton("↻")  # Reload icon
        self.reload_button.clicked.connect(self.reload_page)
        self.top_layout.addWidget(self.reload_button)

        self.bookmark_button = QPushButton("#")  # Bookmark icon
        self.bookmark_button.clicked.connect(self.add_bookmark)
        self.top_layout.addWidget(self.bookmark_button)

        # New button to show bookmarks in a dialog
        self.show_bookmarks_button = QPushButton("Show Bookmarks")
        self.show_bookmarks_button.clicked.connect(self.show_bookmarks)
        self.top_layout.addWidget(self.show_bookmarks_button)

        # Buttons for new tab and close tab functionality
        self.new_tab_button = QPushButton("New Tab")
        self.new_tab_button.clicked.connect(self.add_new_tab)
        self.top_layout.addWidget(self.new_tab_button)

        self.close_tab_button = QPushButton("Close Tab")
        self.close_tab_button.clicked.connect(self.close_current_tab)
        self.top_layout.addWidget(self.close_tab_button)

        self.layout.addLayout(self.top_layout)

        # Create a table for history
        self.history_table = QTableWidget()
        self.history_table.setColumnCount(2)
        self.history_table.setHorizontalHeaderLabels(["URL", "Timestamp"])
        self.layout.addWidget(self.history_table)
        self.load_history()

    def add_new_tab(self, url=None):
        new_browser = QWebEngineView()
        if url:
            new_browser.setUrl(QUrl(url))
        else:
            self.set_homepage(new_browser)

        new_browser.urlChanged.connect(self.update_url)
        new_browser.urlChanged.connect(self.save_history)

        new_tab_index = self.tab_widget.addTab(new_browser, "New Tab")
        self.tab_widget.setCurrentIndex(new_tab_index)

    def close_current_tab(self):
        if self.tab_widget.count() > 1:
            self.tab_widget.removeTab(self.tab_widget.currentIndex())
        else:
            self.statusBar().showMessage("Cannot close the last tab.", 3000)

    def set_homepage(self, browser):
        # Set homepage to a custom HTML file or a URL
        home_page_path = os.path.abspath("homepage.html")  # Ensure homepage.html exists
        if os.path.exists(home_page_path):
            browser.setUrl(QUrl.fromLocalFile(home_page_path))
        else:
            browser.setUrl(QUrl("https://www.example.com"))  # Default to example.com if file is not found

    def show_bookmarks(self):
        # Create a dialog to display bookmarks
        dialog = BookmarkDialog(self.bookmarks)
        dialog.exec_()

    def go_back(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_browser.back()

    def go_forward(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_browser.forward()

    def reload_page(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_browser.reload()

    def load_url(self):
        current_browser = self.get_current_browser()
        if current_browser:
            url = self.url_bar.text()
            if not url.startswith("http://") and not url.startswith("https://"):
                url = "https://" + url
            current_browser.setUrl(QUrl(url))

    def update_url(self, q):
        self.url_bar.setText(q.toString())

    def add_bookmark(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_url = current_browser.url().toString()
            if current_url not in self.bookmarks:
                self.bookmarks.append(current_url)
                self.save_bookmarks()

    def load_bookmarks(self):
        try:
            with open(self.bookmarks_file, "r") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def save_bookmarks(self):
        with open(self.bookmarks_file, "w") as file:
            json.dump(self.bookmarks, file)

    def init_history_db(self):
        conn = sqlite3.connect(self.history_db)
        cursor = conn.cursor()
        cursor.execute(
            """CREATE TABLE IF NOT EXISTS history (
                   id INTEGER PRIMARY KEY AUTOINCREMENT,
                   url TEXT NOT NULL,
                   timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
               )"""
        )
        conn.commit()
        conn.close()

    def save_history(self):
        current_browser = self.get_current_browser()
        if current_browser:
            current_url = current_browser.url().toString()
            conn = sqlite3.connect(self.history_db)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO history (url) VALUES (?)", (current_url,))
            conn.commit()
            conn.close()
            self.load_history()

    def load_history(self):
        conn = sqlite3.connect(self.history_db)
        cursor = conn.cursor()
        cursor.execute("SELECT url, timestamp FROM history ORDER BY id DESC")
        rows = cursor.fetchall()
        conn.close()

        self.history_table.setRowCount(len(rows))
        for row_index, row_data in enumerate(rows):
            self.history_table.setItem(row_index, 0, QTableWidgetItem(row_data[0]))
            self.history_table.setItem(row_index, 1, QTableWidgetItem(row_data[1]))

    def get_current_browser(self):
        current_widget = self.tab_widget.currentWidget()
        if isinstance(current_widget, QWebEngineView):
            return current_widget
        return None


# Apply the custom stylesheet
def apply_stylesheet(app, stylesheet_path):
    if os.path.exists(stylesheet_path):
        with open(stylesheet_path, "r") as file:
            app.setStyleSheet(file.read())


if __name__ == "__main__":
    app = QApplication(sys.argv)
    browser = CustomBrowser()

    # Load and apply the Shadow Monarch CSS theme
    stylesheet_path = "./CSS/browser-theme.css"
    apply_stylesheet(app, stylesheet_path)

    browser.show()
    sys.exit(app.exec_())
