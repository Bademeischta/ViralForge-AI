# ViralForge AI

**ViralForge AI** ist eine End-to-End-Python-Anwendung, die lange Videoinhalte (z.B. Podcasts, Let's Plays) von YouTube analysiert, die emotionalen Höhepunkte und "viralen" Momente identifiziert und diese vollautomatisch in kurze, aufmerksamkeitsstarke Clips für Plattformen wie TikTok, Shorts und Reels umwandelt.

## Funktionsweise

Das Projekt ist in vier Phasen unterteilt, die nahtlos zusammenarbeiten:

1.  **Phase 1: Das Fundament (`ContentPipeline`)**
    *   Lädt ein beliebiges YouTube-Video mit `yt-dlp` herunter.
    *   Extrahiert die Audiospur mit `ffmpeg`.
    *   Erstellt eine präzise, wortgenaue Transkription mit Zeitstempeln mithilfe von `openai-whisper`.

2.  **Phase 2: Die Analyse (`SignalRecognizer`)**
    *   Analysiert das Transkript auf textbasierte Signale wie **Fragen**, emotionale **Schlüsselwörter** und **Ausrufe**.
    *   Analysiert die Audiospur mit `librosa` auf auditive Signale wie **Lautstärkespitzen** (Lachen, Aufregung) und dramatische **Pausen**.

3.  **Phase 3: Der Kurator (`ClipCurator`)**
    *   Implementiert einen "Geschmacks-Algorithmus", der die erkannten Signale bewertet.
    *   Verwendet ein gleitendes Zeitfenster, um die Dichte und Kombination von Signalen zu bewerten und "Momente" mit hohem viralen Potenzial zu finden.
    *   Wählt die besten, nicht überlappenden Clips aus und passt ihre Grenzen an die gesprochenen Sätze an.

4.  **Phase 4: Der Editor (`VideoEditor`)**
    *   Nimmt die kuratierten Zeitstempel und schneidet die finalen Clips aus dem Originalvideo mit `moviepy`.
    *   Formatiert die Clips automatisch in ein vertikales 9:16-Format.
    *   Generiert und überlagert dynamische, Wort-für-Wort animierte Untertitel, bei denen das aktuell gesprochene Wort hervorgehoben wird.

---

## Nutzung

### Lokale Installation

**1. Voraussetzungen:**
*   **Python 3.8+**: Stellen Sie sicher, dass Python installiert ist.
*   **ffmpeg**: Sie müssen `ffmpeg` auf Ihrem System installiert haben.
    *   **Auf Ubuntu/Debian:** `sudo apt-get update && sudo apt-get install ffmpeg`
    *   **Auf macOS (mit Homebrew):** `brew install ffmpeg`
    *   **Auf Windows:** Laden Sie es von der [offiziellen Website](https://ffmpeg.org/download.html) herunter und fügen Sie es zu Ihrem System-PATH hinzu.

**2. Projekt klonen:**
```bash
git clone <repository-url>
cd <repository-directory>
```

**3. Abhängigkeiten installieren:**
Alle erforderlichen Python-Pakete sind in der `requirements.txt`-Datei aufgeführt.
```bash
pip install -r requirements.txt
```

**4. Ausführung:**
Verwenden Sie das `main.py`-Skript, um die Pipeline zu starten. Übergeben Sie die YouTube-URL als Argument.

```bash
python main.py "https://www.youtube.com/watch?v=your_video_id"
```

Die fertigen Clips werden standardmäßig im Ordner `output_clips/` gespeichert. Sie können mit dem `--output_dir`-Flag ein anderes Verzeichnis angeben:
```bash
python main.py "URL" --output_dir "meine_neuen_clips"
```

---

### Nutzung in Google Colab

Sie können ViralForge AI auch ohne lokale Installation direkt in einem Google Colab Notebook ausführen. Dies ist ideal zum Testen oder wenn Sie keinen lokalen Zugriff auf eine leistungsstarke Maschine haben.

**Anleitung:**
1.  Öffnen Sie ein neues Notebook in [Google Colab](https://colab.research.google.com/).
2.  Fügen Sie den folgenden Code in eine Zelle ein und führen Sie sie aus. Dieser Block kümmert sich um die Installation aller notwendigen Abhängigkeiten und das Klonen des Projekts.

```python
# @title ViralForge AI Setup in Google Colab
# 1. Install System Dependencies (ffmpeg)
!sudo apt-get update
!sudo apt-get install -y ffmpeg

# 2. Clone the ViralForge AI repository
!git clone https://github.com/bademeischta/viralforge-ai.git
%cd /content/viralforge-ai/viralforge

# 3. Install Python Dependencies
!pip install -r requirements.txt

print("\n\n✅ Setup complete! ViralForge AI is ready to use.")
```
*Hinweis: Ersetzen Sie `https://github.com/your-username/viralforge-ai.git` durch die tatsächliche URL des Projekt-Repositorys.*

3.  Nachdem der Setup-Block abgeschlossen ist, können Sie die Pipeline in einer neuen Zelle mit der gewünschten YouTube-URL ausführen.

```python
# @title Run the ViralForge AI Pipeline
# @markdown Geben Sie die YouTube-URL des Videos ein, das Sie verarbeiten möchten.
%cd /content/viralforge-ai
YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ" # Beispiel-URL

# Führen Sie das Hauptskript aus
!python main.py "{YOUTUBE_URL}"

# Die Clips werden im Ordner /content/viralforge-ai/output_clips/ gespeichert.
# Sie können sie im Dateibrowser auf der linken Seite finden und herunterladen.
print("\n\n🚀 Pipeline finished! Check the 'output_clips' folder in the file browser.")
```
