import tkinter as tk
from tkinter import filedialog
import csv
import cv2
from PIL import Image, ImageTk

review_video = None
original_video = None
data = []

rows = []
selections = []  # lưu index đã tick

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
        next(reader, None)

        for row in reader:
            try:
                r = float(row[col_r])
                o = float(row[col_o])
                data.append((r, o))
            except:
                continue

    render()

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

    frame = cv2.resize(frame, (200, 120))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    return ImageTk.PhotoImage(Image.fromarray(frame))

# ===== xử lý tick =====
def on_check(idx, var, label, updated_label):
    global selections

    if var.get() == 1:
        selections.append(idx)
    else:
        if idx in selections:
            selections.remove(idx)

    selections.sort()

    update_states()

# ===== update trạng thái START / END =====
def update_states():
    current_start = None

    for i, row in enumerate(rows):
        idx = row["idx"]

        if idx in selections:
            pos = selections.index(idx)

            if pos % 2 == 0:
                # START
                row["status"].config(text="START", fg="green")
                row["updated"].config(text="")
                current_start = idx

            else:
                # END
                start_idx = selections[pos - 1]
                r_start, o_start = data[start_idx]
                r_end, _ = data[idx]

                delta = r_end - r_start
                o_end = o_start + delta

                row["status"].config(text="END", fg="red")
                row["updated"].config(text=f"{o_end:.2f}s")

        else:
            row["status"].config(text="")
            row["updated"].config(text="")

# ===== render list =====
def render():
    global rows, selections
    rows = []
    selections = []

    for widget in scroll_frame.winfo_children():
        widget.destroy()

    for i, (r, o) in enumerate(data):
        frame = tk.Frame(scroll_frame)
        frame.pack(pady=5)

        img1 = get_frame(review_video, r)
        img2 = get_frame(original_video, o)

        lbl1 = tk.Label(frame, image=img1)
        lbl1.image = img1
        lbl1.pack(side="left")

        text = tk.Label(frame, text=f"{r:.2f}s → {o:.2f}s", width=20)
        text.pack(side="left", padx=5)

        lbl2 = tk.Label(frame, image=img2)
        lbl2.image = img2
        lbl2.pack(side="left")

        var = tk.IntVar()
        chk = tk.Checkbutton(frame, variable=var)
        chk.pack(side="left", padx=5)

        status = tk.Label(frame, text="", width=6)
        status.pack(side="left")

        updated = tk.Label(frame, text="", width=10)
        updated.pack(side="left")

        chk.config(command=lambda i=i, v=var, s=status, u=updated: on_check(i, v, s, u))

        rows.append({
            "idx": i,
            "status": status,
            "updated": updated
        })

# ===== xuất CSV =====
def export_csv():
    if len(selections) < 2:
        return

    path = filedialog.asksaveasfilename(defaultextension=".csv")
    if not path:
        return

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["start", "end"])

        for i in range(0, len(selections)-1, 2):
            s_idx = selections[i]
            e_idx = selections[i+1]

            r_start, o_start = data[s_idx]
            r_end, _ = data[e_idx]

            delta = r_end - r_start
            o_end = o_start + delta

            writer.writerow([round(o_start, 2), round(o_end, 2)])

# ===== GUI =====
root = tk.Tk()
root.title("Clip Selector Tool")

tk.Button(root, text="Chọn video review", command=choose_review).pack()
review_label = tk.Label(root, text="")
review_label.pack()

tk.Button(root, text="Chọn video original", command=choose_original).pack()
original_label = tk.Label(root, text="")
original_label.pack()

frame_col = tk.Frame(root)
frame_col.pack()

tk.Label(frame_col, text="Cột review").grid(row=0, column=0)
col_review_entry = tk.Entry(frame_col, width=5)
col_review_entry.insert(0, "1")
col_review_entry.grid(row=0, column=1)

tk.Label(frame_col, text="Cột original").grid(row=0, column=2)
col_original_entry = tk.Entry(frame_col, width=5)
col_original_entry.insert(0, "2")
col_original_entry.grid(row=0, column=3)

tk.Button(root, text="Load CSV", command=load_csv).pack()
tk.Button(root, text="Export CSV", command=export_csv).pack()

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