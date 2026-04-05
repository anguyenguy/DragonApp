import tkinter as tk
from tkinter import filedialog
import cv2
import numpy as np
from PIL import Image, ImageTk

video_path = None

# ===== Chọn video =====
def choose_video():
    global video_path
    video_path = filedialog.askopenfilename(
        filetypes=[("Video files", "*.mp4 *.avi *.mov")]
    )
    path_label.config(text=video_path)

# ===== Lưu timestamp =====
def save_timestamps(results):
    if not results:
        return

    save_path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text file", "*.txt")]
    )

    if not save_path:
        return

    with open(save_path, "w") as f:
        for ts, _ in results:
            minutes = int(ts // 60)
            seconds = ts % 60
            f.write(f"{minutes:02d}:{seconds:05.2f}\n")

# ===== Detect scene =====
def detect_scenes():
    if not video_path:
        result_box.insert(tk.END, "Chọn video trước\n")
        return

    cap = cv2.VideoCapture(video_path)

    fps = cap.get(cv2.CAP_PROP_FPS)
    threshold = float(threshold_entry.get())
    interval_sec = float(interval_entry.get())
    interval = int(fps * interval_sec)

    prev_frame = None
    frame_count = 0

    results = []

    result_box.delete(1.0, tk.END)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % interval == 0:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            if prev_frame is not None:
                diff = cv2.absdiff(prev_frame, gray)
                score = np.mean(diff)

                if score > threshold:
                    timestamp = frame_count / fps
                    results.append((timestamp, frame.copy()))

                    result_box.insert(tk.END, f"Scene at: {timestamp:.2f}s\n")

            prev_frame = gray

        frame_count += 1

    cap.release()

    # Hiển thị preview
    show_preview(results)

    # Lưu file txt
    save_timestamps(results)

# ===== Preview frame =====
def show_preview(results):
    for widget in preview_frame.winfo_children():
        widget.destroy()

    for i, (ts, frame) in enumerate(results[:10]):  # show tối đa 10 frame
        img = cv2.resize(frame, (160, 90))
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(Image.fromarray(img))

        lbl = tk.Label(preview_frame, image=img)
        lbl.image = img
        lbl.grid(row=i//5, column=i%5)

# ===== GUI =====
root = tk.Tk()
root.title("Scene Detection Tool")

btn = tk.Button(root, text="Chọn video", command=choose_video)
btn.pack()

path_label = tk.Label(root, text="Chưa chọn file")
path_label.pack()

# Params
param_frame = tk.Frame(root)
param_frame.pack()

tk.Label(param_frame, text="Interval (giây):").grid(row=0, column=0)
interval_entry = tk.Entry(param_frame)
interval_entry.insert(0, "1")
interval_entry.grid(row=0, column=1)

tk.Label(param_frame, text="Threshold:").grid(row=1, column=0)
threshold_entry = tk.Entry(param_frame)
threshold_entry.insert(0, "25")
threshold_entry.grid(row=1, column=1)

run_btn = tk.Button(root, text="Detect Scene", command=detect_scenes)
run_btn.pack()

result_box = tk.Text(root, height=10)
result_box.pack()

preview_frame = tk.Frame(root)
preview_frame.pack()

root.mainloop()