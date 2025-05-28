import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
from pubchem_lookup import get_cid_from_name, extract_ghs_statements, scrape_ewg

import pandas as pd
from paddleocr import PaddleOCR

import cv2
from PIL import Image

def extract_text_from_image(image_path):
    # Read image using OpenCV
    image = cv2.imread(image_path)

    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Apply thresholding for better OCR
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)

    # Convert to PIL format
    pil_img = Image.fromarray(thresh)

    # Run OCR
    text = pytesseract.image_to_string(pil_img)

    return text
from paddleocr import PaddleOCR

def extract_text_with_paddle(image_path):
    ocr = PaddleOCR(use_angle_cls=True, lang='en')  # init once
    results = ocr.ocr(image_path, cls=True)

    lines = []
    for line in results[0]:
        text = line[1][0]  # actual recognized string
        lines.append(text)

    return " ".join(lines)

def parse_ingredients(text):
    # Convert to lowercase, remove newlines
    clean_text = text.lower().replace('\n', ' ')

    # Find "ingredients: " and extract everything after it
    if "ingredients:" in clean_text:
        clean_text = clean_text.split("ingredients:")[1]

    # Remove parentheses and split by commas
    clean_text = clean_text.replace("(", "").replace(")", "")
    ingredients = [i.strip() for i in clean_text.split(",") if i.strip()]

    return ingredients

def classify_safety_from_hazards(statements):
    text = " ".join(statements).lower()
    if "cancer" in text or "fatal" in text or "carcinogen" in text:
        return "harmful"
    elif "irritant" in text or "toxic" in text or "mutation" in text:
        return "moderate"
    elif "safe" in text:
        return "safe"
    else:
        return "unknown"
import os
import pandas as pd

def ensure_csv_exists(csv_path="data/ingredient_safety.csv"):
    # Check if the CSV file exists
    if not os.path.exists(csv_path):
        print(f"📁 Creating new CSV at: {csv_path}")
        # Create with expected columns
        df = pd.DataFrame(columns=["ingredient", "safety_level", "note", "source"])
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(csv_path), exist_ok=True)
        df.to_csv(csv_path, index=False)
    else:
        print(f"📄 Found existing CSV at: {csv_path}")

def check_ingredient_safety(ingredients, csv_path="data/ingredient_safety.csv"):
    ensure_csv_exists(csv_path)
    df = pd.read_csv(csv_path)

    manual_path = "data/manual_ingredient_safety.csv"
    manual_df = pd.read_csv(manual_path) if os.path.exists(manual_path) else pd.DataFrame()

    new_entries = []
    results = []

    for ing in ingredients:
        match = manual_df[manual_df["ingredient"].str.lower() == ing.lower()]
        if not match.empty:
            level = match.iloc[0]["safety_level"]
            note = match.iloc[0]["note"]
            source = match.iloc[0]["source"]
        else:
            # 2. Existing auto-generated CSV
            match = df[df["ingredient"].str.contains(ing, case=False, na=False)]
            if not match.empty:
                level = match.iloc[0]["safety_level"]
                note = match.iloc[0]["note"]
                source = "cached"
            else:
                # Not in CSV → query PubChem
                print(f"🌐 Looking up {ing} on PubChem...")
                cid = get_cid_from_name(ing)
                if cid:
                    hazards = extract_ghs_statements(cid)
                    level = classify_safety_from_hazards(hazards)
                    note = "; ".join(hazards)[:200]
                    source = "PubChem"
                else:
                    print(f"📉 No CID found for {ing}. Falling back to EWG...")
                    ewg_data = scrape_ewg(ing)
                    level = ewg_data["safety_level"]
                    note = ewg_data["note"]
                    source = ewg_data["source"]

            
            new_entries.append({"ingredient": ing, "safety_level": level, "note": note, "source":source})
        
        results.append((ing, level, note))

    # Update CSV with new data
    if new_entries:
        df = pd.concat([df, pd.DataFrame(new_entries)], ignore_index=True)
        df.to_csv(csv_path, index=False)
        print("📁 Updated CSV with new ingredients!")

    return results

# Run pipeline
if __name__ == "__main__":
    image_path = "assets/sample 2.jpg"
    raw_text = extract_text_with_paddle(image_path)
    ingredients = parse_ingredients(raw_text)
    
    print("\n🧾 Extracted Ingredients:")
    for i in ingredients:
        print("-", i)

    print("\n🔍 Ingredient Safety Lookup (OCR ➜ PubChem):")
    
    results = check_ingredient_safety(ingredients)
    for ing, level, note in results:
        emoji = {"safe": "🟢", "moderate": "🟡", "harmful": "🔴", "unknown": "⚪"}.get(level, "⚪")
        print(f"{emoji} {ing.title():<25} → {level.upper()} — {note}")
