import sys
import cv2
import csv
import json
import os
from datetime import datetime

from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *

# ===== GLOBAL =====
frame_cache = {}
data = []
selections = []
overrides = {}

cap_review = None
cap_original = None


# ===== FRAME LOADER =====
def get_frame(cap, time_sec, key):
    cache_key = f"{key}_{round(time_sec,2)}"

    if cache_key in frame_cache:
        return frame_cache[cache_key]

    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_id = int(time_sec * fps)

    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_id)
    ret, frame = cap.read()

    if not ret:
        return None

    frame = cv2.resize(frame, (160, 90))
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    h, w, ch = frame.shape
    img = QImage(frame.data, w, h, ch*w, QImage.Format_RGB888)
    pix = QPixmap.fromImage(img)

    frame_cache[cache_key] = pix
    return pix


# ===== ROW =====
class RowWidget(QWidget):
    def __init__(self, idx, r, o):
        super().__init__()
        self.idx = idx
        self.r = r
        self.o = o

        layout = QHBoxLayout()

        self.img1 = QLabel()
        self.img2 = QLabel()

        self.label = QLabel(f"{r:.2f}s → {o:.2f}s")

        self.checkbox = QCheckBox()
        self.checkbox.stateChanged.connect(self.on_check)

        self.entry = QLineEdit()
        self.entry.setFixedWidth(80)
        self.entry.textChanged.connect(self.on_override)

        layout.addWidget(self.img1)
        layout.addWidget(self.label)
        layout.addWidget(self.img2)
        layout.addWidget(self.checkbox)
        layout.addWidget(self.entry)

        self.setLayout(layout)

    def load_images(self):
        if cap_review:
            self.img1.setPixmap(get_frame(cap_review, self.r, "review"))
        if cap_original:
            self.img2.setPixmap(get_frame(cap_original, self.o, "original"))

    def on_check(self):
        if self.checkbox.isChecked():
            if self.idx not in selections:
                selections.append(self.idx)
        else:
            if self.idx in selections:
                selections.remove(self.idx)

        selections.sort()

    def on_override(self, text):
        if text.strip() == "":
            overrides.pop(str(self.idx), None)
        else:
            try:
                overrides[str(self.idx)] = float(text)
            except:
                pass


# ===== APP =====
class App(QWidget):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Clip Tool PyQt")

        layout = QVBoxLayout()

        # ===== buttons =====
        btn_review = QPushButton("Chọn video review")
        btn_review.clicked.connect(self.load_review)

        btn_original = QPushButton("Chọn video original")
        btn_original.clicked.connect(self.load_original)

        btn_csv = QPushButton("Load CSV")
        btn_csv.clicked.connect(self.load_csv)

        btn_save = QPushButton("Save Session")
        btn_save.clicked.connect(self.save_session)

        btn_load = QPushButton("Load Session")
        btn_load.clicked.connect(self.load_session)

        btn_export = QPushButton("Export CSV")
        btn_export.clicked.connect(self.export_csv)

        layout.addWidget(btn_review)
        layout.addWidget(btn_original)
        layout.addWidget(btn_csv)
        layout.addWidget(btn_save)
        layout.addWidget(btn_load)
        layout.addWidget(btn_export)

        # ===== list =====
        self.list = QListWidget()
        layout.addWidget(self.list)

        self.setLayout(layout)

    # ===== LOAD VIDEO =====
    def load_review(self):
        global cap_review
        path, _ = QFileDialog.getOpenFileName()
        if not path:
            return

        self.review_path = path
        cap_review = cv2.VideoCapture(path)

    def load_original(self):
        global cap_original
        path, _ = QFileDialog.getOpenFileName()
        if not path:
            return

        self.original_path = path
        cap_original = cv2.VideoCapture(path)

    # ===== LOAD CSV =====
    def load_csv(self):
        global data
        path, _ = QFileDialog.getOpenFileName()
        if not path:
            return

        self.csv_path = path

        data.clear()
        with open(path) as f:
            reader = csv.reader(f)
            next(reader)

            for row in reader:
                try:
                    data.append((float(row[0]), float(row[1])))
                except:
                    continue

        frame_cache.clear()
        self.render()

    # ===== RENDER =====
    def render(self):
        self.list.clear()

        for i, (r, o) in enumerate(data[:200]):  # limit để mượt
            item = QListWidgetItem()
            widget = RowWidget(i, r, o)
            widget.load_images()

            # restore state
            if i in selections:
                widget.checkbox.setChecked(True)

            if str(i) in overrides:
                widget.entry.setText(str(overrides[str(i)]))
                widget.entry.setStyleSheet("background:#fff3a0;")

            item.setSizeHint(widget.sizeHint())
            self.list.addItem(item)
            self.list.setItemWidget(item, widget)

    # ===== SAVE SESSION =====
    def save_session(self):
        if not os.path.exists("save"):
            os.makedirs("save")

        now = datetime.now().strftime("%S-%M-%H-%d-%m-%Y")
        path = f"save/{now}.json"

        session = {
            "review_video": getattr(self, "review_path", ""),
            "original_video": getattr(self, "original_path", ""),
            "csv_path": getattr(self, "csv_path", ""),
            "selections": selections,
            "overrides": overrides
        }

        with open(path, "w") as f:
            json.dump(session, f, indent=2)

        QMessageBox.information(self, "OK", "Đã lưu session")

    # ===== LOAD SESSION =====
    def load_session(self):
        global cap_review, cap_original, data, selections, overrides

        path, _ = QFileDialog.getOpenFileName(filter="JSON (*.json)")
        if not path:
            return

        with open(path) as f:
            session = json.load(f)

        review_path = session.get("review_video")
        original_path = session.get("original_video")
        csv_path = session.get("csv_path")

        if review_path and os.path.exists(review_path):
            self.review_path = review_path
            cap_review = cv2.VideoCapture(review_path)

        if original_path and os.path.exists(original_path):
            self.original_path = original_path
            cap_original = cv2.VideoCapture(original_path)

        if not csv_path or not os.path.exists(csv_path):
            QMessageBox.warning(self, "Lỗi", "Không tìm thấy CSV")
            return

        self.csv_path = csv_path

        data.clear()
        with open(csv_path) as f:
            reader = csv.reader(f)
            next(reader)

            for row in reader:
                try:
                    data.append((float(row[0]), float(row[1])))
                except:
                    continue

        selections = [i for i in session.get("selections", []) if i < len(data)]
        overrides = {k: v for k, v in session.get("overrides", {}).items() if int(k) < len(data)}

        frame_cache.clear()
        self.render()

        QMessageBox.information(self, "OK", "Đã load session")

    # ===== EXPORT =====
    def export_csv(self):
        if len(selections) < 2:
            QMessageBox.warning(self, "Lỗi", "Chưa chọn đủ START/END")
            return

        path, _ = QFileDialog.getSaveFileName()
        if not path:
            return

        with open(path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["start", "end"])

            for i in range(0, len(selections)-1, 2):
                s = selections[i]
                e = selections[i+1]

                r_start, o_start = data[s]
                r_end, _ = data[e]

                if str(s) in overrides:
                    o_start = overrides[str(s)]

                o_end = o_start + (r_end - r_start)
                writer.writerow([round(o_start, 2), round(o_end, 2)])

        QMessageBox.information(self, "OK", "Đã export CSV")


# ===== RUN =====
app = QApplication(sys.argv)
window = App()
window.resize(1000, 700)
window.show()
sys.exit(app.exec_())