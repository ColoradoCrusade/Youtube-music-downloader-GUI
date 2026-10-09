import os
import re
import sys
import threading
import subprocess
import platform
import tkinter as tk
from tkinter import messagebox, scrolledtext
import urllib.request
import urllib.parse
import json
from ytmusicapi import YTMusic

# 🔹 Clean up names for safe folder/file creation
def sanitize_name(name: str) -> str:
    """Make safe folder/filename by replacing illegal characters with underscores."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

# 🔹 PRIMARY: Fetch genre from iTunes API
def fetch_genre_itunes(album_name: str, artist_name: str) -> str:
    """Fetch the primary genre for an album using the free iTunes Search API."""
    if not album_name or not artist_name:
        return None
    
    query = f"{album_name} {artist_name}"
    url = f"https://itunes.apple.com/search?term={urllib.parse.quote(query)}&entity=album&limit=1"
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'YTMusicDownloader/1.3'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            if data.get('resultCount', 0) > 0:
                genre = data['results'][0].get('primaryGenreName')
                return genre if genre else None
    except Exception:
        return None
    return None

# 🔹 SECONDARY: Fetch genre from Deezer API
def fetch_genre_deezer(album_name: str, artist_name: str) -> str:
    """Fetch the primary genre using Deezer's free public API as a fallback."""
    if not album_name or not artist_name:
        return None
    
    # Step 1: Search for the album to get its Deezer ID
    search_query = f'album:"{album_name}" artist:"{artist_name}"'
    search_url = f"https://api.deezer.com/search/album?q={urllib.parse.quote(search_query)}"
    
    try:
        req = urllib.request.Request(search_url, headers={'User-Agent': 'YTMusicDownloader/1.3'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            if not data.get('data'):
                return None
            
            album_id = data['data'][0].get('id')
            if not album_id:
                return None
            
        # Step 2: Fetch the specific album details to extract the genre
        album_url = f"https://api.deezer.com/album/{album_id}"
        album_req = urllib.request.Request(album_url, headers={'User-Agent': 'YTMusicDownloader/1.3'})
        with urllib.request.urlopen(album_req, timeout=3) as album_response:
            album_data = json.loads(album_response.read().decode('utf-8'))
            genres = album_data.get('genres', {}).get('data', [])
            if genres:
                # Return the first (primary) genre found
                return genres[0].get('name')
                
    except Exception:
        return None
        
    return None

# 🔹 WRAPPER: Try iTunes, then fallback to Deezer
def fetch_best_genre(album_name: str, artist_name: str) -> tuple:
    """Returns a tuple of (genre_name, source_name) or (None, None)."""
    genre = fetch_genre_itunes(album_name, artist_name)
    if genre:
        return genre, "iTunes"
        
    genre = fetch_genre_deezer(album_name, artist_name)
    if genre:
        return genre, "Deezer"
        
    return None, None


class YTMusicDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YT Music Downloader")
        self.root.geometry("680x480")
        self.root.minsize(500, 400)

        # --- Top Frame: Input & Buttons ---
        input_frame = tk.Frame(root, padx=10, pady=10)
        input_frame.pack(fill=tk.X)

        tk.Label(input_frame, text="YouTube Music Playlist URL:", font=("Arial", 12)).pack(anchor="w", pady=(0, 5))
        
        self.url_entry = tk.Entry(input_frame, font=("Arial", 12))
        self.url_entry.pack(fill=tk.X, side=tk.LEFT, expand=True, padx=(0, 10))

        # Open Folder Button
        self.folder_btn = tk.Button(
            input_frame, 
            text="Open Folder", 
            bg="#4CAF50", 
            fg="black", 
            font=("Arial", 11, "bold"), 
            command=self.open_download_folder
        )
        self.folder_btn.pack(side=tk.RIGHT, padx=(0, 5))

        # Start button
        self.start_btn = tk.Button(
            input_frame, 
            text="Start Download", 
            bg="#4CAF50", 
            fg="black", 
            font=("Arial", 11, "bold"), 
            command=self.start_download_thread
        )
        self.start_btn.pack(side=tk.RIGHT)

        # --- Bottom Frame: Console / Progress Log ---
        log_frame = tk.Frame(root, padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(log_frame, text="Download Progress:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.log_area = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, bg="#1e1e1e", fg="#00ff00", font=("Menlo", 11))
        self.log_area.pack(fill=tk.BOTH, expand=True)
        self.log_area.insert(tk.END, "Ready. Paste a YouTube Music playlist URL above and click Start.\n")

    def log(self, message):
        """Helper to safely write text to the GUI log window."""
        self.log_area.insert(tk.END, message + "\n")
        self.log_area.see(tk.END)

    def open_download_folder(self):
        """Opens the DownloadedMusic folder using the OS's native file explorer with an inversion click effect."""
        self.folder_btn.config(bg="black", fg="#4CAF50")
        self.root.after(150, lambda: self.folder_btn.config(bg="#4CAF50", fg="black"))

        base_dir = os.path.abspath("DownloadedMusic")
        os.makedirs(base_dir, exist_ok=True)

        system = platform.system()
        try:
            if system == "Darwin":       # macOS
                subprocess.run(["open", base_dir])
            elif system == "Windows":    # Windows
                os.startfile(base_dir)
            elif system == "Linux":      # Linux
                subprocess.run(["xdg-open", base_dir])
            else:
                self.log(f"❌ Unsupported operating system: {system}")
        except Exception as e:
            self.log(f"❌ Could not open folder: {str(e)}")

    def start_download_thread(self):
        playlist_url = self.url_entry.get().strip()
        if not playlist_url or "playlist?list=" not in playlist_url:
            messagebox.showerror("Error", "Please enter a valid YouTube Music playlist URL.")
            return

        # Disable button during download and invert colors
        self.start_btn.config(state=tk.DISABLED, bg="black", fg="#4CAF50")
        
        # Run download in a background thread
        threading.Thread(target=self.download_playlist, args=(playlist_url,), daemon=True).start()

    def download_playlist(self, playlist_url: str, base_dir="DownloadedMusic"):
        """Download all songs from a YouTube Music playlist with proper titles, metadata, and high-res album art."""
        try:
            self.log(f"\n=== Downloading playlist: {playlist_url} ===")

            # Initialize YTMusic API
            ytmusic = YTMusic()

            # Extract playlist ID from the URL (everything after "list=")
            playlist_id = playlist_url.split("list=")[-1].split("&")[0]

            # Fetch full playlist metadata (no song limit)
            playlist = ytmusic.get_playlist(playlist_id, limit=None)

            # Create folder for the playlist
            playlist_name = sanitize_name(playlist['title'])
            playlist_folder = os.path.join(base_dir, playlist_name)
            os.makedirs(playlist_folder, exist_ok=True)

            # Extract all track info
            tracks = playlist['tracks']
            total_songs = len(tracks)

            downloaded_count = 0
            already_present_count = 0
            no_video_count = 0
            
            # Cache genres so we only lookup once per album
            album_genres = {}

            # Loop through every song in the playlist
            for idx, track in enumerate(tracks, start=1):
                song_title = sanitize_name(track['title'])
                file_path = os.path.join(playlist_folder, f"{song_title}.mp3")

                # ✅ Skip if file already exists
                if os.path.exists(file_path):
                    self.log(f"[{idx:3d} / {total_songs}] Already exists, skipping: {song_title}")
                    already_present_count += 1
                    continue

                # ❌ Skip if no videoId available
                video_id = track.get('videoId')
                if not video_id:
                    self.log(f"[{idx:3d} / {total_songs}] ⚠️ No video found, skipping: {song_title}")
                    no_video_count += 1
                    continue

                # --- Automatic Genre Lookup ---
                album_dict = track.get('album')
                artists_list = track.get('artists')
                
                album_name = album_dict.get('name') if isinstance(album_dict, dict) else None
                artist_name = artists_list[0].get('name') if isinstance(artists_list, list) and len(artists_list) > 0 else None
                
                genre = None
                if album_name and artist_name:
                    cache_key = f"{album_name}-{artist_name}"
                    
                    # Check if we already looked up this exact album in this run
                    if cache_key in album_genres:
                        genre = album_genres[cache_key]
                    else:
                        genre, source = fetch_best_genre(album_name, artist_name)
                        album_genres[cache_key] = genre
                        
                        if genre:
                            self.log(f"[{idx:3d} / {total_songs}] 🏷️  Identified Genre: {genre} (via {source})")
                        else:
                            self.log(f"[{idx:3d} / {total_songs}] 🏷️  No Genre Found. Leaving blank.")

                # Build full YouTube URL for the track
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                self.log(f"[{idx:3d} / {total_songs}] Downloading: {song_title}")

                # yt-dlp command
                command_download = [
                    "yt-dlp",
                    "-f", "bestaudio",
                    "--extract-audio",
                    "--audio-format", "mp3",
                    "--add-metadata",
                    "--embed-metadata",
                    "--embed-thumbnail",
                    "--convert-thumbnail", "jpg",
                    "--ppa", "ThumbnailsConvertor+FFmpeg_o:-c:v mjpeg -qmin 1 -qscale:v 1 -vf crop=\"'if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'\""
                ]

                # 1. Force inject our genre into yt-dlp's dict (if we have one)
                # 2. Obliterate ANY existing genre or category tag ("Music", "NA", etc.) using regex (?s)^.*$
                if genre:
                    command_download.extend([
                        "--parse-metadata", f"{genre}:%(genre)s",
                        "--replace-in-metadata", "genre", "(?s)^.*$", genre,
                        "--replace-in-metadata", "category", "(?s)^.*$", genre
                    ])
                else:
                    command_download.extend([
                        "--replace-in-metadata", "genre", "(?s)^.*$", "",
                        "--replace-in-metadata", "category", "(?s)^.*$", ""
                    ])

                # Output path and video URL
                command_download.extend([
                    "-o", os.path.join(playlist_folder, "%(title)s.%(ext)s"),
                    video_url
                ])

                # Run download process
                subprocess.run(command_download)
                downloaded_count += 1

            # Summary after playlist download
            skipped_total = already_present_count + no_video_count

            self.log("\n✅ Playlist download completed!")
            self.log(f"Playlist: {playlist_name}")
            self.log(f"Total songs in playlist: {total_songs}")
            self.log(f"Downloaded this run: {downloaded_count}")
            self.log(f"Already in folder: {already_present_count}")
            self.log(f"Skipped (no video found): {no_video_count}")
            self.log(f"Total skipped: {skipped_total}")

        except Exception as e:
            self.log(f"\n❌ An error occurred: {str(e)}")
        
        finally:
            # Re-enable button when finished and revert colors back to normal
            self.start_btn.config(state=tk.NORMAL, bg="#4CAF50", fg="black")


def main():
    root = tk.Tk()
    app = YTMusicDownloaderApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
