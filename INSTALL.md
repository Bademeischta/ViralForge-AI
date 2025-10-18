# Installation von System-Abhängigkeiten

ViralForge AI benötigt einige externe Programme, die auf Ihrem System installiert und im System-PATH verfügbar sein müssen, bevor Sie die Anwendung ausführen können.

---

## 1. ffmpeg

**Zweck:** Wird von `moviepy` und `yt-dlp` für alle Aufgaben der Video- und Audioverarbeitung benötigt.

*   **Windows:**
    1.  Laden Sie eine statische Version von der [offiziellen ffmpeg-Website](https://ffmpeg.org/download.html#build-windows).
    2.  Entpacken Sie die heruntergeladene Datei.
    3.  Fügen Sie den `bin`-Ordner aus dem entpackten Verzeichnis (z.B. `C:\ffmpeg\bin`) zu Ihrem System-PATH hinzu.

*   **macOS (mit Homebrew):**
    ```bash
    brew install ffmpeg
    ```

*   **Linux (Ubuntu/Debian):**
    ```bash
    sudo apt-get update && sudo apt-get install -y ffmpeg
    ```

---

## 2. ImageMagick

**Zweck:** Wird von `moviepy` benötigt, um Text-Clips (z.B. für Untertitel und Overlays) zu rendern.

*   **Windows:**
    1.  Laden Sie den Installer von der [offiziellen ImageMagick-Website](https://imagemagick.org/script/download.php).
    2.  **Wichtig:** Wählen Sie während der Installation die Optionen **"Install legacy utilities (e.g., convert)"** und **"Add application directory to your system path"**. Dies stellt sicher, dass der `convert`-Befehl, den `moviepy` benötigt, verfügbar ist.

*   **macOS (mit Homebrew):**
    ```bash
    brew install imagemagick
    ```

*   **Linux (Ubuntu/Debian):**
    ```bash
    sudo apt-get install -y imagemagick
    ```

---

## 3. Tesseract-OCR

**Zweck:** Wird für die V2-Valorant-Analyse benötigt, um Text aus dem Spiel (z.B. Spielernamen im Killfeed) zu erkennen.

*   **Windows:**
    1.  Laden Sie den Installer von der [offiziellen Tesseract GitHub-Seite (gepflegt von UB Mannheim)](https://github.com/UB-Mannheim/tesseract/wiki).
    2.  Fügen Sie das Tesseract-Installationsverzeichnis (z.B. `C:\Program Files\Tesseract-OCR`) zu Ihrem System-PATH hinzu.
    3.  Möglicherweise müssen Sie auch eine Systemumgebungsvariable `TESSDATA_PREFIX` erstellen, die auf das `tessdata`-Verzeichnis in Ihrer Installation verweist.

*   **macOS (mit Homebrew):**
    ```bash
    brew install tesseract
    ```

*   **Linux (Ubuntu/Debian):**
    ```bash
    sudo apt-get install -y tesseract-ocr
    ```

---

Nachdem diese drei Abhängigkeiten installiert sind, können Sie die Python-Pakete mit `pip install -r requirements.txt` installieren und die Anwendung sollte lauffähig sein.