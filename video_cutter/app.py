import os
import threading
import pandas as pd
from moviepy.editor import VideoFileClip
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

# ===== TIME PARSE FUNCTION =====
def time_to_seconds(t):
    parts = list(map(float, str(t).split(":")))
    if len(parts) == 3:
        h, m, s = parts
        return h * 3600 + m * 60 + s
    elif len(parts) == 2:
        m, s = parts
        return m * 60 + s
    else:
        return parts[0]

# ===== MAIN APP =====
class VideoCutterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Video Cutter Tool")
        self.root.geometry("500x300")

        self.video_path = ""
        self.csv_path = ""

        # UI
        tk.Label(root, text="Video Cutter Tool", font=("Arial", 16)).pack(pady=10)

        tk.Button(root, text="Chọn Video", command=self.select_video).pack(pady=5)
        self.video_label = tk.Label(root, text="Chưa chọn video")
        self.video_label.pack()

        tk.Button(root, text="Chọn CSV", command=self.select_csv).pack(pady=5)
        self.csv_label = tk.Label(root, text="Chưa chọn CSV")
        self.csv_label.pack()

        self.progress = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
        self.progress.pack(pady=15)

        self.start_btn = tk.Button(root, text="Bắt đầu cắt", command=self.start_processing)
        self.start_btn.pack(pady=10)

    def select_video(self):
        path = filedialog.askopenfilename(filetypes=[("Video files", "*.mp4 *.mov *.avi")])
        if path:
            self.video_path = path
            self.video_label.config(text=os.path.basename(path))

    def select_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv")])
        if path:
            self.csv_path = path
            self.csv_label.config(text=os.path.basename(path))

    def start_processing(self):
        if not self.video_path or not self.csv_path:
            messagebox.showerror("Lỗi", "Vui lòng chọn đầy đủ file!")
            return

        threading.Thread(target=self.process).start()

    def process(self):
        try:
            output_dir = "clips"
            os.makedirs(output_dir, exist_ok=True)

            df = pd.read_csv(self.csv_path)
            video = VideoFileClip(self.video_path)

            total = len(df)
            self.progress["maximum"] = total

            for i, row in df.iterrows():
                start = time_to_seconds(row["start"])
                end = time_to_seconds(row["end"])

                clip = video.subclip(start, end)
                output_path = os.path.join(output_dir, f"clip_{i+1}.mp4")

                clip.write_videofile(output_path, codec="libx264", audio_codec="aac", verbose=False, logger=None)

                self.progress["value"] = i + 1
                self.root.update_idletasks()

            messagebox.showinfo("Hoàn thành", "Đã cắt xong video!")

        except Exception as e:
            messagebox.showerror("Lỗi", str(e))

# ===== RUN =====
if __name__ == "__main__":
    root = tk.Tk()
    app = VideoCutterApp(root)
    root.mainloop()
