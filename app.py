import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import torch
import clip
import cv2
from skimage.metrics import structural_similarity as ssim

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

# ===== CLIP score =====
def clip_score(img1_path, img2_path):
    image1 = preprocess(Image.open(img1_path)).unsqueeze(0).to(device)
    image2 = preprocess(Image.open(img2_path)).unsqueeze(0).to(device)

    with torch.no_grad():
        f1 = model.encode_image(image1)
        f2 = model.encode_image(image2)

    f1 = f1 / f1.norm(dim=-1, keepdim=True)
    f2 = f2 / f2.norm(dim=-1, keepdim=True)

    score = (f1 @ f2.T).item()
    return score * 100

# ===== SSIM score =====
def ssim_score(img1_path, img2_path):
    img1 = cv2.imread(img1_path)
    img2 = cv2.imread(img2_path)

    img1 = cv2.resize(img1, (256, 256))
    img2 = cv2.resize(img2, (256, 256))

    gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
    gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

    gray1 = cv2.GaussianBlur(gray1, (5,5), 0)
    gray2 = cv2.GaussianBlur(gray2, (5,5), 0)

    score, _ = ssim(gray1, gray2, full=True)
    return score * 100

# ===== Compare =====
def compare_images():
    if not img1_path or not img2_path:
        result_label.config(text="Chọn đủ 2 ảnh", fg="orange")
        return

    c_score = clip_score(img1_path, img2_path)
    s_score = ssim_score(img1_path, img2_path)

    # Combine
    final = 0.6 * c_score + 0.4 * s_score

    # Hiển thị
    clip_label.config(text=f"CLIP: {c_score:.2f}%")
    ssim_label.config(text=f"SSIM: {s_score:.2f}%")
    final_label.config(text=f"FINAL: {final:.2f}%")

    if final >= 75:
        result_label.config(text="ĐÚNG", fg="green")
    else:
        result_label.config(text="SAI", fg="red")

# ===== GUI =====
root = tk.Tk()
root.title("So sánh ảnh (CLIP + SSIM)")

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

clip_label = tk.Label(root, text="CLIP: ")
clip_label.grid(row=3, column=0, columnspan=2)

ssim_label = tk.Label(root, text="SSIM: ")
ssim_label.grid(row=4, column=0, columnspan=2)

final_label = tk.Label(root, text="FINAL: ", font=("Arial", 12))
final_label.grid(row=5, column=0, columnspan=2)

result_label = tk.Label(root, text="Kết quả", font=("Arial", 16))
result_label.grid(row=6, column=0, columnspan=2)

root.mainloop()