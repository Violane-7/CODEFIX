import os
import numpy as np
from PIL import Image
import tensorflow as tf

# ------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------

IMAGE_FOLDER = "./images"     # folder containing images named 0.png ... 9.png
MODEL_PATH = "/home/Lab703/Desktop/final-set-three/medium/fashion_classifier (1).h5"
IMG_SIZE = (28, 28)           # Fashion-MNIST size (assumed for this challenge)
EPSILON = 0.1                 # FGSM attack strength (tweak if needed)

# ------------------------------------------------------------
# LOAD MODEL
# ------------------------------------------------------------
print("[*] Loading model...")
model = tf.keras.models.load_model(MODEL_PATH)

# ------------------------------------------------------------
# HELPER: Preprocess input image to match Fashion-MNIST model
# ------------------------------------------------------------
def preprocess(img):
    """
    Convert PIL image to normalized tensor the model expects:
    - convert to grayscale
    - resize to 28x28
    - scale pixel values to [0,1]
    - add batch dimension
    """
    img = img.convert("L")
    img = img.resize(IMG_SIZE)
    arr = np.array(img) / 255.0
    arr = arr.astype(np.float32)
    arr = np.expand_dims(arr, axis=(0, -1))   # shape: (1, 28, 28, 1)
    return arr

# ------------------------------------------------------------
# LOAD & CLASSIFY ALL IMAGES
# ------------------------------------------------------------
print("[*] Scanning images...")
images = {}
predictions = {}

for fname in sorted(os.listdir(IMAGE_FOLDER)):
    if fname.endswith(".png"):
        path = os.path.join(IMAGE_FOLDER, fname)
        img = Image.open(path)

        x = preprocess(img)
        pred = model.predict(x, verbose=0)
        label = np.argmax(pred)

        images[fname] = x
        predictions[fname] = label

        print(f"Image {fname}: predicted label = {label}")

print("\n[*] Identify which image is the real FLAG image by context:")
print("    (The challenge says the correct image becomes adversarial → flag)")
print("    Pick the image that should be classified correctly in normal conditions.")
print("    Then set FLAG_IMAGE_NAME below.\n")

# ------------------------------------------------------------
# MANUAL SELECTION OF FLAG IMAGE
# ------------------------------------------------------------
# After reading printed predictions, set the correct image name manually.
# Example: if "7.png" looked like a 'Sneaker' but model predicts wrong, 
# that might be the intended FLAG image.
FLAG_IMAGE_NAME = input("Enter the filename of the correct (flag) image: ").strip()

if FLAG_IMAGE_NAME not in images:
    raise ValueError("Invalid image name entered!")

flag_image = images[FLAG_IMAGE_NAME]

# ------------------------------------------------------------
# FGSM ATTACK IMPLEMENTATION
# ------------------------------------------------------------
print("\n[*] Running FGSM attack...")

# Convert image to tensor with gradient tracking
x_adv = tf.Variable(flag_image)

# Get the true (intended) label the image SHOULD have
true_label = predictions[FLAG_IMAGE_NAME]

# One-hot label
y_true = tf.one_hot(true_label, depth=10)
y_true = tf.reshape(y_true, (1, 10))

with tf.GradientTape() as tape:
    tape.watch(x_adv)
    preds = model(x_adv)
    loss = tf.keras.losses.categorical_crossentropy(y_true, preds)

# Gradient of loss w.r.t. image pixels
gradient = tape.gradient(loss, x_adv)

# Sign of gradient
signed_grad = tf.sign(gradient)

# FGSM perturbation
x_adv = x_adv + EPSILON * signed_grad
x_adv = tf.clip_by_value(x_adv, 0, 1)   # keep pixels valid

print("[+] FGSM perturbation applied.")

# ------------------------------------------------------------
# CLASSIFY ADVERSARIAL IMAGE
# ------------------------------------------------------------
adv_pred = model.predict(x_adv, verbose=0)
adv_label = np.argmax(adv_pred)

print("\n====================================================")
print(" ORIGINAL PREDICTION :", predictions[FLAG_IMAGE_NAME])
print(" ADVERSARIAL LABEL  :", adv_label)
print("====================================================")
print("\n🎉 **FLAG = Misclassified label =", adv_label, "** 🎉")
