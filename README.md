# Invoice Renamer Pro

> Automatically renames scanned invoice PDFs using OCR — built for high-volume invoice processing.

---

## What It Does

At Farmers Choice and similar businesses, hundreds to thousands of scanned invoice PDFs arrive daily with generic filenames like `scan001.pdf`. This tool reads each PDF using OCR (Optical Character Recognition), extracts the invoice number, and renames the file automatically.

**Before:**
```
scan001.pdf
scan002.pdf
document(3).pdf
```

**After:**
```
IN00691347.pdf
IN00689027.pdf
BSI0012345.pdf
```

---

## Supported Invoice Formats

| Format | Example |
|--------|---------|
| IN + 8 digits | `IN00691347` |
| BSI + 7 digits | `BSI0012345` |

---

## Features

- 🖥️ Clean GUI — no command line needed for daily use
- 🔍 OCR with automatic correction for common misreads (O→0, l→I, etc.)
- ⚡ Multi-threaded — processes multiple PDFs simultaneously
- 💾 RAM-efficient — safe on 8GB machines
- 📋 Full rename log saved after every run
- ▶️ Resume — skips already-processed files if interrupted
- ⚙️ Adjustable threads (1/2/4) and DPI (150/200/300)
- 🔌 Portable — runs from USB or external drive

---

## Requirements

### Software
- Python 3.10+
- [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) (Windows 64-bit installer)

### Python Libraries
```
pip install pymupdf pytesseract Pillow tqdm
```

---

## Installation

1. **Install Python** from [python.org](https://python.org)
   - ✅ Tick **"Add Python to PATH"** during install

2. **Install Tesseract OCR** from [UB Mannheim](https://github.com/UB-Mannheim/tesseract/wiki)
   - Install to default location: `C:\Program Files\Tesseract-OCR\`

3. **Install Python libraries**
   ```
   pip install pymupdf pytesseract Pillow tqdm
   ```

4. **Run the app**
   ```
   python invoice_renamer_gui.py
   ```

---

## Usage

1. Open the app
2. Click **Browse** to select your invoice folder
3. Confirm Tesseract path is correct (auto-detected if installed to default location)
4. Choose Threads and DPI settings
5. Click **▶ START RENAMING**
6. Monitor progress in the live log window

### Settings Guide

| Setting | Recommended | Notes |
|---------|------------|-------|
| Threads | 2 | Safe for 8GB RAM machines |
| DPI | 200 | Best balance of speed vs accuracy |
| Threads | 1 | If PC feels slow during processing |
| DPI | 300 | For low quality or blurry scans |

---

## Portable USB Setup

To run on any PC without installation:

```
YourUSB\
    InvoiceRenamerPro.exe
    tesseract\
        tesseract.exe
        tessdata\
```

1. Copy `C:\Program Files\Tesseract-OCR\` to your USB as a folder named `tesseract\`
2. Build the exe (see below)
3. Plug into any Windows PC and double-click — nothing needs installing

---

## Building the .exe

```
pip install pyinstaller
pyinstaller --onefile --noconsole --name "InvoiceRenamerPro" invoice_renamer_gui.py
```

Your standalone `InvoiceRenamerPro.exe` will appear in the `dist\` folder.

---

## How OCR Correction Works

Tesseract commonly misreads invoice numbers on scanned documents. The app automatically corrects:

| Misread | Corrected |
|---------|-----------|
| `INO0689027` | `IN00689027` |
| `1N00689027` | `IN00689027` |
| `lN00689027` | `IN00689027` |
| `BSl0012345` | `BSI0012345` |
| `B5I0012345` | `BSI0012345` |

It also tries multiple image processing modes (raw, greyscale+contrast, sharpened) before giving up on a file.

---

## Project Structure

```
invoice-renamer-pro/
    invoice_renamer_gui.py   — main app with GUI
    debug_ocr.py             — diagnostic tool for skipped files
    README.md                — this file
```

---

## Roadmap

- [ ] License key system for commercial distribution
- [ ] Windows installer (Inno Setup)
- [ ] Support for additional invoice number formats
- [ ] Batch scheduling (auto-run at set times)
- [ ] Email notification on completion

---

## Author

**Jacqueline Wairimu Ndungu**  
Credit Control & IT Automation  
Nairobi, Kenya

---

## License

Private — All rights reserved.  
This software is not open source. Unauthorised copying or distribution is prohibited.
