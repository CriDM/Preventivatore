import sys
import os
import json
import tempfile
import threading
import subprocess
import platform
from pathlib import Path
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from datetime import date, datetime

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFormLayout, QLabel, QLineEdit, QPushButton, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog, QMessageBox,
    QFileDialog, QGroupBox, QAbstractItemView, QFrame
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QShortcut, QKeySequence

import storage
import woo_sync
from pdf_generator import generate_quote_pdf

TWOPLACES = Decimal("0.01")

def q(value: Decimal) -> Decimal:
    return value.quantize(TWOPLACES, rounding=ROUND_HALF_UP)

def parse_decimal(text: str, field_name: str) -> Decimal:
    cleaned = text.strip().replace(" ", "").replace(",", ".")
    if not cleaned:
        raise ValueError(f"Il campo '{field_name}' è obbligatorio.")
    try:
        return Decimal(cleaned)
    except InvalidOperation as exc:
        raise ValueError(f"Il campo '{field_name}' deve essere numerico.") from exc

def format_decimal(value: Decimal) -> str:
    return f"{q(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class SettingsDialog(QDialog):
    def __init__(self, parent, settings, first_run=False):
        super().__init__(parent)
        self.settings = settings
        self.parent_app = parent
        
        self.setWindowTitle("Setup Dati Azienda" if first_run else "Impostazioni Azienda")
        self.resize(600, 500)
        
        layout = QVBoxLayout(self)

        if first_run:
            welcome_lbl = QLabel("Benvenuto! Inserisci i dati della tua azienda. Li salveremo per sempre.")
            welcome_lbl.setStyleSheet("font-weight: bold; margin-bottom: 10px;")
            layout.addWidget(welcome_lbl)

        form_layout = QFormLayout()

        self.name_edit = QLineEdit(self.settings.get("company_name", ""))
        self.addr_edit = QLineEdit(self.settings.get("company_address", ""))
        self.piva_edit = QLineEdit(self.settings.get("piva", ""))
        self.email_edit = QLineEdit(self.settings.get("email", ""))
        self.phone_edit = QLineEdit(self.settings.get("phone", ""))

        form_layout.addRow("Nome Azienda:", self.name_edit)
        form_layout.addRow("Indirizzo:", self.addr_edit)
        form_layout.addRow("Partita IVA:", self.piva_edit)
        form_layout.addRow("Email:", self.email_edit)
        form_layout.addRow("Telefono:", self.phone_edit)

        # Logo path
        logo_layout = QHBoxLayout()
        self.logo_edit = QLineEdit(self.settings.get("logo_path", ""))
        self.logo_edit.setReadOnly(True)
        browse_btn = QPushButton("Sfoglia...")
        browse_btn.clicked.connect(self._choose_logo)
        logo_layout.addWidget(self.logo_edit)
        logo_layout.addWidget(browse_btn)

        form_layout.addRow("Logo Predefinito:", logo_layout)

        # Divider
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        form_layout.addRow(line)

        woo_lbl = QLabel("Integrazione WooCommerce")
        woo_lbl.setStyleSheet("font-weight: bold; margin-top: 10px; margin-bottom: 5px;")
        form_layout.addRow(woo_lbl)

        self.woo_url_edit = QLineEdit(self.settings.get("woo_url", ""))
        self.woo_key_edit = QLineEdit(self.settings.get("woo_key", ""))
        self.woo_secret_edit = QLineEdit(self.settings.get("woo_secret", ""))
        self.woo_secret_edit.setEchoMode(QLineEdit.Password)

        form_layout.addRow("URL Sito:", self.woo_url_edit)
        form_layout.addRow("Consumer Key:", self.woo_key_edit)
        form_layout.addRow("Consumer Secret:", self.woo_secret_edit)

        # Woo Sync
        sync_layout = QHBoxLayout()
        self.sync_btn = QPushButton("🔄 Sincronizza Prodotti")
        self.sync_btn.clicked.connect(self._run_sync)
        self.sync_lbl = QLabel("")
        sync_layout.addWidget(self.sync_btn)
        sync_layout.addWidget(self.sync_lbl)
        sync_layout.addStretch()

        form_layout.addRow(sync_layout)

        layout.addLayout(form_layout)

        # Bottom Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Salva Impostazioni")
        save_btn.clicked.connect(self._save_and_close)

        export_btn = QPushButton("Esporta Settings")
        export_btn.clicked.connect(self._export_settings)

        import_btn = QPushButton("Importa Settings")
        import_btn.clicked.connect(self._import_settings)

        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(import_btn)

        layout.addLayout(btn_layout)

    def _choose_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Scegli Logo", "",
            "Images (*.png *.jpg *.jpeg *.svg);;All Files (*.*)"
        )
        if file_path:
            self.logo_edit.setText(file_path)

    def _save_and_close(self):
        self.settings["company_name"] = self.name_edit.text().strip()
        self.settings["company_address"] = self.addr_edit.text().strip()
        self.settings["piva"] = self.piva_edit.text().strip()
        self.settings["email"] = self.email_edit.text().strip()
        self.settings["phone"] = self.phone_edit.text().strip()
        self.settings["logo_path"] = self.logo_edit.text().strip()
        self.settings["woo_url"] = self.woo_url_edit.text().strip()
        self.settings["woo_key"] = self.woo_key_edit.text().strip()
        self.settings["woo_secret"] = self.woo_secret_edit.text().strip()

        self.parent_app._save_settings()
        self.accept()

    def _export_settings(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "Esporta Settings", "preventivatore_settings.json", "JSON (*.json)"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(self.settings, f, ensure_ascii=False, indent=2)
                QMessageBox.information(self, "Successo", "Impostazioni esportate correttamente!")
            except Exception as exc:
                QMessageBox.critical(self, "Errore", f"Impossibile esportare:\n{exc}")

    def _import_settings(self):
        path, _ = QFileDialog.getOpenFileName(self, "Importa Settings", "", "JSON (*.json)")
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    new_settings = json.load(f)
                self.settings.update(new_settings)
                self.parent_app._save_settings()

                # Update UI fields with new settings
                self.name_edit.setText(self.settings.get("company_name", ""))
                self.addr_edit.setText(self.settings.get("company_address", ""))
                self.piva_edit.setText(self.settings.get("piva", ""))
                self.email_edit.setText(self.settings.get("email", ""))
                self.phone_edit.setText(self.settings.get("phone", ""))
                self.logo_edit.setText(self.settings.get("logo_path", ""))
                self.woo_url_edit.setText(self.settings.get("woo_url", ""))
                self.woo_key_edit.setText(self.settings.get("woo_key", ""))
                self.woo_secret_edit.setText(self.settings.get("woo_secret", ""))

                QMessageBox.information(self, "Successo", "Impostazioni importate correttamente!")
            except Exception as exc:
                QMessageBox.critical(self, "Errore", f"Impossibile importare:\n{exc}")

    def _run_sync(self):
        url = self.woo_url_edit.text().strip()
        key = self.woo_key_edit.text().strip()
        secret = self.woo_secret_edit.text().strip()
        if not url or not key or not secret:
            QMessageBox.critical(self, "Errore", "Inserisci URL, Key e Secret per sincronizzare.")
            return

        self.sync_btn.setEnabled(False)
        self.sync_lbl.setText("Sincronizzazione in corso...")
        self.sync_lbl.setStyleSheet("color: blue;")

        def update_status(msg):
            QTimer.singleShot(0, lambda: self.sync_lbl.setText(msg))

        def fetch_thread():
            try:
                products = woo_sync.fetch_woocommerce_products(url, key, secret, update_callback=update_status)
                storage.save_woo_products(products)
                QTimer.singleShot(0, lambda: self._on_sync_success(products))
            except Exception as e:
                QTimer.singleShot(0, lambda: self._on_sync_error(str(e)))

        threading.Thread(target=fetch_thread, daemon=True).start()

    def _on_sync_success(self, products):
        self.parent_app.woo_products = products
        self.parent_app._update_woo_autocomplete()
        self.sync_lbl.setText("Sincronizzazione completata.")
        self.sync_lbl.setStyleSheet("color: green;")
        self.sync_btn.setEnabled(True)

    def _on_sync_error(self, err_msg):
        self.sync_lbl.setText(f"Errore: {err_msg}")
        self.sync_lbl.setStyleSheet("color: red;")
        self.sync_btn.setEnabled(True)


class PreventivoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Preventivatore - Croce e Cuore ARTE SACRA")
        self.resize(1200, 800)
        self.setMinimumSize(1000, 700)

        self.items = []

        # Settings Directory
        self.settings_dir = Path.home() / ".preventivatore"
        self.settings_file = self.settings_dir / "settings.json"

        self.settings = self._load_settings()
        self.woo_products = storage.load_woo_products()

        self._set_window_icon()

        self.shortcut_save = QShortcut(QKeySequence("Ctrl+S"), self)
        self.shortcut_save.activated.connect(self.save_project)

        self.shortcut_pdf = QShortcut(QKeySequence("Ctrl+P"), self)
        self.shortcut_pdf.activated.connect(self.generate_pdf)


        # Main Widget and Layout
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

    def _load_settings(self) -> dict:
        if not self.settings_file.exists():
            return {}
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _save_settings(self) -> None:
        self.settings_dir.mkdir(exist_ok=True)
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            QMessageBox.critical(self, "Errore di salvataggio", f"Impossibile salvare:\n{exc}")

    def _set_window_icon(self):
        # Implementation for setting the icon
        pass

    def open_settings_dialog(self, first_run=False):
        dialog = SettingsDialog(self, self.settings, first_run)
        dialog.exec()

    def _update_woo_autocomplete(self):
        # Placeholder for autocomplete logic
        pass


    def _build_header(self):
        header_layout = QHBoxLayout()
        title_lbl = QLabel("Compilazione Nuovo Preventivo")
        title_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        settings_btn = QPushButton("⚙️ Impostazioni Azienda")
        settings_btn.clicked.connect(lambda: self.open_settings_dialog())
        
        header_layout.addWidget(title_lbl)
        header_layout.addStretch()
        header_layout.addWidget(settings_btn)

        self.main_layout.addLayout(header_layout)

    def _build_client_section(self):
        client_group = QGroupBox("Dati Documento e Cliente")
        client_layout = QGridLayout(client_group)

        # Document Data
        client_layout.addWidget(QLabel("Numero Preventivo:"), 0, 0)

        quote_num_layout = QHBoxLayout()
        self.quote_number_edit = QLineEdit(self.settings.get("quote_number", "1"))
        self.quote_number_edit.textChanged.connect(self._save_draft)

        inc_btn = QPushButton("+1")
        inc_btn.setFixedWidth(40)
        inc_btn.clicked.connect(self._increment_quote_number)

        quote_num_layout.addWidget(self.quote_number_edit)
        quote_num_layout.addWidget(inc_btn)
        client_layout.addLayout(quote_num_layout, 0, 1)

        client_layout.addWidget(QLabel("Data:"), 0, 2)
        self.quote_date_edit = QLineEdit(date.today().strftime("%d/%m/%Y"))
        self.quote_date_edit.textChanged.connect(self._save_draft)
        client_layout.addWidget(self.quote_date_edit, 0, 3)

        # Customer Data
        client_layout.addWidget(QLabel("Cliente:"), 1, 0)
        self.customer_combo = QComboBox()
        self.customer_combo.setEditable(True)
        self.customer_combo.setInsertPolicy(QComboBox.NoInsert)
        self.customer_combo.currentTextChanged.connect(self._on_customer_change)
        self.customer_combo.currentTextChanged.connect(self._save_draft)
        client_layout.addWidget(self.customer_combo, 1, 1, 1, 3)

        client_layout.addWidget(QLabel("Indirizzo:"), 2, 0)
        self.customer_address_edit = QLineEdit()
        self.customer_address_edit.textChanged.connect(self._save_draft)
        client_layout.addWidget(self.customer_address_edit, 2, 1, 1, 3)

        client_layout.addWidget(QLabel("Referente/Parroco:"), 3, 0)
        self.contact_person_edit = QLineEdit()
        self.contact_person_edit.textChanged.connect(self._save_draft)
        client_layout.addWidget(self.contact_person_edit, 3, 1, 1, 3)

        client_layout.addWidget(QLabel("Oggetto:"), 4, 0)
        self.oggetto_edit = QLineEdit()
        self.oggetto_edit.textChanged.connect(self._save_draft)
        client_layout.addWidget(self.oggetto_edit, 4, 1, 1, 3)

        client_layout.addWidget(QLabel("Note finali:"), 5, 0)
        self.final_notes_edit = QLineEdit()
        self.final_notes_edit.textChanged.connect(self._save_draft)
        client_layout.addWidget(self.final_notes_edit, 5, 1, 1, 3)

        self.main_layout.addWidget(client_group)
        self._refresh_customer_combo()

    def _increment_quote_number(self):
        val = self.quote_number_edit.text().strip()
        if val.isdigit():
            self.quote_number_edit.setText(str(int(val) + 1))

    def _refresh_customer_combo(self):
        self.customer_combo.blockSignals(True)
        current = self.customer_combo.currentText()
        self.customer_combo.clear()

        db = storage.load_customers()
        names = sorted(list(db.keys()))
        self.customer_combo.addItems([""] + names)

        self.customer_combo.setCurrentText(current)
        self.customer_combo.blockSignals(False)

    def _on_customer_change(self, text):
        if self._loading_draft:
            return
        if not text:
            return
        data = storage.get_customer(text)
        if data:
            self.customer_address_edit.setText(data.get("address", ""))
            self.contact_person_edit.setText(data.get("contact", ""))


    def _build_form(self):
        form_group = QGroupBox("Aggiungi / Modifica Articolo")
        form_layout = QGridLayout(form_group)
        
        form_layout.addWidget(QLabel("Descrizione (Cerca in Woo)"), 0, 0)
        form_layout.addWidget(QLabel("Prezzo cad. (€)"), 0, 1)
        form_layout.addWidget(QLabel("Quantità"), 0, 2)
        form_layout.addWidget(QLabel("IVA %"), 0, 3)
        
        self.desc_combo = QComboBox()
        self.desc_combo.setEditable(True)
        self.desc_combo.setInsertPolicy(QComboBox.NoInsert)
        self.desc_combo.lineEdit().returnPressed.connect(self.add_item)

        self.price_edit = QLineEdit()
        self.price_edit.returnPressed.connect(self.add_item)

        self.qty_edit = QLineEdit()
        self.qty_edit.returnPressed.connect(self.add_item)

        self.vat_edit = QLineEdit("22")
        self.vat_edit.returnPressed.connect(self.add_item)

        form_layout.addWidget(self.desc_combo, 1, 0)
        form_layout.addWidget(self.price_edit, 1, 1)
        form_layout.addWidget(self.qty_edit, 1, 2)
        form_layout.addWidget(self.vat_edit, 1, 3)

        self.add_btn = QPushButton("➕ Aggiungi")
        self.add_btn.clicked.connect(self.add_item)
        form_layout.addWidget(self.add_btn, 1, 4)

        self.main_layout.addWidget(form_group)
        self._update_woo_autocomplete()

    def _update_woo_autocomplete(self):
        self.desc_combo.clear()
        if hasattr(self, 'woo_products'):
            names = [p.get("name", "") for p in self.woo_products]
            self.desc_combo.addItems([""] + names)

    def _build_table(self):
        table_group = QGroupBox("Articoli Inseriti")
        table_layout = QVBoxLayout(table_group)
        
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels([
            "Descrizione", "Prezzo cad.", "Quantità",
            "Importo Tot", "C.Iva (%)", "Totale"
        ])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, 6):
            self.table.horizontalHeader().setSectionResizeMode(i, QHeaderView.ResizeToContents)

        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.table.itemChanged.connect(self._on_item_changed)
        
        table_layout.addWidget(self.table)
        self.main_layout.addWidget(table_group, 1) # Give it stretch priority


    def _validate_fields(self):
        name = self.desc_combo.currentText().strip()
        if not name:
            raise ValueError("Il campo 'Descrizione' è obbligatorio.")

        unit_price = parse_decimal(self.price_edit.text(), "Prezzo cad.")
        quantity = parse_decimal(self.qty_edit.text(), "Quantità")
        vat_percent = parse_decimal(self.vat_edit.text(), "IVA %")

        total = q(unit_price * quantity)
        vat_amount = q(total * (vat_percent / Decimal("100")))
        total_with_vat = q(total + vat_amount)

        return {
            "name": name,
            "unit_price": unit_price,
            "quantity": quantity,
            "vat_percent": vat_percent,
            "total": total,
            "total_with_vat": total_with_vat
        }

    def add_item(self):
        try:
            item = self._validate_fields()
        except ValueError as exc:
            QMessageBox.critical(self, "Errore", str(exc))
            return

        self.items.append(item)
        self._insert_table_row(item)
        self._refresh_summary()
        self._save_draft()
        
        self.desc_combo.setCurrentText("")
        self.price_edit.clear()
        self.qty_edit.clear()
        self.vat_edit.setText("22")

    def _insert_table_row(self, item, row=None):
        self.table.blockSignals(True)
        
        if row is None:
            row = self.table.rowCount()
            self.table.insertRow(row)

        qty_str = f"{item['quantity']:,.0f}" if item['quantity'] % 1 == 0 else format_decimal(item['quantity'])

        items_data = [
            (item["name"], Qt.AlignLeft),
            (format_decimal(item["unit_price"]), Qt.AlignRight),
            (qty_str, Qt.AlignCenter),
            (format_decimal(item["total"]), Qt.AlignRight),
            (format_decimal(item["vat_percent"]), Qt.AlignCenter),
            (format_decimal(item["total_with_vat"]), Qt.AlignRight),
        ]

        for col, (text, alignment) in enumerate(items_data):
            cell = QTableWidgetItem(text)
            cell.setTextAlignment(alignment | Qt.AlignVCenter)

            # Make only specific columns editable
            if col not in [0, 1, 2, 4]:
                cell.setFlags(cell.flags() & ~Qt.ItemIsEditable)

            self.table.setItem(row, col, cell)

        self.table.blockSignals(False)

    def _on_cell_double_clicked(self, row, col):
        # Native editing handles inline editing due to ItemIsEditable flags
        pass

    def _on_item_changed(self, item_widget):
        row = item_widget.row()
        col = item_widget.column()

        if row >= len(self.items):
            return

        item = self.items[row]
        new_text = item_widget.text()

        try:
            if col == 0:
                item["name"] = new_text.strip()
            elif col == 1:
                item["unit_price"] = parse_decimal(new_text, "Prezzo")
            elif col == 2:
                item["quantity"] = parse_decimal(new_text, "Quantità")
            elif col == 4:
                item["vat_percent"] = parse_decimal(new_text, "IVA")
        except ValueError:
            # Revert to old value if invalid
            self._insert_table_row(item, row)
            return

        # Recalculate
        item["total"] = q(item["unit_price"] * item["quantity"])
        vat_amount = q(item["total"] * (item["vat_percent"] / Decimal("100")))
        item["total_with_vat"] = q(item["total"] + vat_amount)

        self.items[row] = item
        self._insert_table_row(item, row)
        self._refresh_summary()
        self._save_draft()

    def remove_selected(self):
        selected_rows = set(item.row() for item in self.table.selectedItems())
        if not selected_rows:
            return

        for row in sorted(selected_rows, reverse=True):
            self.table.removeRow(row)
            del self.items[row]

        self._refresh_summary()
        self._save_draft()


    def _build_buttons(self):
        btn_layout = QHBoxLayout()

        # Left side
        self.summary_lbl = QLabel("Totale Generale: € 0,00")
        self.summary_lbl.setStyleSheet("font-size: 14px; font-weight: bold;")

        remove_btn = QPushButton("❌ Rimuovi")
        remove_btn.clicked.connect(self.remove_selected)

        btn_layout.addWidget(self.summary_lbl)
        btn_layout.addWidget(remove_btn)
        btn_layout.addStretch()

        # Right side
        new_btn = QPushButton("🆕 Svuota Tutto")
        new_btn.clicked.connect(self.new_project)

        open_btn = QPushButton("📂 Apri Archivio")
        open_btn.clicked.connect(self.show_archive_window)

        export_btn = QPushButton("💾 Salva (.pquote)")
        export_btn.clicked.connect(self.save_project)

        import_btn = QPushButton("📥 Importa")
        import_btn.clicked.connect(self.load_project)

        pdf_btn = QPushButton("📄 GENERA PDF")
        pdf_btn.setStyleSheet("background-color: #2e7d32; color: white; font-weight: bold;")
        pdf_btn.clicked.connect(self.generate_pdf)

        btn_layout.addWidget(new_btn)
        btn_layout.addWidget(open_btn)
        btn_layout.addWidget(export_btn)
        btn_layout.addWidget(import_btn)
        btn_layout.addWidget(pdf_btn)

        self.main_layout.addLayout(btn_layout)

    def _refresh_summary(self):
        generale = q(sum((item["total_with_vat"] for item in self.items), Decimal("0")))
        self.summary_lbl.setText(f"Totale Generale: € {format_decimal(generale)}")

    def new_project(self):
        rep = QMessageBox.question(
            self, "Nuovo", "Svuotare tutti i dati del cliente e della tabella?",
            QMessageBox.Yes | QMessageBox.No
        )
        if rep == QMessageBox.No:
            return

        self.quote_date_edit.setText(date.today().strftime("%d/%m/%Y"))
        self.customer_combo.setCurrentText("")
        self.customer_address_edit.clear()
        self.contact_person_edit.clear()
        self.oggetto_edit.clear()
        self.final_notes_edit.clear()

        self.items.clear()
        self.table.setRowCount(0)
        self._refresh_summary()
        self._delete_draft()

    def _serialize_items(self):
        return [{k: str(v) if isinstance(v, Decimal) else v for k, v in i.items()} for i in self.items]

    def save_project(self):
        # Salva in anagrafica
        storage.save_customer(
            self.customer_combo.currentText(),
            self.customer_address_edit.text(),
            self.contact_person_edit.text()
        )
        self._refresh_customer_combo()

        path, _ = QFileDialog.getSaveFileName(
            self, "Salva Progetto", "", "Progetto Preventivatore (*.pquote)"
        )
        if not path:
            return

        payload = {
            "customer": {
                "name": self.customer_combo.currentText(),
                "address": self.customer_address_edit.text(),
                "contact": self.contact_person_edit.text(),
                "oggetto": self.oggetto_edit.text(),
                "quote_date": self.quote_date_edit.text(),
                "notes": self.final_notes_edit.text(),
            },
            "items": self._serialize_items()
        }

        try:
            with open(path, "w", encoding="utf-8") as fp:
                json.dump(payload, fp, ensure_ascii=False, indent=2)
            QMessageBox.information(self, "Salvato", f"Progetto salvato con successo:\n{path}")
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Impossibile salvare il progetto:\n{e}")

    def load_project(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Apri Progetto", "", "Progetto Preventivatore (*.pquote)"
        )
        if not path:
            return
        self._load_from_filepath(path)

    def _load_from_filepath(self, filepath: str):
        self._loading_draft = True
        try:
            payload = storage.load_local_quote(filepath)
            if not payload:
                # try normal json load if it wasn't from local archive format
                with open(filepath, "r", encoding="utf-8") as fp:
                    payload = json.load(fp)

            if not payload:
                QMessageBox.critical(self, "Errore", "Impossibile caricare il file.")
                return

            cust = payload.get("customer", {})
            self.customer_combo.setCurrentText(cust.get("name", ""))
            self.customer_address_edit.setText(cust.get("address", ""))
            self.contact_person_edit.setText(cust.get("contact", ""))
            self.oggetto_edit.setText(cust.get("oggetto", ""))
            self.quote_date_edit.setText(cust.get("quote_date", date.today().strftime("%d/%m/%Y")))
            self.final_notes_edit.setText(cust.get("notes", ""))

            self.items.clear()
            self.table.setRowCount(0)

            for item in payload.get("items", []):
                i = {
                    "name": str(item["name"]),
                    "unit_price": q(Decimal(str(item["unit_price"]))),
                    "quantity": q(Decimal(str(item["quantity"]))),
                    "vat_percent": q(Decimal(str(item["vat_percent"]))),
                    "total": q(Decimal(str(item["total"]))),
                    "total_with_vat": q(Decimal(str(item["total_with_vat"]))),
                }
                self.items.append(i)
                self._insert_table_row(i)

            self._refresh_summary()
        except Exception as e:
            QMessageBox.critical(self, "Errore", f"Errore durante il caricamento:\n{e}")
        finally:
            self._loading_draft = False

    def show_archive_window(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Archivio Preventivi Locali")
        dialog.resize(600, 400)
        
        layout = QVBoxLayout(dialog)

        table = QTableWidget(0, 2)
        table.setHorizontalHeaderLabels(["Nome File", "Data Creazione"])
        table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        table.setSelectionBehavior(QAbstractItemView.SelectRows)
        table.setEditTriggers(QAbstractItemView.NoEditTriggers)

        quotes = storage.list_local_quotes()
        for q_data in quotes:
            row = table.rowCount()
            table.insertRow(row)

            dt_str = datetime.fromtimestamp(q_data["mtime"]).strftime("%d/%m/%Y %H:%M")

            item1 = QTableWidgetItem(q_data["filename"])
            item1.setData(Qt.UserRole, q_data["filepath"])

            item2 = QTableWidgetItem(dt_str)
            item2.setTextAlignment(Qt.AlignCenter)

            table.setItem(row, 0, item1)
            table.setItem(row, 1, item2)

        layout.addWidget(table)
        layout.addWidget(QLabel("Doppio clic su un preventivo per caricarlo."))

        def on_double_click(row, col):
            item = table.item(row, 0)
            filepath = item.data(Qt.UserRole)
            self._load_from_filepath(filepath)
            dialog.accept()

        table.cellDoubleClicked.connect(on_double_click)
        dialog.exec()

    def _get_doc_data(self) -> dict:
        return {
            "company_name": self.settings.get("company_name", ""),
            "company_address": self.settings.get("company_address", ""),
            "piva": self.settings.get("piva", ""),
            "email": self.settings.get("email", ""),
            "phone": self.settings.get("phone", ""),
            "logo_path": self.settings.get("logo_path", ""),
            
            "quote_number": self.quote_number_edit.text(),
            "quote_date": self.quote_date_edit.text(),
            "customer_name": self.customer_combo.currentText(),
            "customer_address": self.customer_address_edit.text(),
            "contact_person": self.contact_person_edit.text(),
            "oggetto": self.oggetto_edit.text(),
            "final_notes": self.final_notes_edit.text(),
        }

    def generate_pdf(self):
        if not self.items:
            QMessageBox.warning(self, "Errore", "Aggiungi articoli prima di generare il PDF.")
            return

        storage.save_customer(
            self.customer_combo.currentText(),
            self.customer_address_edit.text(),
            self.contact_person_edit.text()
        )
        self._refresh_customer_combo()

        out_name = f"Preventivo_{self.quote_number_edit.text()}_{self.customer_combo.currentText().replace(' ','_')}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            self, "Salva PDF", out_name, "PDF (*.pdf)"
        )

        if not file_path:
            return

        try:
            generate_quote_pdf(self.items, self._get_doc_data(), file_path)

            payload = {
                "customer": {
                    "name": self.customer_combo.currentText(),
                    "address": self.customer_address_edit.text(),
                    "contact": self.contact_person_edit.text(),
                    "oggetto": self.oggetto_edit.text(),
                    "quote_date": self.quote_date_edit.text(),
                    "notes": self.final_notes_edit.text(),
                },
                "items": self._serialize_items()
            }
            storage.save_local_quote(payload, self.quote_number_edit.text(), self.customer_combo.currentText())
            self._delete_draft()

            QMessageBox.information(self, "Fatto!", f"PDF generato:\n{file_path}")

            try:
                if platform.system() == "Windows":
                    os.startfile(file_path)
                elif platform.system() == "Darwin":
                    subprocess.call(["open", file_path])
                else:
                    subprocess.call(["xdg-open", file_path])
            except Exception as e:
                print(f"Preview error: {e}")

        except Exception as exc:
            QMessageBox.critical(self, "Errore PDF", str(exc))


    def _save_draft(self, *args):
        if getattr(self, "_loading_draft", False):
            return

        payload = {
            "customer": {
                "name": self.customer_combo.currentText(),
                "address": self.customer_address_edit.text(),
                "contact": self.contact_person_edit.text(),
                "oggetto": self.oggetto_edit.text(),
                "quote_date": self.quote_date_edit.text(),
                "notes": self.final_notes_edit.text(),
            },
            "items": self._serialize_items()
        }
        try:
            with open(self.settings_dir / "draft.pquote", "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def _delete_draft(self):
        draft_file = self.settings_dir / "draft.pquote"
        if draft_file.exists():
            try:
                draft_file.unlink()
            except Exception:
                pass

    def _check_and_load_draft(self):
        draft_file = self.settings_dir / "draft.pquote"
        if not draft_file.exists():
            if not self.settings.get("company_name"):
                QTimer.singleShot(500, lambda: self.open_settings_dialog(first_run=True))
            return

        try:
            with open(draft_file, "r", encoding="utf-8") as f:
                payload = json.load(f)

            has_data = False
            cust = payload.get("customer", {})
            if any(cust.values()) or payload.get("items"):
                has_data = True

            if has_data:
                rep = QMessageBox.question(
                    self, "Bozza trovata",
                    "È stata trovata una bozza non salvata.\nVuoi ripristinarla?",
                    QMessageBox.Yes | QMessageBox.No
                )
                if rep == QMessageBox.Yes:
                    self._load_from_filepath(str(draft_file))
                else:
                    self._delete_draft()
                    if not self.settings.get("company_name"):
                        QTimer.singleShot(500, lambda: self.open_settings_dialog(first_run=True))
        except Exception:
            self._delete_draft()

def main():
    app = QApplication(sys.argv)

    # Modern UI setup
    app.setStyle("Fusion")

    window = PreventivoApp()

    # Needs to be called before showing the window in PySide to set it up
    window._build_header()
    window._build_client_section()
    window._build_form()
    window._build_table()
    window._build_buttons()

    window.show()

    # Add a short delay to check for draft to ensure the window is loaded
    QTimer.singleShot(100, window._check_and_load_draft)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()
