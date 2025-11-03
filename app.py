#!/usr/bin/env python3
"""
Application entrypoint for GeoClone separated layout.

Use `python app.py` or `python web.py` to run the GUI.
"""

import tkinter as tk
from view import GeoCloneApp


def main():
    root = tk.Tk()
    app = GeoCloneApp(root)
    root.geometry("1000x650")
    root.mainloop()


if __name__ == "__main__":
    main()
