# ViralForge AI V2.0

**ViralForge AI** ist eine End-to-End-Python-Anwendung, die lange Videoinhalte von YouTube analysiert und vollautomatisch in kurze, aufmerksamkeitsstarke Clips umwandelt. Das Projekt verfügt über zwei Analyse-Modi: einen allgemeinen Modus (V1) und einen hochspezialisierten Modus für Valorant-Gameplay (V2).

## Funktionsweise & Modi

### V1: Standard-Analyse (Audio & Text)
Dieser Modus eignet sich für allgemeine Videoinhalte wie Podcasts oder Interviews. Er analysiert Transkript- und Audiodaten, um interessante Momente zu finden.

### V2: Valorant-Analyse (Computer Vision & Narrative)
Dieser Modus ist speziell für Valorant-Gameplay konzipiert. Er kombiniert Computer Vision mit Audio-/Text-Analyse, um "narrative Ereignisketten" zu finden und visuell zu inszenieren. Die V2-Analyse erfordert eine robustere, kontextsensitive Erkennung.

---

## Lokale Installation

**1. System-Abhängigkeiten installieren (Kritisch!)**

ViralForge AI benötigt externe Programme, die vor der Ausführung installiert und im System-PATH verfügbar sein müssen.

*   **ffmpeg**: Erforderlich für die Audio- und Videoverarbeitung.
    *   **Auf Ubuntu/Debian:** `sudo apt-get update && sudo apt-get install -y ffmpeg`
    *   **Auf macOS (mit Homebrew):** `brew install ffmpeg`

*   **ImageMagick**: Erforderlich für die Erstellung von Text-Untertiteln mit `moviepy`.
    *   **Auf Ubuntu/Debian:** `sudo apt-get install -y imagemagick`
    *   **Auf macOS (mit Homebrew):** `brew install imagemagick`
    *   **Auf Windows:** Laden Sie den Installer von [imagemagick.org](https://imagemagick.org/script/download.php). **Wichtig:** Wählen Sie bei der Installation die Optionen "Install legacy utilities (e.g., convert)" und "Add application directory to your system path".

*   **Tesseract OCR**: Erforderlich für die V2-Valorant-Analyse (Texterkennung im Spiel).
    *   **Auf Ubuntu/Debian:** `sudo apt-get install -y tesseract-ocr`
    *   **Auf macOS (mit Homebrew):** `brew install tesseract`
    *   **Auf Windows:** Laden Sie den Installer von [Tesseracts GitHub-Seite](https://github.com/UB-Mannheim/tesseract/wiki). Fügen Sie das Installationsverzeichnis zu Ihrem System-PATH hinzu.

**2. Projekt klonen & Python-Abhängigkeiten installieren**

```bash
# Ersetzen Sie die URL durch die tatsächliche Repository-URL
git clone https://github.com/your-username/viralforge-ai.git
cd viralforge-ai

# Python-Pakete installieren
pip install -r requirements.txt
```

**3. Ausführung**

Das Skript überprüft beim Start, ob die System-Abhängigkeiten gefunden werden.

*   **Für allgemeine Videos (V1-Modus):**
    ```bash
    python main.py "https://www.youtube.com/watch?v=your_video_id" --mode v1
    ```

*   **Für Valorant-Gameplay (V2-Modus):**
    ```bash
    python main.py "https://www.youtube.com/watch?v=valorant_gameplay_id" --mode valorant
    ```

---
## Fehlerbehebung

*   **`ERROR: [youtube] ... Sign in to confirm...`**: YouTube blockiert den Download. Versuchen Sie ein anderes Video oder verwenden Sie die Cookie-Methode, die in der [yt-dlp-Dokumentation](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp) beschrieben ist.
*   **`TesseractNotFoundError` oder `ImageMagick` Fehler**: Eine der System-Abhängigkeiten ist nicht korrekt installiert oder nicht im PATH des Systems verfügbar. Überprüfen Sie die Installationsschritte oben.
