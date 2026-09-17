import os
import re
import sys
import threading
import subprocess
import platform
import tkinter as tk
from tkinter import messagebox, scrolledtext
from ytmusicapi import YTMusic

# 🔹 Clean up names for safe folder/file creation
def sanitize_name(name: str) -> str:
    """Make safe folder/filename by replacing illegal characters with underscores."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)


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

        # Open Folder Button (Matches Start button style: Green bg, Black text)
        self.folder_btn = tk.Button(
            input_frame, 
            text="Open Folder", 
            bg="#4CAF50", 
            fg="black", 
            font=("Arial", 11, "bold"), 
            command=self.open_download_folder
        )
        self.folder_btn.pack(side=tk.RIGHT, padx=(0, 5))

        # Start button with black text on green background
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

        # Disable button during download and invert colors (Black background, Green text)
        self.start_btn.config(state=tk.DISABLED, bg="black", fg="#4CAF50")
        
        # Run download in a background thread so the GUI window doesn't freeze/lock up
        threading.Thread(target=self.download_playlist, args=(playlist_url,), daemon=True).start()

    # 🔹 Main function to download songs from a YouTube Music playlist
    def download_playlist(self, playlist_url: str, base_dir="DownloadedMusic"):
        """Download all songs from a YouTube Music playlist with proper titles, metadata, and high-res album art."""
        try:
            self.log(f"\n=== Downloading playlist: {playlist_url} ===")

            # Initialize YTMusic API (works without authentication for public playlists)
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

            # Counters for summary
            downloaded_count = 0
            already_present_count = 0
            no_video_count = 0

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

                # Build full YouTube URL for the track
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                self.log(f"[{idx:3d} / {total_songs}] Downloading: {song_title}")

                # yt-dlp command → best audio, convert to MP3, embed metadata + cropped square thumbnail
                command_download = [
                    "yt-dlp",
                    "-f", "bestaudio",
                    "--extract-audio",
                    "--audio-format", "mp3",
                    "--add-metadata",
                    "--embed-metadata",
                    "--embed-thumbnail",
                    "--convert-thumbnail", "jpg",
                    "--ppa", "ThumbnailsConvertor+FFmpeg_o:-c:v mjpeg -qmin 1 -qscale:v 1 -vf crop=\"'if(gt(ih,iw),iw,ih)':'if(gt(iw,ih),ih,iw)'\"",
                    "-o", os.path.join(playlist_folder, "%(title)s.%(ext)s"),  # Save as song title
                    video_url
                ]

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


# 🔹 Script entry point
def main():
    root = tk.Tk()
    app = YTMusicDownloaderApp(root)
    root.mainloop()


# 🔹 Run script
if __name__ == "__main__":
    main()
