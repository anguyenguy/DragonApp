import tkinter as tk
from tkinter import filedialog
import csv
import cv2
from PIL import Image, ImageTk
import json
import os
from datetime import datetime

# ===== GLOBAL =====
review_video = None
original_video = None
csv_path = None

cap_review = None
cap_original = None

frame_cache = {}

data = []
rows = []
selections = []
overrides = {}

# pagination
start_index = 0
PAGE_SIZE = 30

# ===== chọn video =====
def choose_review():
    global review_video, cap_review
    review_video = filedialog.askopenfilename()
    review_label.config(text=review_video)

    if cap_review:
        cap_review.release()
    cap_review = cv2.VideoCapture(review_video)


def choose_original():
    global original_video, cap_original
    original_video = filedialog.askopenfilename()
    original_label.config(text=original_video)

    if cap_original:
        cap_original.release()
    cap_original = cv2.VideoCapture(original_video)

# ===== load CSV =====
def load_csv():
    global data, csv_path, frame_cache, start_index

    path = filedialog.askopenfilename(filetypes=[("CSV", "*.csv")])
    if not path:
        return

    csv_path = path
    frame_cache.clear()
    start_index = 0

    col_r = int(col_review_entry.get()) - 1
    col_o = int(col_original_entry.get()) - 1

    data = []

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)

        for row in reader:
            try:
                data.append((float(row[col_r]), float(row[col_o])))
            except:
                continue

    render()

# ===== frame cache =====
def get_frame(cap, time_sec, key):
    cache_key = f"{key}_{round(time_sec, 2)}"

    if cache_key in frame_cache:
        return frame_cache[cache_key]

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_id = int(time_sec * fps)

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    ret, frame = cap.read()

    if not ret:
        return None

    frame = cv2.resize(frame, (200, 120))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = ImageTk.PhotoImage(Image.fromarray(frame))

    frame_cache[cache_key] = img
    return img

# ===== checkbox =====
def on_check(idx, var):
    if var.get() == 1:
        if idx not in selections:
            selections.append(idx)
    else:
        if idx in selections:
            selections.remove(idx)

    selections.sort()
    update_states()

# ===== override =====
def on_override(idx, entry):
    val = entry.get().strip()

    if val == "":
        overrides.pop(str(idx), None)
        entry.config(bg="white")
    else:
        try:
            overrides[str(idx)] = float(val)
            entry.config(bg="#fff3a0")
        except:
            entry.config(bg="#ffcccc")

    update_states()

# ===== update START / END =====
def update_states():
    for row in rows:
        row["status"].config(text="")
        row["updated"].config(text="")

    for i in range(len(selections)):
        idx = selections[i]

        # chỉ update nếu đang visible
        for row in rows:
            if row["idx"] == idx:
                if i % 2 == 0:
                    row["status"].config(text="START", fg="green")
                else:
                    start_idx = selections[i - 1]

                    r_start, o_start = data[start_idx]
                    r_end, _ = data[idx]

                    if str(start_idx) in overrides:
                        o_start = overrides[str(start_idx)]

                    delta = r_end - r_start
                    o_end = o_start + delta

                    row["status"].config(text="END", fg="red")
                    row["updated"].config(text=f"{o_end:.2f}s")

# ===== render =====
def render():
    global rows

    for w in scroll_frame.winfo_children():
        w.destroy()

    rows = []

    end_index = min(start_index + PAGE_SIZE, len(data))

    for i in range(start_index, end_index):
        r, o = data[i]

        frame = tk.Frame(scroll_frame)
        frame.pack(pady=5)

        img1 = get_frame(cap_review, r, "review")
        img2 = get_frame(cap_original, o, "original")

        lbl1 = tk.Label(frame, image=img1)
        lbl1.image = img1
        lbl1.pack(side="left")

        tk.Label(frame, text=f"{r:.2f}s → {o:.2f}s", width=20).pack(side="left")

        lbl2 = tk.Label(frame, image=img2)
        lbl2.image = img2
        lbl2.pack(side="left")

        var = tk.IntVar(value=1 if i in selections else 0)
        chk = tk.Checkbutton(frame, variable=var)
        chk.pack(side="left")

        status = tk.Label(frame, width=6)
        status.pack(side="left")

        updated = tk.Label(frame, width=10)
        updated.pack(side="left")

        entry = tk.Entry(frame, width=8)
        entry.pack(side="left", padx=5)

        if str(i) in overrides:
            entry.insert(0, str(overrides[str(i)]))
            entry.config(bg="#fff3a0")

        entry.bind("<KeyRelease>", lambda e, i=i, en=entry: on_override(i, en))
        chk.config(command=lambda i=i, v=var: on_check(i, v))

        rows.append({
            "idx": i,
            "status": status,
            "updated": updated
        })

    update_states()

# ===== pagination =====
def next_page():
    global start_index
    if start_index + PAGE_SIZE < len(data):
        start_index += PAGE_SIZE
        render()

def prev_page():
    global start_index
    if start_index - PAGE_SIZE >= 0:
        start_index -= PAGE_SIZE
        render()

# ===== save session =====
def save_session():
    if not os.path.exists("save"):
        os.makedirs("save")

    now = datetime.now().strftime("%S-%M-%H-%d-%m-%Y")
    path = f"save/{now}.json"

    session = {
        "review_video": review_video,
        "original_video": original_video,
        "csv_path": csv_path,
        "col_review": int(col_review_entry.get()),
        "col_original": int(col_original_entry.get()),
        "selections": selections,
        "overrides": overrides
    }

    with open(path, "w") as f:
        json.dump(session, f, indent=2)

def load_session():
    global review_video, original_video, csv_path
    global selections, overrides, cap_review, cap_original, start_index, data

    path = filedialog.askopenfilename(filetypes=[("JSON", "*.json")])
    if not path:
        return

    with open(path) as f:
        session = json.load(f)

    # ===== restore basic =====
    review_video = session.get("review_video")
    original_video = session.get("original_video")
    csv_path = session.get("csv_path")

    review_label.config(text=review_video)
    original_label.config(text=original_video)

    # mở video lại
    if cap_review:
        cap_review.release()
    if cap_original:
        cap_original.release()

    cap_review = cv2.VideoCapture(review_video)
    cap_original = cv2.VideoCapture(original_video)

    # set cột
    col_review_entry.delete(0, tk.END)
    col_review_entry.insert(0, session.get("col_review", 1))

    col_original_entry.delete(0, tk.END)
    col_original_entry.insert(0, session.get("col_original", 2))

    # ===== load CSV thủ công =====
    data.clear()

    col_r = int(col_review_entry.get()) - 1
    col_o = int(col_original_entry.get()) - 1

    if not os.path.exists(csv_path):
        print("Không tìm thấy CSV")
        return

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.reader(f)
        next(reader, None)

        for row in reader:
            try:
                data.append((float(row[col_r]), float(row[col_o])))
            except:
                continue

    # ===== restore state =====
    selections = session.get("selections", [])
    overrides = session.get("overrides", {})

    # lọc index lỗi
    selections = [i for i in selections if i < len(data)]
    overrides = {k: v for k, v in overrides.items() if int(k) < len(data)}

    # reset pagination
    start_index = 0

    # clear cache để tránh mismatch frame
    frame_cache.clear()

    # render 1 lần duy nhất
    render()

# ===== export =====
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

            if str(s_idx) in overrides:
                o_start = overrides[str(s_idx)]

            delta = r_end - r_start
            o_end = o_start + delta

            writer.writerow([round(o_start, 2), round(o_end, 2)])

# ===== GUI =====
root = tk.Tk()
root.title("Clip Selector PRO v5")

tk.Button(root, text="Chọn video review", command=choose_review).pack()
review_label = tk.Label(root)
review_label.pack()

tk.Button(root, text="Chọn video original", command=choose_original).pack()
original_label = tk.Label(root)
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
tk.Button(root, text="Prev", command=prev_page).pack()
tk.Button(root, text="Next", command=next_page).pack()

tk.Button(root, text="Save Session", command=save_session).pack()
tk.Button(root, text="Load Session", command=load_session).pack()
tk.Button(root, text="Export CSV", command=export_csv).pack()

canvas = tk.Canvas(root, height=500)
scrollbar = tk.Scrollbar(root, orient="vertical", command=canvas.yview)

scroll_frame = tk.Frame(canvas)
scroll_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

root.mainloop()