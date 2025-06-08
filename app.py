from flask import Flask, render_template, request, jsonify
from gradio_client import Client
import uuid
import os
from PIL import Image
import threading
import time  # For optional progress simulation

app = Flask(__name__)
client = Client("namelessai/HiDream-Unlimited")

GENERATED_DIR = os.path.join("static", "generated_images")
os.makedirs(GENERATED_DIR, exist_ok=True)

# Store task info: progress (0-100), image_url, error
tasks = {}

def generate_image_task(task_id, prompt, resolution, guidance_scale, steps, shift):
    try:
        # Optional: simulate progress updates while waiting for model
        # (If model predict is fast, you can skip this or just set progress = 0 initially)
        for i in range(0, steps, max(1, steps // 10)):
            tasks[task_id]["progress"] = int(i / steps * 100 * 0.5)  # e.g. up to 50%
            time.sleep(0.1)  # adjust as needed

        # Actual generation call (blocking)
        # The API_name "/generate_image" matches the model endpoint
        result_path = client.predict(
            prompt=prompt,
            resolution=resolution,
            guidance_scale=guidance_scale,
            num_inference_steps=steps,
            shift=shift,
            api_name="/generate_image"
        )

        if not os.path.exists(result_path):
            tasks[task_id]["error"] = "Image file not found from model"
            tasks[task_id]["progress"] = 100
            return

        # Open generated image and add watermark
        original_img = Image.open(result_path).convert("RGBA")

        watermark_path = os.path.join("static", "logo.png")
        if not os.path.exists(watermark_path):
            tasks[task_id]["error"] = "Watermark image not found"
            tasks[task_id]["progress"] = 100
            return

        watermark = Image.open(watermark_path).convert("RGBA")

        # Reduce watermark opacity to 50%
        alpha = watermark.split()[3].point(lambda p: int(p * 0.5))
        watermark.putalpha(alpha)

        # Resize watermark if too wide (max 1/4 width of original image)
        wm_width, wm_height = watermark.size
        max_width = original_img.width // 4
        if wm_width > max_width:
            ratio = max_width / wm_width
            new_size = (int(wm_width * ratio), int(wm_height * ratio))
            watermark = watermark.resize(new_size, Image.LANCZOS)

        # Position watermark bottom-right with 10px padding
        position = (
            original_img.width - watermark.width - 10,
            original_img.height - watermark.height - 10
        )
        original_img.paste(watermark, position, watermark)

        # Save final image as WEBP
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
        resolution = data.get("resolution", "1024x1024")
        guidance_scale = float(data.get("guidance_scale", 7.5))
        steps = int(data.get("num_inference_steps", 50))
        shift = int(data.get("shift", 0))

        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        task_id = uuid.uuid4().hex
        tasks[task_id] = {"progress": 0, "image_url": None, "error": None}

        thread = threading.Thread(
            target=generate_image_task,
            args=(task_id, prompt, resolution, guidance_scale, steps, shift),
            daemon=True  # Daemon thread so it doesn't block exit
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
    # Set threaded=True for concurrent requests handling
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)

