<<<<<<< HEAD
from flask import Flask, render_template, request, jsonify
=======
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
>>>>>>> d8edd3e (Your meaningful commit message here)
from gradio_client import Client
import uuid
import os
from PIL import Image
import threading
import time
<<<<<<< HEAD
=======
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User, ImageHistory
from werkzeug.security import generate_password_hash, check_password_hash
>>>>>>> d8edd3e (Your meaningful commit message here)

app = Flask(__name__)
client = Client("NihalGazi/FLUX-Pro-Unlimited")

<<<<<<< HEAD
=======
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
db.init_app(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

>>>>>>> d8edd3e (Your meaningful commit message here)
GENERATED_DIR = os.path.join("static", "generated_images")
os.makedirs(GENERATED_DIR, exist_ok=True)

# Store task info: progress (0-100), image_url, error
tasks = {}

<<<<<<< HEAD
def generate_image_task(task_id, prompt, width, height, seed, randomize, server_choice):
=======
def generate_image_task(task_id, prompt, width, height, seed, randomize, server_choice, user_id):
>>>>>>> d8edd3e (Your meaningful commit message here)
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

<<<<<<< HEAD
=======
        # Save generated image to user history if user_id was provided
        with app.app_context():
            if user_id:
                new_history = ImageHistory(
                    image_url=f"/static/generated_images/{filename}",
                    prompt=prompt,
                    user_id=user_id
                )
                db.session.add(new_history)
                db.session.commit()

>>>>>>> d8edd3e (Your meaningful commit message here)
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

<<<<<<< HEAD
        thread = threading.Thread(
            target=generate_image_task,
            args=(task_id, prompt, width, height, seed, randomize, server_choice),
=======
        # Pass current_user.id if logged in; otherwise, pass None
        user_id = current_user.id if current_user.is_authenticated else None

        thread = threading.Thread(
            target=generate_image_task,
            args=(task_id, prompt, width, height, seed, randomize, server_choice, user_id),
>>>>>>> d8edd3e (Your meaningful commit message here)
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


<<<<<<< HEAD
=======
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash("Username already exists.")
            return redirect(url_for("signup"))
        user = User(username=username, password_hash=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect(url_for("dashboard"))
    return render_template("signup.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    if request.method == "POST":
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for("dashboard"))
        flash("Invalid credentials.")
        return redirect(url_for("login"))
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


@app.route("/dashboard")
@login_required
def dashboard():
    history = ImageHistory.query.filter_by(user_id=current_user.id).order_by(ImageHistory.timestamp.desc()).all()
    return render_template("dashboard.html", history=history)


>>>>>>> d8edd3e (Your meaningful commit message here)
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True, threaded=True)
