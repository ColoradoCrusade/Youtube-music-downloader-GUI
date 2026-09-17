# YouTube Music Playlist Downloader (GUI Edition)

---

## Features

 Graphical User Interface (GUI) with real-time progress logs.
 Square Album Art - Automatically converts YouTube's widescreen 16:9 video thumbnails into clean, centered 1:1 square artwork optimized for  music libraries and mobile apps.
 Metadata & MP3 Conversion: Automatically extracts audio, embeds song titles, artist info, and thumbnail imagery using yt-dlp.
 Smart Skipping Safely skips songs that have already been downloaded to avoid duplicates.
 
---

## Prerequisites

Before running the application, make sure you have the following installed on your system:

1. Python 3.x**
2. FFmpeg (Required by `yt-dlp` to convert audio formats and crop thumbnails).

---

## Installation & Setup

# MacOS Users

1. **Install Homebrew** (if not already installed):
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

2. **Install system dependencies**:
   brew install ffmpeg

3. **Clone the repository**:
   git clone https://github.com/ColoradoCrusade/Youtube-music-downloader-GUI.git
   cd Youtube-music-downloader-GUI

4. **Install Python dependencies**:
   python3 -m pip install --upgrade yt-dlp ytmusicapi

---

# Windows Users

1. **Install Python 3.10+** from python.org (Make sure to check "Add Python to PATH")

2. **Install FFmpeg**:
   * Download from the FFmpeg website or use winget:
     winget install Gyan.FFmpeg
   * Ensure `bin` folder is added to your System PATH. (Verify by running `ffmpeg -version` in PowerShell)

3. **Clone or download the repository**:
   git clone https://github.com/ColoradoCrusade/Youtube-music-downloader-GUI.git
   cd Youtube-music-downloader-GUI

4. **Install Python dependencies**:
   python -m pip install --upgrade yt-dlp ytmusicapi

---

# Linux Users

1. **Install system dependencies via package manager**:

   **Ubuntu/Debian:**
   sudo apt update
   sudo apt install ffmpeg python3-pip -y

   **Fedora/CentOS:**
   sudo dnf install ffmpeg python3-pip -y

2. **Clone the repository**:
   git clone https://github.com/ColoradoCrusade/Youtube-music-downloader-GUI.git
   cd Youtube-music-downloader-GUI

3. **Install Python dependencies** (using a virtual environment to prevent package management errors):
   python3 -m venv venv
   source venv/bin/activate
   pip install --upgrade yt-dlp ytmusicapi

# Arch Linux (Alternative)

1. Install system dependencies via pacman:
sudo pacman -S python python-pip ffmpeg git

2. Clone your repository:
git clone https://github.com/YOUR_USERNAME/Youtube-music-downloader.git

3. Navigate into the project directory:
cd Youtube-music-downloader

4. Install or upgrade the required Python packages:
pip install --upgrade yt-dlp ytmusicapi --user

5. Run the script:
python3 ytmusic_downloader.py

---

## Usage

1. **Navigate to your project directory** (if not already there):
   cd Youtube-music-downloader-GUI

2. **Launch the script**:
   * **MacOS / Linux:**
     python3 ytmusic_downloader.py
   * **Windows:**
     python ytmusic_downloader.py

3. **Using the script**:
   * Paste your YouTube Music Playlist URL into the input field at the top of the window.
   * Click Start Download.
   * Track real-time progress via the embedded log console. 
   * Completed MP3s (featuring cropped 1:1 square album art) will be saved in a folder named `DownloadedMusic/[Playlist Name]/`.
   
---

## Troubleshooting & Notes

* Use Python 3.10+ to avoid deprecation warnings.
* Only **playlist URLs** are supported; profile/channel URLs are not.
* Special characters in video titles are sanitized automatically.
* Already downloaded songs are skipped; deleted songs can be re-downloaded.
* Script shows progress `[current / total]` for downloading, skipped, or missing songs.
* High-resolution album art is embedded automatically.
* Updating yt-dlp can fix unsupported format errors.
* At the end, a summary is displayed with: total songs, downloaded this run, already in folder, skipped (no video found).

---

## License

MIT License © Sumit Kumar

