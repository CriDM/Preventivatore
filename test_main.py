import sys
from unittest.mock import MagicMock

# Mock PySide6 and other GUI related imports that might fail in headless environment
sys.modules["PySide6"] = MagicMock()
sys.modules["PySide6.QtWidgets"] = MagicMock()
sys.modules["PySide6.QtCore"] = MagicMock()
sys.modules["PySide6.QtGui"] = MagicMock()
sys.modules["reportlab"] = MagicMock()
sys.modules["reportlab.lib"] = MagicMock()
sys.modules["reportlab.lib.colors"] = MagicMock()
sys.modules["reportlab.lib.pagesizes"] = MagicMock()
sys.modules["reportlab.lib.styles"] = MagicMock()
sys.modules["reportlab.lib.enums"] = MagicMock()
sys.modules["reportlab.lib.units"] = MagicMock()
sys.modules["reportlab.platypus"] = MagicMock()
sys.modules["svglib"] = MagicMock()
sys.modules["svglib.svglib"] = MagicMock()

from decimal import Decimal
from main import format_decimal

def test_format_decimal_basic():
    assert format_decimal(Decimal("1.23")) == "1,23"

def test_format_decimal_thousands():
    assert format_decimal(Decimal("1234.56")) == "1.234,56"

def test_format_decimal_large():
    assert format_decimal(Decimal("1000000")) == "1.000.000,00"

def test_format_decimal_rounding_down():
    assert format_decimal(Decimal("1.234")) == "1,23"

def test_format_decimal_rounding_up():
    assert format_decimal(Decimal("1.235")) == "1,24"

def test_format_decimal_zero():
    assert format_decimal(Decimal("0")) == "0,00"

def test_format_decimal_negative():
    assert format_decimal(Decimal("-1234.56")) == "-1.234,56"

def test_format_decimal_single_digit_integer():
    assert format_decimal(Decimal("5")) == "5,00"
