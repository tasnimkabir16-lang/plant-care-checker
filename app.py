from flask import Flask, render_template, request
from PIL import Image
import colorsys
import requests
import io

app = Flask(__name__)


PLANTNET_API_KEY = "PASTE_YOUR_PLANTNET_API_KEY_HERE"

plant_keywords = {
    "rose": ["rose"],
    "tomato": ["tomato"],
    "mango": ["mango"],
    "hibiscus": ["hibiscus"],
    "chili": ["chili", "chilli", "pepper", "capsicum"],
    "basil": ["basil", "tulsi", "ocimum"],
    "aloe_vera": ["aloe"],
    "money_plant": ["money plant", "pothos", "epipremnum"],
}

plants = {
    "rose": {
        "name": "Rose",
        "water": "Water deeply 2-3 times a week. Avoid wetting the leaves.",
        "sunlight": "Full sun, at least 6 hours a day.",
        "fertilizer": "Balanced fertilizer (10-10-10) every 3-4 weeks.",
        "soil": "Well-drained soil, slightly acidic."
    },
    "tomato": {
        "name": "Tomato",
        "water": "Water 2-3 times a week, more when fruiting.",
        "sunlight": "Full sun, 6-8 hours a day.",
        "fertilizer": "High phosphorus at planting, then balanced fertilizer every 2-3 weeks.",
        "soil": "Rich soil with compost."
    },
    "mango": {
        "name": "Mango tree",
        "water": "Water weekly when young, less once grown.",
        "sunlight": "Full sun.",
        "fertilizer": "Balanced fertilizer 3-4 times a year.",
        "soil": "Sandy loam, well-drained."
    },
    "hibiscus": {
        "name": "Hibiscus",
        "water": "Keep soil moist, water almost daily in hot weather.",
        "sunlight": "Full sun, tolerates a bit of shade.",
        "fertilizer": "Potassium-rich fertilizer every 2-3 weeks when blooming.",
        "soil": "Rich, well-drained soil."
    },
    "chili": {
        "name": "Chili pepper",
        "water": "Water 2-3 times a week, keep soil moist while flowering.",
        "sunlight": "Full sun.",
        "fertilizer": "Balanced fertilizer, then more potassium once flowers appear.",
        "soil": "Fertile, well-drained soil."
    },
    "basil": {
        "name": "Basil (Tulsi)",
        "water": "Keep soil moist, water every 1-2 days in hot weather.",
        "sunlight": "Full sun to partial shade.",
        "fertilizer": "Light fertilizer every 4-6 weeks.",
        "soil": "Rich, well-drained soil."
    },
    "aloe_vera": {
        "name": "Aloe vera",
        "water": "Water every 2-3 weeks, let soil dry fully between waterings.",
        "sunlight": "Full sun to bright shade.",
        "fertilizer": "Light fertilizer 2-3 times during growing season.",
        "soil": "Sandy, fast-draining soil."
    },
    "money_plant": {
        "name": "Money plant",
        "water": "Water 2-3 times a week, keep soil lightly moist.",
        "sunlight": "Partial shade, avoid harsh midday sun.",
        "fertilizer": "Liquid fertilizer once a month.",
        "soil": "Well-drained, rich soil."
    },
}


def check_leaf(image):
    image = image.convert("RGB")
    image.thumbnail((100, 100))  

    width, height = image.size
    pixels = image.load()

    green_count = 0
    yellow_count = 0
    brown_count = 0
    total = 0

    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            hue = h * 360
            if s < 0.15 or v < 0.12:
                continue

            total += 1
            if 70 <= hue <= 170:
                green_count += 1
            elif 40 <= hue < 70:
                yellow_count += 1
            elif 10 <= hue < 40 and v < 0.6:
                brown_count += 1

    if total == 0:
        return {"message": "Could not find enough leaf area in the photo. Try a clearer, closer photo."}

    green_pct = round((green_count / total) * 100, 1)
    yellow_pct = round((yellow_count / total) * 100, 1)
    brown_pct = round((brown_count / total) * 100, 1)

    if brown_pct > 15:
        msg = "Leaves look dry/brown. This can mean underwatering or too much direct sun."
    elif yellow_pct > 20:
        msg = "Leaves look yellow. This can mean overwatering or a nutrient deficiency."
    elif green_pct > 50:
        msg = "Leaves look mostly healthy and green."
    else:
        msg = "No strong problem detected, but the photo was not very clear."

    return {
        "green": green_pct,
        "yellow": yellow_pct,
        "brown": brown_pct,
        "message": msg
    }


def identify_plant(filename, photo_bytes, mimetype):
    if not PLANTNET_API_KEY or PLANTNET_API_KEY == "PASTE_YOUR_PLANTNET_API_KEY_HERE":
        return None 

    url = "https://my-api.plantnet.org/v2/identify/all?api-key=" + PLANTNET_API_KEY
    files = [("images", (filename, photo_bytes, mimetype))]
    data = {"organs": "leaf"}

    try:
        response = requests.post(url, files=files, data=data, timeout=10)
        response.raise_for_status()
        result = response.json()
    except Exception as e:
        print("plantnet request failed:", e)
        return None

    if not result.get("results"):
        return None

    top = result["results"][0]
    species = top["species"]
    common_names = species.get("commonNames", [])
    scientific_name = species.get("scientificNameWithoutAuthor", "")

    text = (scientific_name + " " + " ".join(common_names)).lower()
    matched_key = None
    for key, words in plant_keywords.items():
        for word in words:
            if word in text:
                matched_key = key
                break
        if matched_key:
            break

    return {
        "matched_key": matched_key,
        "scientific_name": scientific_name,
        "common_names": common_names,
        "score": round(top.get("score", 0) * 100, 1)
    }


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html", plants=plants, result=None)


@app.route("/analyze", methods=["POST"])
def analyze():
    plant_key = request.form.get("plant")
    photo = request.files.get("photo")

    if not plant_key or plant_key not in plants:
        return render_template("index.html", plants=plants, result=None, error="Please select a plant.")

    if not photo or photo.filename == "":
        return render_template("index.html", plants=plants, result=None, error="Please upload a photo.")

    photo_bytes = photo.read()
    image = Image.open(io.BytesIO(photo_bytes))
    health = check_leaf(image)
    selected_info = plants[plant_key]

    identification = identify_plant(photo.filename, photo_bytes, photo.mimetype)

    # Which plant's care info we'll actually show. Starts as the user's
    # selection, but gets swapped to the identified plant below if PlantNet
    # is confident it's something else.
    plant_info = selected_info
    warning = None

    if identification:
        matched_key = identification["matched_key"]
        if matched_key and matched_key != plant_key:
            plant_info = plants[matched_key]
            warning = ("This looks like a " + plant_info["name"] +
                       " leaf, not " + selected_info["name"] +
                       ". Showing " + plant_info["name"] + " care info instead.")
        elif not matched_key:
            warning = ("Could not confidently match this photo to a plant in our list " +
                       "(closest guess: " + identification["scientific_name"] + "). " +
                       "Showing " + selected_info["name"] + " info since that's what you selected.")

    result = {
        "plant": plant_info,
        "health": health,
        "warning": warning
    }

    return render_template("index.html", plants=plants, result=result)


if __name__ == "__main__":
    app.run(debug=True)
