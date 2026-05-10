# Preventivatore Desktop - Croce e Cuore

**Applicazione desktop Python** per compilare preventivi con dati azienda fissi e cliente variabile. Genera PDF strutturati e professionali.

---

## 🚀 Quick Start macOS

Copia-incolla nel Terminale (una riga):

```bash
brew install python-tk@3.14 && cd /Users/cristiandellamonica/Desktop/croceecuore/preventivatore && rm -rf .venv && python3 -m venv .venv && source .venv/bin/activate && python -m pip install --upgrade pip && pip install -r requirements.txt && python main.py
```

---

## 📦 Creare App Bundle per macOS (Preventivatore.app)

Se vuoi un'app "nativa" macOS con icona e nome nel Dock, esegui:

```bash
cd /Users/cristiandellamonica/Desktop/croceecuore/preventivatore
source .venv/bin/activate
pip install py2app
python setup.py py2app
```

Genererà: `dist/Preventivatore.app`

### Usare l'app bundle:
1. Apri Finder → Naviga a `/Users/cristiandellamonica/Desktop/croceecuore/preventivatore/dist/`
2. Doppio click su **Preventivatore.app**
3. Vedrai "Preventivatore" nel Dock con l'icona personalizzata

✅ **Vantaggi**: Icona nel Dock, nome corretto, comportamento nativo macOS


## Flusso utilizzo app

### **Step 1: Setup azienda (primo avvio)**
1. Clicca su "⚙️ Impostazioni Azienda".
2. Inserisci: Nome, Indirizzo, P.IVA, Email, Telefono, Logo.
3. Clicca "Salva Impostazioni" (i dati rimangono salvati per sempre).

### **Step 2: Compila preventivo**
1. **Dati Documento**: Numero preventivo, Data (auto compilato).
2. **Dati Cliente**: Cliente, Indirizzo, Referente/Parroco, Oggetto.
3. **Note a piè pagina**: Personalizza il testo finale (es. personalizzazioni).

### **Step 3: Aggiungi articoli**
1. Riempi Descrizione, Prezzo, Quantità, IVA %.
2. Clicca "➕ Aggiungi" (oppure "💾 Salva Modifica" se stai editando).

### **Step 4: Modifica / Rimuovi**
- **Seleziona una riga** dalla tabella in basso.
- Clicca **"✏️ Modifica"** per carare i dati nel form (cambiano il bottone e il label).
- Modifica i valori e clicca **"💾 Salva Modifica"**.
- Clicca **"❌ Rimuovi"** per cancellare la riga selezionata.

### **Step 5: Salva / Carica / Genera PDF**
- **"💾 Salva (.pquote)"** → Salva stato completo (cliente + articoli + note).
- **"📂 Apri"** → Ricarica un progetto salvato.
- **"📄 GENERA PDF"** → Crea il preventivo in PDF.
- **"🆕 Svuota Tutto"** → Resetta cliente e articoli per un nuovo preventivo.

---

## Struttura PDF generato

Il PDF include automaticamente:

- **Header**: Logo aziendale (se configurato), Nome, Indirizzo, P.IVA, Email, Telefono.
- **Titolo**: "PREVENTIVO" con Data.
- **Dati Cliente**: Cliente, Indirizzo, Referente.
- **Oggetto**: Descrizione oggetto preventivo.
- **Tabella**: Descrizione | Quantità | Prezzo cad. | Importo Tot | C.Iva (%) | Totale.
- **Footer**: "Totale preventivo euro €X.XX compreso iva, [note a piè pagina]".

---

## Impostazioni azienda (salvate localmente)

I dati azienda vengono salvati in `~/.preventivatore/settings.json` (cartella nascosta home) e rimangono fissi tra i riavvii.

**Modificare in qualsiasi momento**: Clicca "⚙️ Impostazioni Azienda".

---

## Salvataggio progetti (.pquote)

File proprietario in formato JSON. Contiene:
- Dati cliente, oggetto, note.
- Tutti gli articoli con prezzi e IVA.
- Numero e data preventivo.

Carica un progetto salvato con **"📂 Apri"**.

---

## Troubleshooting macOS

### Errore `_tkinter` mancante
Se vedi `ModuleNotFoundError: No module named '_tkinter'`:

```bash
brew install python-tk@3.14
cd /Users/cristiandellamonica/Desktop/croceecuore/preventivatore
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### App non si avvia
```bash
python3 -c "import tkinter, reportlab, PyInstaller; print('OK')"
```

Se fallisce, reinstalla l'ambiente:
```bash
rm -rf /Users/cristiandellamonica/Desktop/croceecuore/preventivatore/.venv
python3 -m venv /Users/cristiandellamonica/Desktop/croceecuore/preventivatore/.venv
source /Users/cristiandellamonica/Desktop/croceecuore/preventivatore/.venv/bin/activate
pip install -r requirements.txt
```

---

## 🎨 Icone (macOS e Windows)

L'app carica automaticamente l'icona dal sistema operativo:

### macOS / Linux
L'app cerca `assets/icon.png` e la carica come icona della finestra.

**Per usare il tuo logo:**
1. Converti il tuo logo a **PNG** (es. con Preview o ImageMagick).
2. Salva come `assets/icon.png`.
3. Riavvia l'app: `python main.py`

Esempio conversione con ImageMagick (se installato):
```bash
convert logo_solo_cuore.ico assets/icon.png
```

### Windows
L'app cerca `assets/icon.ico` e la usa come icona finestra + icona taskbar.

**Per usare il tuo logo:**
1. Salva il tuo `.ico` come `assets/icon.ico`.
2. Riavvia l'app: `python main.py`

---

## Windows (PowerShell)

```powershell
cd C:\percorso\al\progetto\preventivatore
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

### Build .exe standalone

```powershell
pyinstaller --noconfirm --clean --onefile --windowed --name Preventivatore --icon=assets/icon.ico --add-data "assets;assets" main.py
```

Output: `dist\Preventivatore.exe`



---

## 📋 Riepilogo: Come eseguire Preventivatore

| Metodo | Comando | Piattaforma | Vantaggi |
|--------|---------|------------|----------|
| **Python (sorgente)** | `python main.py` | macOS / Windows / Linux | Veloce, facile debug |
| **App Bundle** | Finder: `dist/Preventivatore.app` | macOS | Icona Dock, nome corretto, nativo |
| **EXE compilato** | `dist\Preventivatore.exe` | Windows | Distribuibile, no dipendenze |

---

## 🎯 Distribuzione (Checklist finale)

### Per macOS:
- ✅ Compilato app bundle: `dist/Preventivatore.app`
- ✅ Icona caricata automaticamente
- ✅ Nome nel Dock: "Preventivatore"
- ✅ Settings salvati in `~/.preventivatore/settings.json`

**Condividi**: Copia `dist/Preventivatore.app` su altre macchine (funziona direttamente)

### Per Windows:
**Opzione 1 - Scarica il .exe precompilato** ⭐ CONSIGLIATO
1. Vai su: https://github.com/CriDM/Preventivatore
2. Clicca su **"Actions"** nel menu in alto
3. Seleziona l'ultima build ("Build Windows EXE")
4. Scorri fino a "Artifacts" e clicca **"Preventivatore-Windows"**
5. Scarica `Preventivatore.exe` (NO dipendenze richieste!)

**Opzione 2 - Compila tu stesso** (se sei su Windows PC)
1. Clone il repository:
   ```powershell
   git clone https://github.com/CriDM/Preventivatore.git
   cd Preventivatore
   ```
2. Setup environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```
3. Compila:
   ```powershell
   pyinstaller --noconfirm --clean --onefile --windowed --name Preventivatore --icon=assets/icon.ico --add-data "assets;assets" main.py
   ```
4. Usa: `dist\Preventivatore.exe`

---

## 📋 Riepilogo: Come eseguire Preventivatore

| Metodo | Comando | Piattaforma | Vantaggi |
|--------|---------|------------|----------|
| **Python (sorgente)** | `python main.py` | macOS / Windows / Linux | Veloce, facile debug |
| **App Bundle** | Finder: `dist/Preventivatore.app` | macOS | Icona Dock, nome corretto, nativo |
| **EXE compilato** | `dist\Preventivatore.exe` | Windows | Distribuibile, no dipendenze |

---



