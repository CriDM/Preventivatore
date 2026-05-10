from setuptools import setup
from pathlib import Path

setup(
    app=["main.py"],
    name="Preventivatore",
    options={
        "py2app": {
            "iconfile": str(Path("assets/icon.png")),
            "includes": [
                "tkinter",
                "tkinter.filedialog",
                "tkinter.messagebox",
                "tkinter.ttk",
                "reportlab",
                "reportlab.lib",
                "reportlab.lib.colors",
                "reportlab.lib.pagesizes",
                "reportlab.lib.styles",
                "reportlab.lib.enums",
                "reportlab.lib.units",
                "reportlab.platypus",
                "svglib",
                "svglib.svglib",
                "decimal",
                "json",
                "pathlib",
                "datetime",
                "platform",
            ],
            "packages": [
                "reportlab",
                "svglib",
            ],
        }
    },
    version="1.0.0",
    description="Generatore di preventivi PDF per Croce e Cuore ARTE SACRA",
)
