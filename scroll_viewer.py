import tkinter as tk
from tkinter import filedialog
import csv
import cv2
from PIL import Image, ImageTk

review_video = None
original_video = None
data = []

# ===== chọn video =====
def choose_review():
    global review_video
    review_video = filedialog.askopenfilename()
    review_label.config(text=review_video)

def choose_original():
    global original_video
    original_video = filedialog.askopenfilename()
    original_label.config(text=original_video)

# ===== load CSV =====
def load_csv():
    global data

    path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
    if not path:
        return

    col_r = int(col_review_entry.get()) - 1
    col_o = int(col_original_entry.get()) - 1

    data = []

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)

        first_row = next(reader, None)

        # kiểm tra nếu dòng đầu không phải số → bỏ
        try:
            float(first_row[col_r])
            float(first_row[col_o])
            # nếu parse được → đây không phải header → dùng luôn
            data.append((float(first_row[col_r]), float(first_row[col_o])))
        except:
            pass  # bỏ header

        for row in reader:
            try:
                r_time = float(row[col_r])
                o_time = float(row[col_o])
                data.append((r_time, o_time))
            except:
                continue

    render_list()

# ===== lấy frame =====
def get_frame(video_path, time_sec):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)

    frame_id = int(time_sec * fps)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)

    ret, frame = cap.read()
    cap.release()

    if not ret:
        return None

    frame = cv2.resize(frame, (240, 135))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return ImageTk.PhotoImage(Image.fromarray(frame))

# ===== CONVERT TIME =====
def sec_to_hms(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# ===== render scroll list =====
def render_list():
    for widget in scroll_frame.winfo_children():
        widget.destroy()

    for i, (r_time, o_time) in enumerate(data):
        row_frame = tk.Frame(scroll_frame)
        row_frame.pack(pady=5)

        img1 = get_frame(review_video, r_time)
        img2 = get_frame(original_video, o_time)

        lbl1 = tk.Label(row_frame, image=img1)
        lbl1.image = img1
        lbl1.pack(side="left")

        text = tk.Label(
            row_frame,
            text=f"{sec_to_hms(r_time)}s  →  {sec_to_hms(o_time)}s",
            width=20
        )
        text.pack(side="left", padx=10)

        lbl2 = tk.Label(row_frame, image=img2)
        lbl2.image = img2
        lbl2.pack(side="left")

# ===== GUI =====
root = tk.Tk()
root.title("Video Compare Scroll Tool")

tk.Button(root, text="Chọn video review", command=choose_review).pack()
review_label = tk.Label(root, text="Chưa chọn")
review_label.pack()

tk.Button(root, text="Chọn video original", command=choose_original).pack()
original_label = tk.Label(root, text="Chưa chọn")
original_label.pack()

# chọn cột
frame_col = tk.Frame(root)
frame_col.pack()

tk.Label(frame_col, text="Cột review:").grid(row=0, column=0)
col_review_entry = tk.Entry(frame_col, width=5)
col_review_entry.insert(0, "1")
col_review_entry.grid(row=0, column=1)

tk.Label(frame_col, text="Cột original:").grid(row=0, column=2)
col_original_entry = tk.Entry(frame_col, width=5)
col_original_entry.insert(0, "3")
col_original_entry.grid(row=0, column=3)

tk.Button(root, text="Load CSV", command=load_csv).pack()

# ===== scroll area =====
canvas = tk.Canvas(root, height=500)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)

scroll_frame = tk.Frame(canvas)

scroll_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
)

canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

root.mainloop()