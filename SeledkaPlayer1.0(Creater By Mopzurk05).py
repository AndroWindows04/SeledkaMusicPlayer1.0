import os
import ctypes
import tkinter as tk
from tkinter import filedialog, ttk

class SeledkaPlayer(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("SeledkaPlayer")
        self.geometry("450x290")
        self.resizable(False, False)

        self.current_alias = "seledka_audio"
        self.is_playing = False
        self.is_paused = False
        self.track_length_ms = 0
        self.user_is_dragging = False

        self.configure(bg="#1a242d") 
        style = ttk.Style()
        style.theme_use('default')
        style.configure(".", background="#1a242d", foreground="white")
        style.configure("TButton", background="#c2d1db", foreground="#1a242d", borderwidth=0, font=("Arial", 10, "bold"))
        style.map("TButton", background=[('active', '#a3b8c7')])
        style.configure("Horizontal.TScale", background="#1a242d")

        self.logo_label = tk.Label(self, text="SeledkaPlayer v1.0", font=("Arial", 10, "italic"), bg="#1a242d", fg="#7da0b8")
        self.logo_label.pack(pady=5)

        self.track_label = tk.Label(self, text="Open file", font=("Arial", 13, "bold"), bg="#1a242d", fg="white", wraplength=400)
        self.track_label.pack(pady=10)

        self.time_label = tk.Label(self, text="00:00 / 00:00", font=("Arial", 10), bg="#1a242d", fg="#7da0b8")
        self.time_label.pack()

        self.timeline = ttk.Scale(self, from_=0, to=100, orient="horizontal", command=self.on_timeline_scroll, style="Horizontal.TScale")
        self.timeline.pack(fill="x", padx=30, pady=10)
        
        self.timeline.bind("<ButtonPress-1>", self.on_slider_press)
        self.timeline.bind("<ButtonRelease-1>", self.on_slider_release)

        self.controls_frame = tk.Frame(self, bg="#1a242d")
        self.controls_frame.pack(pady=10)

        ttk.Button(self.controls_frame, text="🎵 Open", command=self.open_file).grid(row=0, column=0, padx=5, ipady=4)
        ttk.Button(self.controls_frame, text="▶ Play", command=self.play_music).grid(row=0, column=1, padx=5, ipady=4)
        ttk.Button(self.controls_frame, text="⏸ Pause", command=self.pause_music).grid(row=0, column=2, padx=5, ipady=4)
        ttk.Button(self.controls_frame, text="⏹ Stop", command=self.stop_music).grid(row=0, column=3, padx=5, ipady=4)

        self.volume_frame = tk.Frame(self, bg="#1a242d")
        self.volume_frame.pack(pady=10)
        
        self.volume_label = tk.Label(self.volume_frame, text="🔊: 70%", bg="#1a242d", fg="white", font=("Arial", 9, "bold"))
        self.volume_label.grid(row=0, column=0, padx=5)
        
        self.volume_slider = ttk.Scale(self.volume_frame, from_=0, to=1000, orient="horizontal", command=self.change_volume, style="Horizontal.TScale")
        self.volume_slider.set(700)
        self.volume_slider.grid(row=0, column=1, padx=5)

        self.update_player_state()
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def send_mci(self, command):
        buffer = ctypes.create_unicode_buffer(64)
        ctypes.windll.winmm.mciSendStringW(command, buffer, 64, 0)
        return buffer.value.strip()

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Audio Files", "*.mp3 *.wav")])
        if file_path:
            self.stop_music()
            native_path = os.path.normpath(file_path)
            self.send_mci(f'open "{native_path}" type mpegvideo alias {self.current_alias}')
            self.send_mci(f"set {self.current_alias} time format milliseconds")
            length_str = self.send_mci(f"status {self.current_alias} length")
            self.track_length_ms = int(length_str) if length_str.isdigit() else 0
            self.timeline.configure(to=self.track_length_ms)
            self.timeline.set(0)
            self.track_label.configure(text=os.path.basename(file_path))
            self.change_volume(self.volume_slider.get())

    def play_music(self):
        if self.is_paused:
            self.send_mci(f"resume {self.current_alias}")
            self.is_paused = False
        else:
            self.send_mci(f"play {self.current_alias}")
        self.is_playing = True

    def pause_music(self):
        if self.is_playing and not self.is_paused:
            self.send_mci(f"pause {self.current_alias}")
            self.is_paused = True

    def stop_music(self):
        self.send_mci(f"stop {self.current_alias}")
        self.send_mci(f"close {self.current_alias}")
        self.is_playing = False
        self.is_paused = False
        self.timeline.set(0)
        self.time_label.configure(text="00:00 / 00:00")

    def change_volume(self, value):
        vol = int(float(value))
        self.send_mci(f"setaudio {self.current_alias} volume to {vol}")
        self.volume_label.configure(text=f"🔊: {int(vol/10)}%")

    def format_time(self, ms):
        seconds = int((ms / 1000) % 60)
        minutes = int((ms / (1000 * 60)) % 60)
        return f"{minutes:02d}:{seconds:02d}"

    def on_slider_press(self, event):
        self.user_is_dragging = True

    def on_slider_release(self, event):
        if self.is_playing or self.is_paused:
            new_position = int(self.timeline.get())
            if self.is_paused:
                self.send_mci(f"seek {self.current_alias} to {new_position}")
            else:
                self.send_mci(f"play {self.current_alias} from {new_position}")
        self.user_is_dragging = False

    def on_timeline_scroll(self, value):
        if self.user_is_dragging:
            current_ms = int(float(value))
            self.time_label.configure(text=f"{self.format_time(current_ms)} / {self.format_time(self.track_length_ms)}")

    def update_player_state(self):
        if self.is_playing and not self.is_paused and not self.user_is_dragging:
            position_str = self.send_mci(f"status {self.current_alias} position")
            if position_str.isdigit():
                current_ms = int(position_str)
                self.timeline.set(current_ms)
                self.time_label.configure(text=f"{self.format_time(current_ms)} / {self.format_time(self.track_length_ms)}")
                if current_ms >= self.track_length_ms - 300:
                    self.stop_music()
        self.after(500, self.update_player_state)

    def on_closing(self):
        self.stop_music()
        self.destroy()

if __name__ == "__main__":
    app = SeledkaPlayer()
    app.mainloop()
