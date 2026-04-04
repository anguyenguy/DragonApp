import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import torch
import clip
import cv2
from skimage.metrics import structural_similarity as ssim
import imagehash

# ===== Load CLIP =====
device = "cuda" if torch.cuda.is_available() else "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

img1_path = None
img2_path = None

# ===== Hiển thị ảnh =====
def show_image(path, panel):
    img = Image.open(path)
    img = img.resize((200, 200))
    img = ImageTk.PhotoImage(img)
    panel.config(image=img)
    panel.image = img

# ===== Chọn ảnh =====
def choose_img1():
    global img1_path
    img1_path = filedialog.askopenfilename()
    show_image(img1_path, panel1)

def choose_img2():
    global img2_path
    img2_path = filedialog.askopenfilename()
    show_image(img2_path, panel2)

# ===== CLIP =====
def clip_score(p1, p2):
    image1 = preprocess(Image.open(p1)).unsqueeze(0).to(device)
    image2 = preprocess(Image.open(p2)).unsqueeze(0).to(device)

    with torch.no_grad():
        f1 = model.encode_image(image1)
        f2 = model.encode_image(image2)

    f1 = f1 / f1.norm(dim=-1, keepdim=True)
    f2 = f2 / f2.norm(dim=-1, keepdim=True)

    return (f1 @ f2.T).item() * 100

# ===== pHash =====
def phash_score(p1, p2):
    h1 = imagehash.phash(Image.open(p1))
    h2 = imagehash.phash(Image.open(p2))

    dist = h1 - h2  # càng nhỏ càng giống
    score = max(0, 100 - dist * 5)  # scale về %
    return score

# ===== SSIM =====
def ssim_score(p1, p2):
    img1 = cv2.imread(p1)
    img2 = cv2.imread(p2)

    img1 = cv2.resize(img1, (256, 256))
    img2 = cv2.resize(img2, (256, 256))

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    gray1 = cv2.GaussianBlur(gray1, (5,5), 0)
    gray2 = cv2.GaussianBlur(gray2, (5,5), 0)

    score, _ = ssim(gray1, gray2, full=True)
    return score * 100

# ===== Combine =====
def compare_images():
    if not img1_path or not img2_path:
        result_label.config(text="Chọn đủ 2 ảnh", fg="orange")
        return

    c = clip_score(img1_path, img2_path)
    p = phash_score(img1_path, img2_path)
    s = ssim_score(img1_path, img2_path)

    # Weighted score (tuned cho video)
    final = 0.4 * c + 0.3 * p + 0.3 * s

    # Hiển thị
    clip_label.config(text=f"CLIP: {c:.2f}%")
    phash_label.config(text=f"pHash: {p:.2f}%")
    ssim_label.config(text=f"SSIM: {s:.2f}%")
    final_label.config(text=f"FINAL: {final:.2f}%")

    # Decision logic (smart hơn)
    if p > 85 and s > 70:
        result = "ĐÚNG (rất chắc chắn)"
        color = "green"
    elif final > 75:
        result = "ĐÚNG"
        color = "green"
    elif final > 60:
        result = "NGHI NGỜ"
        color = "orange"
    else:
        result = "SAI"
        color = "red"

    result_label.config(text=result, fg=color)

# ===== GUI =====
root = tk.Tk()
root.title("So sánh ảnh (CLIP + pHash + SSIM)")

btn1 = tk.Button(root, text="Chọn ảnh 1", command=choose_img1)
btn1.grid(row=0, column=0)

btn2 = tk.Button(root, text="Chọn ảnh 2", command=choose_img2)
btn2.grid(row=0, column=1)

panel1 = tk.Label(root)
panel1.grid(row=1, column=0)

panel2 = tk.Label(root)
panel2.grid(row=1, column=1)

compare_btn = tk.Button(root, text="So sánh", command=compare_images)
compare_btn.grid(row=2, column=0, columnspan=2)

clip_label = tk.Label(root, text="CLIP:")
clip_label.grid(row=3, column=0, columnspan=2)

phash_label = tk.Label(root, text="pHash:")
phash_label.grid(row=4, column=0, columnspan=2)

ssim_label = tk.Label(root, text="SSIM:")
ssim_label.grid(row=5, column=0, columnspan=2)

final_label = tk.Label(root, text="FINAL:", font=("Arial", 12))
final_label.grid(row=6, column=0, columnspan=2)

result_label = tk.Label(root, text="Kết quả", font=("Arial", 16))
result_label.grid(row=7, column=0, columnspan=2)

root.mainloop()