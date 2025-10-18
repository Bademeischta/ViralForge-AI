# ViralForge AI V2.0

**ViralForge AI** ist eine End-to-End-Python-Anwendung, die lange Videoinhalte von YouTube analysiert und vollautomatisch in kurze, aufmerksamkeitsstarke Clips umwandelt. Das Projekt verfügt über zwei Analyse-Modi: einen allgemeinen Modus (V1) und einen hochspezialisierten Modus für Valorant-Gameplay (V2).

## Funktionsweise & Modi

### V1: Standard-Analyse (Audio & Text)
Dieser Modus eignet sich für allgemeine Videoinhalte wie Podcasts, Interviews oder Let's Plays. Er identifiziert interessante Momente, indem er die Transkript- und Audiodaten analysiert.
*   **`ContentPipeline`**: Lädt Video, extrahiert Audio und erstellt eine wortgenaue Transkription.
*   **`SignalRecognizer`**: Findet emotionale Signale (Fragen, Schlüsselwörter, Lautstärke, Pausen).
*   **`ClipCurator`**: Bewertet die Dichte dieser Signale in Zeitfenstern, um die besten Momente auszuwählen.
*   **`VideoEditor`**: Schneidet die Clips, formatiert sie in 9:16 und fügt animierte Untertitel hinzu.

### V2: Valorant-Analyse (Computer Vision & Narrative)
Dieser Modus ist speziell für Valorant-Gameplay konzipiert. Er kombiniert Computer Vision mit der V1-Analyse, um "narrative Ereignisketten" – kleine Geschichten im Spiel – zu finden und visuell zu inszenieren.
*   **`GameDataPipeline`**: Erzwingt den Download in 1080p/60fps und extrahiert Frames für die Analyse.
*   **`GameObserver`**: Erkennt präzise Spielereignisse (Kills, Headshots) durch Template-Matching im Killfeed der Video-Frames und nutzt eine robuste **Debouncing-Logik**, um einzelne Ereignisse zu identifizieren.
*   **`SignalRecognizer`**: Wird wiederverwendet, um die Reaktionen des Spielers (Schreie, Kommentare) zu erfassen.
*   **`NarrativeCurator`**: Das Herzstück von V2. Findet Muster wie **"Multi-Kills"** oder **"Reaktions-Kills"** (ein Kill gefolgt von einer lauten Audio-Reaktion) und bewertet sie mit einem **multiplikativen Scoring-System**.
*   **`HollywoodEditor`**: Ein erweiterter Editor, der kontextsensitive Effekte anwendet, z.B. **Zeitlupe** für Headshots und **Text-Overlays** ("MULTI-KILL!", "REACTION!").

---

## Nutzung

### Lokale Installation

**1. Voraussetzungen:**
*   **Python 3.8+**: Stellen Sie sicher, dass Python installiert ist.
*   **ffmpeg**: Erforderlich für die Audio- und Videoverarbeitung.
    *   **Auf Ubuntu/Debian:** `sudo apt-get update && sudo apt-get install ffmpeg`
    *   **Auf macOS (mit Homebrew):** `brew install ffmpeg`
    *   **Auf Windows:** Laden Sie es von der [offiziellen Website](https://ffmpeg.org/download.html) herunter und fügen Sie es zu Ihrem System-PATH hinzu.
*   **ImageMagick**: Erforderlich für die Erstellung von Text-Untertiteln.
    *   **Auf Ubuntu/Debian:** `sudo apt-get install imagemagick`
    *   **Auf macOS (mit Homebrew):** `brew install imagemagick`
    *   **Auf Windows:** Laden Sie den Installer von der [offiziellen Website](https://imagemagick.org/script/download.php) herunter. **Wichtig:** Wählen Sie bei der Installation die Optionen "Install legacy utilities (e.g., convert)" und "Add application directory to your system path".

**2. Projekt klonen:**
```bash
git clone https://github.com/bademeischta/viralforge-ai.git
cd viralforge-ai
```
*(Ersetzen Sie die URL durch die tatsächliche Repository-URL)*

**3. Abhängigkeiten installieren:**
```bash
pip install -r requirements.txt
```
Die `assets/`-Verzeichnisstruktur mit den Valorant-Templates (`kill_icon.png`, `headshot_icon.png`) muss vorhanden sein, um den V2-Modus zu nutzen.

**4. Ausführung:**
Verwenden Sie das `main.py`-Skript und wählen Sie den gewünschten Modus mit dem `--mode`-Flag.

*   **Für allgemeine Videos (V1-Modus):**
    ```bash
    python main.py "https://www.youtube.com/watch?v=your_video_id" --mode v1
    ```

*   **Für Valorant-Gameplay (V2-Modus):**
    ```bash
    python main.py "https://www.youtube.com/watch?v=valorant_gameplay_id" --mode valorant
    ```

Die fertigen Clips werden standardmäßig im Ordner `output_clips/` gespeichert.

---

## Fehlerbehebung (Troubleshooting)

**Problem: Der Video-Download schlägt mit einem `Sign in to confirm...` Fehler fehl.**
*   **Ursache:** YouTube blockiert den automatisierten Download. Dies geschieht häufig bei Videos mit Altersbeschränkung.
*   **Lösung:** Versuchen Sie es mit einem anderen YouTube-Video. Fortgeschrittene Benutzer können Cookies aus ihrem Browser exportieren und mit `yt-dlp` verwenden (siehe [yt-dlp-Dokumentation](https://github.com/yt-dlp/yt-dlp/wiki/FAQ#how-do-i-pass-cookies-to-yt-dlp)).

**Problem: Die Erstellung von Clips schlägt mit einem `OSError` oder `ImageMagick is not installed` fehl.**
*   **Ursache:** Die Systemabhängigkeit `ImageMagick`, die für das Rendern von Text-Untertiteln benötigt wird, ist nicht installiert oder nicht im Systempfad verfügbar.
*   **Lösung:** Befolgen Sie die Installationsanweisungen für `ImageMagick` für Ihr Betriebssystem im Abschnitt "Voraussetzungen".

---

### Nutzung in Google Colab

**Anleitung:**
1.  Öffnen Sie ein neues Notebook in [Google Colab](https://colab.research.google.com/).
2.  Fügen Sie den folgenden Code in eine Zelle ein und führen Sie sie aus. Dieser Block installiert alle Abhängigkeiten, klont das Repository und richtet die Asset-Struktur ein.

```python
# @title ViralForge AI V2.0 Setup in Google Colab
# 1. Install System Dependencies (ffmpeg & ImageMagick)
!sudo apt-get update
!sudo apt-get install -y ffmpeg imagemagick

# 2. Clone the ViralForge AI repository
# HINWEIS: Ersetzen Sie die URL durch die tatsächliche URL Ihres Repositorys!
GIT_REPO_URL = "https://github.com/your-username/viralforge-ai.git"
!git clone {GIT_REPO_URL}
%cd viralforge-ai

# 3. Install Python Dependencies
!pip install -r requirements.txt

# 4. Create dummy assets for the V2 pipeline (falls nicht im Repo vorhanden)
!mkdir -p assets/templates/valorant
import numpy as np
import cv2
dummy_template = np.zeros((10, 10), dtype=np.uint8)
cv2.imwrite("assets/templates/valorant/kill_icon.png", dummy_template)
cv2.imwrite("assets/templates/valorant/headshot_icon.png", dummy_template)

print("\n\n✅ Setup complete! ViralForge AI V2.0 is ready to use.")
```

3.  Führen Sie die Analyse in einer neuen Zelle aus. Wählen Sie den Modus (`v1` oder `valorant`).

```python
# @title Run the ViralForge AI Pipeline
# @markdown Geben Sie die YouTube-URL und den Analyse-Modus an.
YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # @param {type:"string"}
ANALYSIS_MODE = "v1" # @param ["v1", "valorant"]

# Führen Sie das Hauptskript aus
!python main.py "{YOUTUBE_URL}" --mode {ANALYSIS_MODE}

print(f"\n\n🚀 Pipeline im {ANALYSIS_MODE}-Modus beendet! Überprüfen Sie den 'output_clips' Ordner im Dateibrowser.")
```
Die erstellten Clips finden Sie im Ordner `/content/viralforge-ai/output_clips/`. Sie können sie von dort herunterladen.
