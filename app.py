import tkinter as tk
from tkinter import filedialog, ttk
import cv2
import numpy as np
from PIL import Image
import imagehash
from skimage.metrics import structural_similarity as ssim
import torch
import clip
import csv

# ===== LOAD CLIP =====
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

review_path = None
original_path = None

# ===== CHỌN FILE =====
def choose_review():
    global review_path
    review_path = filedialog.askopenfilename()
    review_label.config(text=review_path)

def choose_original():
    global original_path
    original_path = filedialog.askopenfilename()
    original_label.config(text=original_path)

# ===== EXTRACT FRAME =====
def extract_frames(video_path, interval_sec):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    interval = int(fps * interval_sec)

    frames, timestamps = [], []
    frame_count = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_count % interval == 0:
            frames.append(frame)
            timestamps.append(frame_count / fps)

        frame_count += 1

    cap.release()
    return frames, timestamps

# ===== pHash =====
def compute_phash(frames):
    hashes = []
    for f in frames:
        img = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
        hashes.append(imagehash.phash(img))
    return hashes

# ===== SSIM =====
def ssim_score(f1, f2):
    f1 = cv2.resize(f1, (256, 256))
    f2 = cv2.resize(f2, (256, 256))
    g1 = cv2.cvtColor(f1, cv2.COLOR_BGR2GRAY)
    g2 = cv2.cvtColor(f2, cv2.COLOR_BGR2GRAY)
    score, _ = ssim(g1, g2, full=True)
    return score

# ===== CLIP =====
def clip_score(f1, f2):
    i1 = preprocess(Image.fromarray(cv2.cvtColor(f1, cv2.COLOR_BGR2RGB))).unsqueeze(0).to(device)
    i2 = preprocess(Image.fromarray(cv2.cvtColor(f2, cv2.COLOR_BGR2RGB))).unsqueeze(0).to(device)

    with torch.no_grad():
        f1_feat = model.encode_image(i1)
        f2_feat = model.encode_image(i2)

    f1_feat /= f1_feat.norm(dim=-1, keepdim=True)
    f2_feat /= f2_feat.norm(dim=-1, keepdim=True)

    return (f1_feat @ f2_feat.T).item()

# ===== CONVERT TIME =====
def sec_to_hms(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# ===== SAVE CSV =====
def save_csv(results):
    path = filedialog.asksaveasfilename(defaultextension=".csv")
    if not path:
        return

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Header
        writer.writerow([
            "Review Time (s)",
            "Review Time (HH:MM:SS)",
            "Original Time (s)",
            "Original Time (HH:MM:SS)",
            "pHash Dist",
            "SSIM",
            "CLIP"
        ])

        for r in results:
            review_s = r[0]
            original_s = r[1]

            writer.writerow([
                review_s,
                sec_to_hms(review_s),
                original_s,
                sec_to_hms(original_s),
                r[2],
                r[3],
                r[4]
            ])

# ===== MATCH =====
def match_videos():
    if not review_path or not original_path:
        result_box.insert(tk.END, "Chọn đủ 2 video\n")
        return

    interval = float(interval_entry.get())

    result_box.delete(1.0, tk.END)

    result_box.insert(tk.END, "Extract frame...\n")
    review_frames, review_ts = extract_frames(review_path, interval)
    original_frames, original_ts = extract_frames(original_path, interval)

    result_box.insert(tk.END, "Compute pHash...\n")
    original_hashes = compute_phash(original_frames)

    results = []

    total = len(review_frames)
    progress_bar["maximum"] = total

    for i, frame in enumerate(review_frames):
        # pHash
        q_hash = imagehash.phash(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))

        best_idx = -1
        best_dist = 999

        for j, h in enumerate(original_hashes):
            dist = q_hash - h
            if dist < best_dist:
                best_dist = dist
                best_idx = j

        # SSIM refine
        best_ssim = -1
        final_idx = best_idx

        for j in range(max(0, best_idx-2), min(len(original_frames), best_idx+3)):
            s = ssim_score(frame, original_frames[j])
            if s > best_ssim:
                best_ssim = s
                final_idx = j

        # CLIP
        c_score = clip_score(frame, original_frames[final_idx])

        results.append((
            round(review_ts[i], 2),
            round(original_ts[final_idx], 2),
            int(best_dist),
            round(best_ssim, 3),
            round(c_score, 3)
        ))

        result_box.insert(
            tk.END,
            f"{review_ts[i]:.2f}s → {original_ts[final_idx]:.2f}s\n"
        )

        # progress
        progress_bar["value"] = i + 1
        progress_label.config(text=f"{i+1} / {total}")
        root.update_idletasks()

    save_csv(results)

# ===== GUI =====
root = tk.Tk()
root.title("Video Matching Tool (Final)")

tk.Button(root, text="Chọn video review", command=choose_review).pack()
review_label = tk.Label(root, text="Chưa chọn")
review_label.pack()

tk.Button(root, text="Chọn video original", command=choose_original).pack()
original_label = tk.Label(root, text="Chưa chọn")
original_label.pack()

tk.Label(root, text="Interval (giây):").pack()
interval_entry = tk.Entry(root)
interval_entry.insert(0, "1")
interval_entry.pack()

tk.Button(root, text="Run Matching", command=match_videos).pack()

progress_label = tk.Label(root, text="0 / 0")
progress_label.pack()

progress_bar = ttk.Progressbar(root, orient="horizontal", length=400, mode="determinate")
progress_bar.pack()

result_box = tk.Text(root, height=15)
result_box.pack()

root.mainloop()