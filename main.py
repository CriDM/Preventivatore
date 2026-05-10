from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import json
import storage
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from datetime import date
import datetime
import sys
import platform

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

class PreventivoApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Preventivatore - Croce e Cuore ARTE SACRA")
        self.root.geometry("1200x800")
        self.root.minsize(1000, 700)
        self._icon_image = None

        # Imposta icona dell'app (cross-platform)
        self._set_window_icon()

        self.items = []
        
        # Percorso "nascosto" in stile vera app (nella home dell'utente)
        self.settings_dir = Path.home() / ".preventivatore"
        self.settings_file = self.settings_dir / "settings.json"
        self.settings = self._load_settings()

        self._build_header()
        
        # I pulsanti in basso vengono pacchettizzati PRIMA della tabella
        # in modo che il frame della tabella non li spinga fuori dallo schermo.
        self._build_buttons()
        self._build_client_section()
        self._build_form()
        self._build_table()

        # Se non c'è il nome azienda, è il primo avvio
        if not self.settings.get("company_name"):
            self.root.after(500, lambda: self.open_settings_dialog(first_run=True))

    def _load_settings(self) -> dict:
        if self.settings_file.exists():
            try:
                with open(self.settings_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "company_name": "",
            "company_address": "",
            "piva": "",
            "email": "",
            "phone": "",
            "logo_path": "",
            "quote_number": "1"
        }

    def _set_window_icon(self) -> None:
        """Carica l'icona della finestra (cross-platform: macOS, Windows, Linux)."""
        try:
            assets_dir = self._get_assets_dir()
            
            # Su Windows: prova ICO con iconbitmap()
            if platform.system() == "Windows":
                ico_path = assets_dir / "icon.ico"
                if ico_path.exists():
                    try:
                        # Usa il path assoluto e converte a string in formato Windows
                        icon_abs_path = str(ico_path.resolve())
                        self.root.iconbitmap(default=icon_abs_path)
                        return
                    except Exception:
                        pass  # Se fallisce, prova PNG
                
                # Se ICO non funziona, prova PNG su Windows
                png_path = assets_dir / "icon.png"
                if png_path.exists():
                    try:
                        # Carica PNG con PhotoImage
                        photo = tk.PhotoImage(file=str(png_path.resolve()))
                        self._icon_image = photo
                        self.root.iconphoto(False, photo)
                        return
                    except Exception:
                        pass
            
            # Su macOS e Linux: preferisci PNG con iconphoto()
            if platform.system() in ("Darwin", "Linux"):
                png_path = assets_dir / "icon.png"
                if png_path.exists():
                    try:
                        photo = tk.PhotoImage(file=str(png_path.resolve()))
                        self._icon_image = photo
                        self.root.iconphoto(False, photo)
                        return
                    except Exception:
                        pass
        except Exception:
            pass  # Se non riesce, continua senza icona (non critico)

    def _get_assets_dir(self) -> Path:
        # In PyInstaller one-file i file aggiuntivi sono estratti in _MEIPASS.
        base_path = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))
        return base_path / "assets"

    def _save_settings(self) -> None:
        self.settings_dir.mkdir(exist_ok=True)
        try:
            with open(self.settings_file, "w", encoding="utf-8") as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
        except Exception as exc:
            messagebox.showerror("Errore di salvataggio", f"Impossibile salvare le impostazioni:\n{exc}")

    def open_settings_dialog(self, first_run=False) -> None:
        dialog = tk.Toplevel(self.root)
        dialog.title("Setup Dati Azienda" if first_run else "Impostazioni Azienda")
        dialog.geometry("550x450")
        dialog.transient(self.root)
        dialog.grab_set()

        if first_run:
            ttk.Label(
                dialog, 
                text="Benvenuto! Inserisci i dati della tua azienda. Li salveremo per sempre.", 
                font=("Helvetica", 10, "bold")
            ).pack(pady=(10, 5))

        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Nome Azienda:").grid(row=0, column=0, sticky="w", pady=5)
        name_var = tk.StringVar(value=self.settings.get("company_name", ""))
        ttk.Entry(frame, textvariable=name_var, width=40).grid(row=0, column=1, pady=5)

        ttk.Label(frame, text="Indirizzo:").grid(row=1, column=0, sticky="w", pady=5)
        addr_var = tk.StringVar(value=self.settings.get("company_address", ""))
        ttk.Entry(frame, textvariable=addr_var, width=40).grid(row=1, column=1, pady=5)

        ttk.Label(frame, text="Partita IVA:").grid(row=2, column=0, sticky="w", pady=5)
        piva_var = tk.StringVar(value=self.settings.get("piva", ""))
        ttk.Entry(frame, textvariable=piva_var, width=40).grid(row=2, column=1, pady=5)

        ttk.Label(frame, text="Email:").grid(row=3, column=0, sticky="w", pady=5)
        email_var = tk.StringVar(value=self.settings.get("email", ""))
        ttk.Entry(frame, textvariable=email_var, width=40).grid(row=3, column=1, pady=5)

        ttk.Label(frame, text="Telefono:").grid(row=4, column=0, sticky="w", pady=5)
        phone_var = tk.StringVar(value=self.settings.get("phone", ""))
        ttk.Entry(frame, textvariable=phone_var, width=40).grid(row=4, column=1, pady=5)

        logo_var = tk.StringVar(value=self.settings.get("logo_path", ""))
        ttk.Label(frame, text="Logo Predefinito:").grid(row=5, column=0, sticky="w", pady=5)
        
        logo_frame = ttk.Frame(frame)
        logo_frame.grid(row=5, column=1, sticky="ew", pady=5)
        ttk.Entry(logo_frame, textvariable=logo_var, state="readonly").pack(side="left", fill="x", expand=True)
        
        def choose_default_logo():
            path = filedialog.askopenfilename(
                filetypes=[
                    ("Loghi supportati", ("*.png", "*.jpg", "*.jpeg", "*.svg")),
                    ("SVG", "*.svg"),
                    ("PNG", "*.png"),
                    ("JPEG", ("*.jpg", "*.jpeg")),
                    ("Tutti i file", "*.*"),
                ]
            )
            if path:
                logo_var.set(path)

        ttk.Button(logo_frame, text="Sfoglia...", command=choose_default_logo).pack(side="right", padx=(5,0))

        def save_and_close():
            self.settings["company_name"] = name_var.get().strip()
            self.settings["company_address"] = addr_var.get().strip()
            self.settings["piva"] = piva_var.get().strip()
            self.settings["email"] = email_var.get().strip()
            self.settings["phone"] = phone_var.get().strip()
            self.settings["logo_path"] = logo_var.get().strip()
            self._save_settings()
            dialog.destroy()

        ttk.Button(frame, text="Salva Impostazioni", command=save_and_close).grid(row=6, column=0, columnspan=2, pady=20)

    def increment_quote_number(self):
        current = self.quote_number_var.get().strip()
        try:
            new_num = int(current) + 1
            self.quote_number_var.set(str(new_num))
            self.settings["quote_number"] = str(new_num)
            self._save_settings()
        except ValueError:
            self.settings["quote_number"] = current
            self._save_settings()
            messagebox.showinfo("Salvato", "Formato testo salvato come predefinito.")

    def _build_header(self) -> None:
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=12, pady=(12, 0))
        
        ttk.Label(header_frame, text="Compilazione Nuovo Preventivo", font=("Helvetica", 14, "bold")).pack(side="left")
        ttk.Button(header_frame, text="⚙️ Impostazioni Azienda", command=self.open_settings_dialog).pack(side="right")

    def _build_client_section(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Dati Documento e Cliente", padding=12)
        frame.pack(fill="x", padx=12, pady=(8, 8))

        self.quote_number_var = tk.StringVar(value=self.settings.get("quote_number", "1"))
        self.quote_date_var = tk.StringVar(value=str(date.today().strftime("%d/%m/%Y")))
        
        self.customer_name_var = tk.StringVar()
        self.customer_address_var = tk.StringVar()
        self.contact_person_var = tk.StringVar()
        self.oggetto_var = tk.StringVar()
        self.final_notes_var = tk.StringVar(value="Tutti gli oggetti sopra indicati saranno personalizzati.")

        # Riga 1: N. Preventivo e Data
        ttk.Label(frame, text="Num. Preventivo:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=4)
        num_frame = ttk.Frame(frame)
        num_frame.grid(row=0, column=1, sticky="w", padx=(0, 15), pady=4)
        ttk.Entry(num_frame, textvariable=self.quote_number_var, width=10).pack(side="left")
        ttk.Button(num_frame, text="+1 Salva", command=self.increment_quote_number).pack(side="left", padx=(5, 0))

        ttk.Label(frame, text="Data:").grid(row=0, column=2, sticky="w", padx=(0, 5), pady=4)
        ttk.Entry(frame, textvariable=self.quote_date_var, width=15).grid(row=0, column=3, sticky="w", pady=4)

        # Riga 2: Cliente e Indirizzo
        ttk.Label(frame, text="Cliente:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=4)

        self.customer_combo = ttk.Combobox(frame, textvariable=self.customer_name_var, width=33)
        self.customer_combo.grid(row=1, column=1, sticky="ew", padx=(0, 15), pady=4)

        # Popoliamo la combobox con i clienti
        self._refresh_customer_combo()

        # Binding dell'evento
        self.customer_combo.bind("<<ComboboxSelected>>", self._on_customer_selected)


        ttk.Label(frame, text="Indirizzo Cliente:").grid(row=1, column=2, sticky="w", padx=(0, 5), pady=4)
        ttk.Entry(frame, textvariable=self.customer_address_var, width=35).grid(row=1, column=3, sticky="ew", pady=4)

        # Riga 3: Referente (Parroco) e Oggetto
        ttk.Label(frame, text="Referente/Parroco:").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=4)
        ttk.Entry(frame, textvariable=self.contact_person_var, width=35).grid(row=2, column=1, sticky="ew", padx=(0, 15), pady=4)

        ttk.Label(frame, text="Oggetto Preventivo:").grid(row=2, column=2, sticky="w", padx=(0, 5), pady=4)
        ttk.Entry(frame, textvariable=self.oggetto_var, width=35).grid(row=2, column=3, sticky="ew", pady=4)

        # Riga 4: Note finali
        ttk.Label(frame, text="Note a piè pagina:").grid(row=3, column=0, sticky="w", padx=(0, 5), pady=4)
        ttk.Entry(frame, textvariable=self.final_notes_var).grid(row=3, column=1, columnspan=3, sticky="ew", pady=4)

        frame.columnconfigure(1, weight=1)
        frame.columnconfigure(3, weight=1)

    def _build_form(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Aggiungi / Modifica Articolo", padding=12)
        frame.pack(fill="x", padx=12, pady=0)

        ttk.Label(frame, text="Descrizione").grid(row=0, column=0, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(frame, text="Prezzo cad. (€)").grid(row=0, column=1, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(frame, text="Quantità").grid(row=0, column=2, sticky="w", padx=(0, 8), pady=2)
        ttk.Label(frame, text="IVA %").grid(row=0, column=3, sticky="w", padx=(0, 8), pady=2)

        self.name_var = tk.StringVar()
        self.price_var = tk.StringVar()
        self.qty_var = tk.StringVar()
        self.vat_var = tk.StringVar(value="22")

        ttk.Entry(frame, textvariable=self.name_var, width=40).grid(row=1, column=0, sticky="ew", padx=(0, 8), pady=4)
        ttk.Entry(frame, textvariable=self.price_var, width=12).grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=4)
        ttk.Entry(frame, textvariable=self.qty_var, width=10).grid(row=1, column=2, sticky="ew", padx=(0, 8), pady=4)
        ttk.Entry(frame, textvariable=self.vat_var, width=8).grid(row=1, column=3, sticky="ew", padx=(0, 8), pady=4)

        ttk.Button(frame, text="➕ Aggiungi alla lista", command=self.add_item).grid(row=1, column=4, padx=(6, 0), pady=4)

        frame.columnconfigure(0, weight=1)

    def _build_table(self) -> None:
        frame = ttk.LabelFrame(self.root, text="Articoli Inseriti", padding=10)
        # expand=True permette alla tabella di occupare lo spazio rimanente, ma non spingerà fuori i bottoni già pacchettizzati
        frame.pack(fill="both", expand=True, padx=12, pady=8)

        columns = ("name", "unit_price", "quantity", "total", "vat", "total_with_vat")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", height=8)

        self.tree.heading("name", text="Descrizione")
        self.tree.heading("unit_price", text="Prezzo cad.")
        self.tree.heading("quantity", text="Quantità")
        self.tree.heading("total", text="Importo Tot")
        self.tree.heading("vat", text="C.Iva (%)")
        self.tree.heading("total_with_vat", text="Totale")

        self.tree.column("name", width=300, anchor="w")
        self.tree.column("unit_price", width=100, anchor="e")
        self.tree.column("quantity", width=80, anchor="center")
        self.tree.column("total", width=100, anchor="e")
        self.tree.column("vat", width=80, anchor="center")
        self.tree.column("total_with_vat", width=100, anchor="e")

        yscroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=yscroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        yscroll.pack(side="right", fill="y")

    def _build_buttons(self) -> None:
        # Questo frame è pacchettizzato BOTTOM, quindi starà sempre in fondo.
        # fill="x" lo fa occupare tutto lo spazio orizzontale
        frame = ttk.Frame(self.root, padding=12)
        frame.pack(side="bottom", fill="x")

        # Sezione di sinistra: Riepilogo e pulsanti tabella
        left_frame = ttk.Frame(frame)
        left_frame.pack(side="left")
        
        self.summary_var = tk.StringVar(value="Totale Generale: € 0,00")
        ttk.Label(left_frame, textvariable=self.summary_var, font=("Helvetica", 11, "bold")).pack(side="left", padx=(0, 15))
        
        ttk.Button(left_frame, text="✏️ Modifica riga", command=self.edit_selected).pack(side="left", padx=4)
        ttk.Button(left_frame, text="❌ Rimuovi", command=self.remove_selected).pack(side="left", padx=4)

        # Sezione di destra: Azioni progetto
        right_frame = ttk.Frame(frame)
        right_frame.pack(side="right")

        ttk.Button(right_frame, text="🆕 Svuota Tutto", command=self.new_project).pack(side="left", padx=4)
        ttk.Button(right_frame, text="🗄️ Archivio", command=self.show_archive_window).pack(side="left", padx=4)
        ttk.Button(right_frame, text="💾 Esporta", command=self.save_project).pack(side="left", padx=4)
        ttk.Button(right_frame, text="📂 Importa", command=self.load_project).pack(side="left", padx=4)
        ttk.Button(right_frame, text="📄 GENERA PDF", command=self.generate_pdf, style="Accent.TButton").pack(side="left", padx=(15, 0))


    def _refresh_customer_combo(self):
        customers = storage.load_customers()
        self.customer_combo['values'] = sorted(list(customers.keys()))

    def _on_customer_selected(self, event=None):
        selected = self.customer_name_var.get()
        if not selected: return
        customer_data = storage.get_customer(selected)
        if customer_data:
            self.customer_address_var.set(customer_data.get("address", ""))
            self.contact_person_var.set(customer_data.get("contact", ""))

    def _validate_fields(self):
        name = self.name_var.get().strip()
        if not name:
            raise ValueError("Il campo 'Descrizione' è obbligatorio.")

        unit_price = parse_decimal(self.price_var.get(), "Prezzo cad.")
        quantity = parse_decimal(self.qty_var.get(), "Quantità")
        vat_percent = parse_decimal(self.vat_var.get(), "IVA %")

        if unit_price < 0 or quantity <= 0 or vat_percent < 0:
            raise ValueError("Valori numerici non validi (negativi o a zero).")

        total = q(unit_price * quantity)
        total_with_vat = q(total * (Decimal("1") + (vat_percent / Decimal("100"))))

        return {
            "name": name,
            "unit_price": q(unit_price),
            "quantity": q(quantity),
            "vat_percent": q(vat_percent),
            "total": total,
            "total_with_vat": total_with_vat,
        }

    def add_item(self) -> None:
        try:
            item = self._validate_fields()
        except ValueError as exc:
            messagebox.showerror("Errore", str(exc))
            return

        self.items.append(item)
        self._insert_tree_row(item)
        self._refresh_summary()
        
        self.name_var.set("")
        self.price_var.set("")
        self.qty_var.set("")
        
    def _insert_tree_row(self, item):
        qty_str = f"{item['quantity']:,.0f}" if item['quantity'] % 1 == 0 else format_decimal(item['quantity'])
        self.tree.insert(
            "", "end",
            values=(
                item["name"],
                format_decimal(item["unit_price"]),
                qty_str,
                format_decimal(item["total"]),
                format_decimal(item["vat_percent"]),
                format_decimal(item["total_with_vat"]),
            )
        )

    def edit_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Nessuna selezione", "Seleziona un articolo dalla tabella per modificarlo.")
            return

        row_id = selected[0]
        index = self.tree.index(row_id)
        item = self.items[index]

        # Riporta i dati nei form
        self.name_var.set(item["name"])
        self.price_var.set(str(item["unit_price"]))
        self.qty_var.set(str(item["quantity"]))
        self.vat_var.set(str(item["vat_percent"]))

        # Rimuove l'articolo dalla lista e dalla tabella
        self.tree.delete(row_id)
        self.items.pop(index)
        self._refresh_summary()

    def remove_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            return
        for row_id in selected:
            index = self.tree.index(row_id)
            self.tree.delete(row_id)
            if 0 <= index < len(self.items):
                self.items.pop(index)
        self._refresh_summary()

    def _refresh_summary(self) -> None:
        generale = q(sum((item["total_with_vat"] for item in self.items), Decimal("0")))
        self.summary_var.set(f"Totale Generale: € {format_decimal(generale)}")

    def new_project(self) -> None:
        if not messagebox.askyesno("Nuovo", "Svuotare tutti i dati del cliente e della tabella?"):
            return
        self.quote_date_var.set(str(date.today().strftime("%d/%m/%Y")))
        self.customer_name_var.set("")
        self.customer_address_var.set("")
        self.contact_person_var.set("")
        self.oggetto_var.set("")
        self.items.clear()
        self.tree.delete(*self.tree.get_children())
        self._refresh_summary()

    def _serialize_items(self):
        return [{k: str(v) if isinstance(v, Decimal) else v for k, v in i.items()} for i in self.items]

    def save_project(self) -> None:
        # Salva o aggiorna in anagrafica
        storage.save_customer(
            self.customer_name_var.get(),
            self.customer_address_var.get(),
            self.contact_person_var.get()
        )
        self._refresh_customer_combo()

        path = filedialog.asksaveasfilename(defaultextension=".pquote", filetypes=[("Progetto Preventivatore", "*.pquote")])
        if not path: return
        payload = {
            "customer": {
                "name": self.customer_name_var.get(),
                "address": self.customer_address_var.get(),
                "contact": self.contact_person_var.get(),
                "oggetto": self.oggetto_var.get(),
                "quote_date": self.quote_date_var.get(),
                "notes": self.final_notes_var.get(),
            },
            "items": self._serialize_items()
        }
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(payload, fp, ensure_ascii=False, indent=2)


    def show_archive_window(self):
        archive_win = tk.Toplevel(self.root)
        archive_win.title("Archivio Preventivi Locali")
        archive_win.geometry("600x400")
        archive_win.transient(self.root)
        archive_win.grab_set()

        columns = ("filename", "date")
        tree = ttk.Treeview(archive_win, columns=columns, show="headings")
        tree.heading("filename", text="Nome File")
        tree.heading("date", text="Data Creazione")
        tree.column("filename", width=400, anchor="w")
        tree.column("date", width=150, anchor="center")

        import datetime
        quotes = storage.list_local_quotes()
        for q in quotes:
            dt_str = datetime.datetime.fromtimestamp(q["mtime"]).strftime("%d/%m/%Y %H:%M")
            tree.insert("", "end", values=(q["filename"], dt_str), tags=(q["filepath"],))

        tree.pack(fill="both", expand=True, padx=10, pady=10)

        def on_double_click(event):
            selected = tree.selection()
            if not selected: return
            filepath = tree.item(selected[0], "tags")[0]
            self._load_from_filepath(filepath)
            archive_win.destroy()

        tree.bind("<Double-1>", on_double_click)

        ttk.Label(archive_win, text="Doppio clic su un preventivo per caricarlo.").pack(pady=(0,10))

    def _load_from_filepath(self, filepath: str):
        payload = storage.load_local_quote(filepath)
        if not payload:
            messagebox.showerror("Errore", "Impossibile caricare il file.")
            return

        cust = payload.get("customer", {})
        self.customer_name_var.set(cust.get("name", ""))
        self.customer_address_var.set(cust.get("address", ""))
        self.contact_person_var.set(cust.get("contact", ""))
        self.oggetto_var.set(cust.get("oggetto", ""))
        self.quote_date_var.set(cust.get("quote_date", str(datetime.date.today().strftime("%d/%m/%Y"))))
        self.final_notes_var.set(cust.get("notes", ""))

        self.items = []
        self.tree.delete(*self.tree.get_children())
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
            self._insert_tree_row(i)
        self._refresh_summary()

    def load_project(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("Progetto Preventivatore", "*.pquote")])
        if not path: return
        with open(path, "r", encoding="utf-8") as fp:
            payload = json.load(fp)
        
        cust = payload.get("customer", {})
        self.customer_name_var.set(cust.get("name", ""))
        self.customer_address_var.set(cust.get("address", ""))
        self.contact_person_var.set(cust.get("contact", ""))
        self.oggetto_var.set(cust.get("oggetto", ""))
        self.quote_date_var.set(cust.get("quote_date", str(date.today().strftime("%d/%m/%Y"))))
        self.final_notes_var.set(cust.get("notes", ""))

        self.items = []
        self.tree.delete(*self.tree.get_children())
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
            self._insert_tree_row(i)
        self._refresh_summary()

    def generate_pdf(self) -> None:
        if not self.items:
            messagebox.showwarning("Errore", "Aggiungi articoli prima di generare il PDF.")
            return

        # Salva o aggiorna in anagrafica
        storage.save_customer(
            self.customer_name_var.get(),
            self.customer_address_var.get(),
            self.contact_person_var.get()
        )
        self._refresh_customer_combo()

        out_name = f"Preventivo_{self.quote_number_var.get()}_{self.customer_name_var.get().replace(' ','_')}.pdf"
        file_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=out_name, filetypes=[("PDF", "*.pdf")])
        if not file_path: return

        # Unisci i dati fissi (dalle settings) e quelli del cliente (dalla UI)
        doc_data = {
            "company_name": self.settings.get("company_name", ""),
            "company_address": self.settings.get("company_address", ""),
            "piva": self.settings.get("piva", ""),
            "email": self.settings.get("email", ""),
            "phone": self.settings.get("phone", ""),
            "logo_path": self.settings.get("logo_path", ""),
            
            "quote_number": self.quote_number_var.get(),
            "quote_date": self.quote_date_var.get(),
            "customer_name": self.customer_name_var.get(),
            "customer_address": self.customer_address_var.get(),
            "contact_person": self.contact_person_var.get(),
            "oggetto": self.oggetto_var.get(),
            "final_notes": self.final_notes_var.get(),
        }

        try:
            generate_quote_pdf(self.items, doc_data, file_path)

            # Salva una copia nel database locale
            payload = {
                "customer": {
                    "name": self.customer_name_var.get(),
                    "address": self.customer_address_var.get(),
                    "contact": self.contact_person_var.get(),
                    "oggetto": self.oggetto_var.get(),
                    "quote_date": self.quote_date_var.get(),
                    "notes": self.final_notes_var.get(),
                },
                "items": self._serialize_items()
            }
            storage.save_local_quote(payload, self.quote_number_var.get(), self.customer_name_var.get())

            messagebox.showinfo("Fatto!", f"PDF generato:\n{file_path}")
        except Exception as exc:
            messagebox.showerror("Errore PDF", str(exc))

def main() -> None:
    root = tk.Tk()
    style = ttk.Style(root)
    if "vista" in style.theme_names():
        style.theme_use("vista")
    app = PreventivoApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()