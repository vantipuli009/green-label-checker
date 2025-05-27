import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

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

# Example usage
if __name__ == "__main__":
    sample_path = "assets/sample_label.png"  # Add your test image here
    raw_text = extract_text_from_image(sample_path)
    ingredients = parse_ingredients(raw_text)
    print("✅ Extracted Ingredients:")
    for i in ingredients:
        print("-", i)