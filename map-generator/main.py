"""Entry point for the Salvage Union Map Generator."""
import sys
from pathlib import Path

# Ensure the project root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).parent))

import generators._registry  # noqa: F401  — triggers all generator registrations

from PySide6.QtWidgets import QApplication
from app.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("SU Map Generator")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
