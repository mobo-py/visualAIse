from flask import Flask, render_template, request, jsonify
from gradio_client import Client
import uuid
import os
from PIL import Image
import threading
import time

app = Flask(__name__)
client = Client("NihalGazi/FLUX-Pro-Unlimited")

GENERATED_DIR = os.path.join("static", "generated_images")
os.makedirs(GENERATED_DIR, exist_ok=True)

# Store task info: progress (0-100), image_url, error
tasks = {}

def generate_image_task(task_id, prompt, width, height, seed, randomize, server_choice):
    try:
        # Simulate progress while waiting
        for i in range(0, 10):
            tasks[task_id]["progress"] = int(i * 10 * 0.5)
            time.sleep(0.1)

        # Call the model and extract path from returned tuple
        result_tuple = client.predict(
            prompt,
            width,
            height,
            seed,
            randomize,
            server_choice,
            api_name="/generate_image"
        )

        image_path = result_tuple[0]  # Fix: result is a tuple (path, token)

        if not os.path.exists(image_path):
            tasks[task_id]["error"] = "Image file not found from model"
            tasks[task_id]["progress"] = 100
            return

        # Open and watermark the image
        original_img = Image.open(image_path).convert("RGBA")
        watermark_path = os.path.join("static", "logo.png")
        if not os.path.exists(watermark_path):
            tasks[task_id]["error"] = "Watermark image not found"
            tasks[task_id]["progress"] = 100
            return

        watermark = Image.open(watermark_path).convert("RGBA")
        alpha = watermark.split()[3].point(lambda p: int(p * 0.5))
        watermark.putalpha(alpha)

        wm_width, wm_height = watermark.size
        max_width = original_img.width // 4
        if wm_width > max_width:
            ratio = max_width / wm_width
            watermark = watermark.resize((int(wm_width * ratio), int(wm_height * ratio)), Image.LANCZOS)

        position = (
            original_img.width - watermark.width - 10,
            original_img.height - watermark.height - 10
        )
        original_img.paste(watermark, position, watermark)

        # Save the final image
        filename = f"{uuid.uuid4().hex}.webp"
        output_path = os.path.join(GENERATED_DIR, filename)
        original_img.save(output_path, format="WEBP")

        tasks[task_id]["image_url"] = f"/static/generated_images/{filename}"
        tasks[task_id]["progress"] = 100

    except Exception as e:
        tasks[task_id]["error"] = str(e)
        tasks[task_id]["progress"] = 100


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/generate", methods=["POST"])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get("prompt", "").strip()
        width = int(data.get("width", 1280))
        height = int(data.get("height", 1280))
        seed = int(data.get("seed", 0))
        randomize = bool(data.get("randomize", True))
        server_choice = data.get("server_choice", "Google US Server")

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        task_id = uuid.uuid4().hex
        tasks[task_id] = {"progress": 0, "image_url": None, "error": None}

        thread = threading.Thread(
            target=generate_image_task,
            args=(task_id, prompt, width, height, seed, randomize, server_choice),
            daemon=True
        )
        thread.start()

        return jsonify({"task_id": task_id})

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@app.route("/progress")
def progress():
    task_id = request.args.get("task_id")
    if not task_id or task_id not in tasks:
        return jsonify({"error": "Invalid or missing task_id"}), 400

    task_info = tasks[task_id]
    return jsonify({
        "progress": task_info.get("progress", 0),
        "image_url": task_info.get("image_url"),
        "error": task_info.get("error")
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
