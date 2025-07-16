import google.generativeai as genai
import os
import re
from dotenv import load_dotenv
from prompts import (
    creative_prompt_template,
    caption_analysis_template,
    image_caption_suggestion_template,
    localization_template,
)

# Load environment variables (for API key)
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("Gemini API key not found in .env. Please set GEMINI_API_KEY.")

# Configure Gemini API key for the current session
genai.configure(api_key=API_KEY)
MODEL_NAME = "gemini-1.5-flash"

def extract_num_ideas(user_prompt):
    """
    Returns the first integer found in the user prompt,
    or defaults to 3 if no number is found.
    """
    match = re.search(r"(\d+)", user_prompt)
    if match:
        return int(match.group(1))
    return 3

def generate_creative_ideas(user_prompt, style):
    """
    Generates creative ideas/slogans based on the user's prompt and desired style.
    Returns both the list of ideas and a list of variations with additional scoring info for A/B simulation.
    """
    num = extract_num_ideas(user_prompt)
    prompt = creative_prompt_template.format(prompt=user_prompt, style=style, num=num)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    text = response.text.strip()
    ideas = []
    variations = []
    for line in text.split('\n'):
        if "." in line:
            parts = line.split(".", 1)
            idea = parts[1].strip().strip('"')
            if "(" in idea:
                caption, meta = idea.rsplit("(", 1)
                score = None
                why = None
                if "Engagement:" in meta:
                    score_part = meta.split("Engagement:")[1].split("/")[0].strip()
                    try:
                        score = float(score_part)
                    except:
                        score = None
                if "Why:" in meta:
                    why = meta.split("Why:")[1].strip().rstrip(")")
                variations.append({
                    "caption": caption.strip(),
                    "score": score,
                    "why": why if why else "",
                    "recommended": False,
                })
                ideas.append(caption.strip())
            else:
                ideas.append(idea)
    # Mark the top-scoring idea as recommended
    if variations:
        top_idx = max(range(len(variations)), key=lambda i: variations[i]['score'] or 0)
        variations[top_idx]['recommended'] = True
    return ideas, variations

def analyze_caption(image, caption):
    """
    Analyzes a given caption with an image to provide engagement, brand voice, compliance, and alternate suggestions.
    """
    import io
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()

    prompt = caption_analysis_template.format(caption=caption)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        [prompt, {"mime_type": "image/png", "data": img_bytes}]
    )
    result = {
        "engagement_score": None,
        "brand_voice": "",
        "compliance": "",
        "caption_variations": [],
    }
    lines = response.text.strip().split('\n')
    for line in lines:
        if line.lower().startswith("engagement score:"):
            try:
                result["engagement_score"] = float(line.split(":")[1].strip().split("/")[0])
            except:
                result["engagement_score"] = None
        elif line.lower().startswith("brand voice:"):
            result["brand_voice"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("compliance:"):
            result["compliance"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("suggested captions:"):
            continue
        elif line.strip() and (line.strip()[0] in "123456789"):
            cap = line.split(".", 1)[1].strip().strip('"')
            result["caption_variations"].append({
                "caption": cap,
                "score": None,
                "why": "",
                "recommended": False,
            })
    return result

def suggest_captions_from_image(image):
    """
    Suggests captions for a given image, returning details including score and compliance notes.
    """
    import io
    img_bytes = io.BytesIO()
    image.save(img_bytes, format="PNG")
    img_bytes = img_bytes.getvalue()
    prompt = image_caption_suggestion_template
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(
        [prompt, {"mime_type": "image/png", "data": img_bytes}]
    )
    lines = response.text.strip().split('\n')
    result = {
        "caption": "",
        "engagement_score": None,
        "brand_voice": "",
        "compliance": "",
        "caption_variations": [],
    }
    for line in lines:
        if line.lower().startswith("caption:"):
            result["caption"] = line.split(":", 1)[1].strip().strip('"')
        elif line.lower().startswith("engagement score:"):
            try:
                result["engagement_score"] = float(line.split(":")[1].strip().split("/")[0])
            except:
                result["engagement_score"] = None
        elif line.lower().startswith("brand voice:"):
            result["brand_voice"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("compliance:"):
            result["compliance"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("alternate captions:"):
            continue
        elif line.strip() and (line.strip()[0] in "123456789"):
            cap = line.split(".", 1)[1].strip().strip('"')
            result["caption_variations"].append({
                "caption": cap,
                "score": None,
                "why": "",
                "recommended": False,
            })
    return result

def localize_caption(caption, target_language):
    """
    Localizes the given caption to the specified language.
    """
    prompt = localization_template.format(
        caption=caption,
        target_language=target_language,
    )
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    lines = response.text.strip().split('\n')
    localized_caption = ""
    notes = ""
    for line in lines:
        if line.lower().startswith("localized caption:"):
            localized_caption = line.split(":", 1)[1].strip().strip('"')
        elif line.lower().startswith("note:"):
            notes = line.split(":", 1)[1].strip()
    return {
        "localized_caption": localized_caption,
        "notes": notes,
    }
