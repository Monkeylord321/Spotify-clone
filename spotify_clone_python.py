import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import json
import random
from pathlib import Path
from pytubefix import YouTube, Search
import pygame
from mutagen.mp3 import MP3


class SpotifyStyleApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Streaming")
        self.root.geometry("1200x700")
        self.root.configure(bg="#000000")
        
        pygame.mixer.init()
        
        self.music_dir = Path.home() / "MusicStreamingApp"
        self.music_dir.mkdir(exist_ok=True)
        self.library_file = self.music_dir / "library.json"
        
        self.current_track = None
        self.current_track_index = -1
        self.is_playing = False
        self.is_paused = False
        self.current_file = None
        self.duration = 0
        self.is_seeking = False
        self.search_mode = "library"
        self.search_results = []
        self.library = self.load_library()
        self.shuffle_mode = False
        self.current_playlist = []
        self.last_seek_pos = 0
        
        self.setup_styles()
        self.setup_ui()
        self.update_progress()
        self.show_all_library_songs()

    def load_library(self):
        if self.library_file.exists():
            with open(self.library_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def save_library(self):
        with open(self.library_file, 'w', encoding='utf-8') as f:
            json.dump(self.library, f, indent=2, ensure_ascii=False)

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        style.configure("Spotify.Horizontal.TScale",
                       background="#000000",
                       troughcolor="#404040",
                       borderwidth=0,
                       lightcolor="#1DB954",
                       darkcolor="#1DB954")

    def setup_ui(self):
        main_container = tk.Frame(self.root, bg="#000000")
        main_container.pack(fill="both", expand=True)
        
        self.setup_sidebar(main_container)
        self.setup_main_content(main_container)
        self.setup_player_bar()

    def setup_sidebar(self, parent):
        sidebar = tk.Frame(parent, bg="#000000", width=250)
        sidebar.pack(side="left", fill="y", padx=(0, 1))
        sidebar.pack_propagate(False)
        
        logo_frame = tk.Frame(sidebar, bg="#000000")
        logo_frame.pack(pady=30, padx=20, anchor="w")
        
        logo = tk.Label(logo_frame, text="♫", font=("Arial", 32, "bold"), 
                       bg="#000000", fg="#1DB954")
        logo.pack(side="left")
        
        logo_text = tk.Label(logo_frame, text="Music", font=("Arial", 20, "bold"),
                            bg="#000000", fg="#FFFFFF")
        logo_text.pack(side="left", padx=(10, 0))
        
        nav_items = [
            ("🏠  Home", lambda: self.switch_view("library")),
            ("🔍  Search", lambda: self.switch_view("search")),
        ]
        
        for text, command in nav_items:
            btn = tk.Button(sidebar, text=text, font=("Arial", 13, "bold"),
                          bg="#000000", fg="#B3B3B3", bd=0, 
                          activebackground="#1DB954", activeforeground="#FFFFFF",
                          cursor="hand2", anchor="w", padx=20, pady=12,
                          command=command)
            btn.pack(fill="x", padx=10, pady=2)
            btn.bind("<Enter>", lambda e, b=btn: b.config(fg="#FFFFFF"))
            btn.bind("<Leave>", lambda e, b=btn: b.config(fg="#B3B3B3"))
        
        tk.Frame(sidebar, bg="#282828", height=1).pack(fill="x", padx=20, pady=20)
        
        library_label = tk.Label(sidebar, text="Your Library", 
                                font=("Arial", 11, "bold"),
                                bg="#000000", fg="#B3B3B3")
        library_label.pack(anchor="w", padx=20, pady=(0, 10))
        
        self.library_count = tk.Label(sidebar, 
                                     text=f"{len(self.library)} songs",
                                     font=("Arial", 12),
                                     bg="#000000", fg="#B3B3B3")
        self.library_count.pack(anchor="w", padx=20)

    def setup_main_content(self, parent):
        main_area = tk.Frame(parent, bg="#121212")
        main_area.pack(side="left", fill="both", expand=True)
        
        top_bar = tk.Frame(main_area, bg="#121212", height=80)
        top_bar.pack(fill="x", padx=30, pady=(20, 0))
        top_bar.pack_propagate(False)
        
        search_container = tk.Frame(top_bar, bg="#242424", height=45)
        search_container.pack(fill="x")
        search_container.pack_propagate(False)
        
        search_icon = tk.Label(search_container, text="🔍", font=("Arial", 14),
                              bg="#242424", fg="#B3B3B3")
        search_icon.pack(side="left", padx=(15, 10))
        
        self.search_entry = tk.Entry(search_container, font=("Arial", 13),
                                     bg="#242424", fg="#FFFFFF", bd=0,
                                     insertbackground="#FFFFFF")
        self.search_entry.pack(side="left", fill="both", expand=True, pady=10)
        self.search_entry.bind("<Return>", lambda e: self.handle_search())
        self.search_entry.insert(0, "What do you want to listen to?")
        self.search_entry.bind("<FocusIn>", self.on_entry_focus_in)
        self.search_entry.bind("<FocusOut>", self.on_entry_focus_out)
        self.search_entry.config(fg="#6A6A6A")
        
        self.mode_indicator = tk.Frame(search_container, bg="#1DB954", width=4)
        
        btn_frame = tk.Frame(search_container, bg="#242424")
        btn_frame.pack(side="right", padx=10)
        
        self.search_btn = tk.Button(btn_frame, text="Search Online",
                                    font=("Arial", 10, "bold"),
                                    bg="#1DB954", fg="#000000", bd=0,
                                    padx=20, pady=8, cursor="hand2",
                                    command=lambda: self.search_mode_set("search"))
        self.search_btn.pack(side="left", padx=5)
        
        content_frame = tk.Frame(main_area, bg="#121212")
        content_frame.pack(fill="both", expand=True, padx=30, pady=20)
        
        header_frame = tk.Frame(content_frame, bg="#121212")
        header_frame.pack(fill="x", pady=(0, 15))
        
        self.content_title = tk.Label(header_frame, text="Your Library",
                                      font=("Arial", 24, "bold"),
                                      bg="#121212", fg="#FFFFFF")
        self.content_title.pack(side="left")
        
        self.delete_btn = tk.Button(header_frame, text="🗑 Delete",
                                    font=("Arial", 10, "bold"),
                                    bg="#B33A3A", fg="#FFFFFF", bd=0,
                                    padx=15, pady=6, cursor="hand2",
                                    command=self.delete_selected)
        self.delete_btn.pack(side="right")
        
        list_container = tk.Frame(content_frame, bg="#121212")
        list_container.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(list_container, bg="#121212", 
                               troughcolor="#121212", width=12)
        scrollbar.pack(side="right", fill="y")
        
        self.results_listbox = tk.Listbox(list_container, font=("Arial", 12),
                                         bg="#121212", fg="#FFFFFF",
                                         selectbackground="#282828",
                                         selectforeground="#1DB954",
                                         yscrollcommand=scrollbar.set,
                                         bd=0, highlightthickness=0,
                                         activestyle="none")
        self.results_listbox.pack(side="left", fill="both", expand=True)
        self.results_listbox.bind("<Double-Button-1>", lambda e: self.handle_selection())
        self.results_listbox.bind("<Delete>", lambda e: self.delete_selected())
        self.results_listbox.bind("<space>", lambda e: self.toggle_play_pause())
        
        scrollbar.config(command=self.results_listbox.yview)

    def setup_player_bar(self):
        player = tk.Frame(self.root, bg="#181818", height=90)
        player.pack(side="bottom", fill="x")
        player.pack_propagate(False)
        
        left_section = tk.Frame(player, bg="#181818")
        left_section.pack(side="left", fill="y", padx=20)
        
        self.now_playing = tk.Label(left_section, text="No track playing",
                                   font=("Arial", 13, "bold"),
                                   bg="#181818", fg="#FFFFFF")
        self.now_playing.pack(anchor="w", pady=(15, 0))
        
        self.artist_label = tk.Label(left_section, text="",
                                     font=("Arial", 11),
                                     bg="#181818", fg="#B3B3B3")
        self.artist_label.pack(anchor="w")
        
        center_section = tk.Frame(player, bg="#181818")
        center_section.pack(expand=True, fill="both")
        
        controls = tk.Frame(center_section, bg="#181818")
        controls.pack(pady=(8, 0))
        
        self.shuffle_btn = tk.Button(controls, text="🔀", font=("Arial", 16),
                                     bg="#181818", fg="#B3B3B3", bd=0,
                                     cursor="hand2", command=self.toggle_shuffle,
                                     activebackground="#181818")
        self.shuffle_btn.pack(side="left", padx=8)
        
        prev_btn = tk.Button(controls, text="⏮", font=("Arial", 20),
                           bg="#181818", fg="#FFFFFF", bd=0,
                           cursor="hand2", command=self.play_previous,
                           activebackground="#181818")
        prev_btn.pack(side="left", padx=8)
        
        self.play_pause_btn = tk.Button(controls, text="▶", font=("Arial", 28),
                                       bg="#FFFFFF", fg="#000000", bd=0,
                                       width=2, height=1, cursor="hand2",
                                       command=self.toggle_play_pause,
                                       activebackground="#B3B3B3")
        self.play_pause_btn.pack(side="left", padx=12)
        
        next_btn = tk.Button(controls, text="⏭", font=("Arial", 20),
                           bg="#181818", fg="#FFFFFF", bd=0,
                           cursor="hand2", command=self.play_next,
                           activebackground="#181818")
        next_btn.pack(side="left", padx=8)
        
        progress_container = tk.Frame(center_section, bg="#181818")
        progress_container.pack(fill="x", padx=80, pady=(0, 15))
        
        self.time_label = tk.Label(progress_container, text="0:00",
                                  font=("Arial", 9), bg="#181818", fg="#B3B3B3")
        self.time_label.pack(side="left", padx=(0, 10))
        
        self.progress_bar = ttk.Scale(progress_container, from_=0, to=100,
                                     orient="horizontal", 
                                     style="Spotify.Horizontal.TScale",
                                     command=self.on_progress_change)
        self.progress_bar.pack(side="left", fill="x", expand=True)
        self.progress_bar.bind("<ButtonPress-1>", 
                              lambda e: setattr(self, 'is_seeking', True))
        self.progress_bar.bind("<ButtonRelease-1>", self.on_seek)
        
        self.duration_label = tk.Label(progress_container, text="0:00",
                                      font=("Arial", 9), bg="#181818", fg="#B3B3B3")
        self.duration_label.pack(side="left", padx=(10, 0))

    def on_entry_focus_in(self, event):
        if self.search_entry.get() == "What do you want to listen to?":
            self.search_entry.delete(0, tk.END)
            self.search_entry.config(fg="#FFFFFF")

    def on_entry_focus_out(self, event):
        if not self.search_entry.get():
            self.search_entry.insert(0, "What do you want to listen to?")
            self.search_entry.config(fg="#6A6A6A")

    def switch_view(self, view):
        if view == "library":
            self.search_mode = "library"
            self.content_title.config(text="Your Library")
            self.show_all_library_songs()
            self.search_entry.delete(0, tk.END)
            self.search_entry.insert(0, "What do you want to listen to?")
            self.search_entry.config(fg="#6A6A6A")
        elif view == "search":
            self.search_mode = "search"
            self.content_title.config(text="Search")
            self.results_listbox.delete(0, tk.END)
            self.search_entry.focus()

    def search_mode_set(self, mode):
        self.search_mode = mode
        if mode == "search":
            self.search_btn.config(bg="#1DB954")
        self.handle_search()

    def handle_search(self):
        query = self.search_entry.get().strip()
        if query == "What do you want to listen to?" or not query:
            return
            
        if self.search_mode == "search":
            self.search_online(query)
        else:
            self.search_library(query)

    def search_online(self, query):
        self.results_listbox.delete(0, tk.END)
        self.content_title.config(text=f"Searching for '{query}'...")
        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()

    def _search_thread(self, query):
        try:
            s = Search(query + " official audio")
            results = s.results[:15]
            self.search_results = results
            self.root.after(0, self._update_results, results, query)
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Search failed: {str(e)}"))

    def _update_results(self, results, query):
        self.results_listbox.delete(0, tk.END)
        for video in results:
            self.results_listbox.insert(tk.END, f"♫  {video.title}")
        self.content_title.config(text=f"Results for '{query}'")

    def search_library(self, query):
        self.results_listbox.delete(0, tk.END)
        query_lower = query.lower()
        matches = [title for title in self.library.keys() if query_lower in title.lower()]
        
        for title in matches:
            self.results_listbox.insert(tk.END, f"♫  {title}")
        
        self.current_playlist = matches
        self.content_title.config(text=f"Found {len(matches)} songs")

    def show_all_library_songs(self):
        self.results_listbox.delete(0, tk.END)
        all_songs = list(self.library.keys())
        
        for title in all_songs:
            self.results_listbox.insert(tk.END, f"♫  {title}")
        
        self.current_playlist = all_songs
        self.library_count.config(text=f"{len(all_songs)} songs")

    def handle_selection(self):
        if self.search_mode == "search":
            self.download_selected()
        else:
            self.play_from_library()

    def download_selected(self):
        selection = self.results_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        video = self.search_results[index]
        self.content_title.config(text="Downloading...")
        threading.Thread(target=self._download_thread, args=(video,), daemon=True).start()

    def _download_thread(self, video):
        try:
            yt = YouTube(video.watch_url)
            audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc().first()
            
            if not audio_stream:
                audio_stream = yt.streams.filter(only_audio=True).first()
            
            if not audio_stream:
                self.root.after(0, lambda: messagebox.showerror("Error", "No audio available"))
                return
            
            safe_title = "".join(c for c in video.title if c.isalnum() or c in (' ', '-', '_')).strip()
            temp_filename = f"{safe_title}_temp"
            final_filename = f"{safe_title}.mp3"
            final_filepath = self.music_dir / final_filename
            
            downloaded_file = audio_stream.download(output_path=str(self.music_dir), filename=temp_filename)
            
            try:
                from pydub import AudioSegment
                audio = AudioSegment.from_file(downloaded_file)
                audio.export(str(final_filepath), format="mp3", bitrate="192k")
                os.remove(downloaded_file)
            except ImportError:
                if os.path.exists(downloaded_file):
                    os.rename(downloaded_file, str(final_filepath))
            
            self.library[video.title] = {
                "filename": final_filename,
                "path": str(final_filepath),
                "duration": yt.length
            }
            self.save_library()
            
            self.root.after(0, lambda: self.content_title.config(text="Download complete!"))
            self.root.after(0, self.show_all_library_songs)
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", f"Download failed: {str(e)}"))

    def play_from_library(self):
        selection = self.results_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        self.current_track_index = index
        title = self.current_playlist[index]
        
        if title not in self.library:
            return
        
        filepath = self.library[title]["path"]
        if os.path.exists(filepath):
            self._play_file(filepath, title)

    def _play_file(self, filepath, title):
        try:
            if self.is_playing:
                pygame.mixer.music.stop()
            
            self.current_file = filepath
            self.current_track = title
            
            try:
                audio = MP3(filepath)
                self.duration = audio.info.length
            except:
                self.duration = self.library.get(title, {}).get("duration", 0)
            
            pygame.mixer.music.load(filepath)
            pygame.mixer.music.play()
            
            self.is_playing = True
            self.is_paused = False
            self.last_seek_pos = 0
            
            self.now_playing.config(text=title)
            self.play_pause_btn.config(text="⏸")
            self.duration_label.config(text=self.format_time(self.duration))
            self.progress_bar.config(to=self.duration if self.duration > 0 else 100)
            
        except Exception as e:
            messagebox.showerror("Error", f"Playback failed: {str(e)}")

    def play_next(self):
        if not self.current_playlist:
            return
        
        if self.shuffle_mode:
            self.play_random_song()
        else:
            next_index = (self.current_track_index + 1) % len(self.current_playlist)
            self.current_track_index = next_index
            title = self.current_playlist[next_index]
            
            if title in self.library:
                filepath = self.library[title]["path"]
                if os.path.exists(filepath):
                    self._play_file(filepath, title)

    def play_previous(self):
        if not self.current_playlist:
            return
        
        if self.shuffle_mode:
            self.play_random_song()
        else:
            prev_index = (self.current_track_index - 1) % len(self.current_playlist)
            self.current_track_index = prev_index
            title = self.current_playlist[prev_index]
            
            if title in self.library:
                filepath = self.library[title]["path"]
                if os.path.exists(filepath):
                    self._play_file(filepath, title)

    def play_random_song(self):
        if not self.library or not self.current_playlist:
            return
        
        random_index = random.randint(0, len(self.current_playlist) - 1)
        self.current_track_index = random_index
        title = self.current_playlist[random_index]
        filepath = self.library[title]["path"]
        
        if os.path.exists(filepath):
            self._play_file(filepath, title)

    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            self.shuffle_btn.config(fg="#1DB954")
        else:
            self.shuffle_btn.config(fg="#B3B3B3")

    def delete_selected(self):
        selection = self.results_listbox.curselection()
        if not selection:
            return
        
        if self.search_mode == "search":
            messagebox.showwarning("Wrong Mode", "Switch to Library view to delete songs.")
            return
        
        index = selection[0]
        if not self.current_playlist or index >= len(self.current_playlist):
            return
        
        title = self.current_playlist[index]
        
        confirm = messagebox.askyesno("Delete Song", 
                                     f"Delete '{title}' from library?")
        if not confirm:
            return
        
        if self.current_track == title and self.is_playing:
            pygame.mixer.music.stop()
            self.is_playing = False
            self.now_playing.config(text="No track playing")
        
        if title in self.library:
            filepath = self.library[title]["path"]
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception as e:
                messagebox.showerror("Error", f"Could not delete: {str(e)}")
                return
            
            del self.library[title]
            self.save_library()
            self.show_all_library_songs()

    def toggle_play_pause(self):
        if not self.is_playing:
            return
            
        if self.is_paused:
            pygame.mixer.music.unpause()
            self.is_paused = False
            self.play_pause_btn.config(text="⏸")
        else:
            pygame.mixer.music.pause()
            self.is_paused = True
            self.play_pause_btn.config(text="▶")

    def update_progress(self):
        if self.is_playing and not self.is_paused and not self.is_seeking:
            if pygame.mixer.music.get_busy():
                pos = pygame.mixer.music.get_pos() / 1000.0 + self.last_seek_pos
                if pos <= self.duration:
                    self.progress_bar.set(pos)
                    self.time_label.config(text=self.format_time(pos))
            else:
                if self.is_playing and not self.is_paused:
                    if self.shuffle_mode:
                        self.play_random_song()
                    else:
                        self.play_next()
        
        self.root.after(100, self.update_progress)

    def on_progress_change(self, value):
        if self.is_seeking:
            self.time_label.config(text=self.format_time(float(value)))

    def on_seek(self, event):
        if self.is_playing and self.duration > 0:
            pos = float(self.progress_bar.get())
            pygame.mixer.music.stop()
            pygame.mixer.music.load(self.current_file)
            pygame.mixer.music.play(start=pos)
            self.last_seek_pos = pos
            
            if self.is_paused:
                pygame.mixer.music.pause()
        
        self.is_seeking = False

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"

    def on_closing(self):
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SpotifyStyleApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()