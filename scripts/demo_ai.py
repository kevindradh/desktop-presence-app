"""Run the explicit memory-only AI lab. No connection to any database."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))


def main():
    from PyQt6.QtWidgets import QApplication
    from app.settings.config import load_config
    from app.ui.theme import apply_theme
    from app.ui.ai_lab import AiLab
    app=QApplication([])
    config=load_config(ROOT)
    apply_theme(app)
    window=AiLab(config)
    app.aboutToQuit.connect(window.cameras.shutdown_now)
    app.aboutToQuit.connect(window.inference.shutdown_now)
    window.show()
    return app.exec()


if __name__=="__main__":
    raise SystemExit(main())
