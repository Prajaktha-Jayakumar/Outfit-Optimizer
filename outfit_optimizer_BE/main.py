from fastapi import FastAPI, File, UploadFile, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from typing import List, Dict, Any
import os
import shutil
import numpy as np
import uuid
import random
import json
from collections import defaultdict
from dotenv import load_dotenv

from clothes_classifier import classify_image
from vector_store import add_item, load_metadata, save_metadata, search_similar
from color_utils import dominant_color
from outfit_suggester import suggest_outfit

load_dotenv()

app = FastAPI(title="Outfit Optimizer API", version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "data/user_images"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

REQUIRED_CATEGORIES = ["top", "bottom", "shoes"]
OPTIONAL_CATEGORIES = ["jacket"]


@app.get("/")
async def root():
    return {"message": "Outfit Optimizer backend is running"}


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post("/upload/")
async def upload_image(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")
    
    # Extract extension safely
    _, ext = os.path.splitext(file.filename)
    ext = ext.lower() if ext else ".jpg"
    
    # Generate a clean unique filename
    new_filename = f"{uuid.uuid4().hex}{ext}"
    file_path = os.path.join(UPLOAD_FOLDER, new_filename)
    file_path = os.path.abspath(file_path)
    
    # Security check
    if not file_path.startswith(os.path.abspath(UPLOAD_FOLDER)):
        raise HTTPException(status_code=400, detail="Invalid file path")
    
    # Save file
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Classify image → get label + embedding
    label, embedding = classify_image(file_path)
    
    # Extract dominant color
    color = dominant_color(file_path)
    
    # Store in FAISS + metadata
    record = {
        "filename": new_filename,
        "label": label,
        "color_hex": color[1] if color else "#000000",
        "path": file_path,
    }
    item_id = add_item(embedding, record)
    
    return {
        "id": item_id,
        "filename": new_filename,
        "label": label,
        "color": color,
    }


@app.get("/images")
async def list_images() -> List[Dict[str, Any]]:
    metadata = load_metadata()  # assuming your vector_store saves info
    results = []
    for name in os.listdir(UPLOAD_FOLDER):
        p = os.path.join(UPLOAD_FOLDER, name)
        if os.path.isfile(p):
            item = {"filename": name, "url": f"/images/{name}"}
            if name in metadata:
                item.update(metadata[name])
            results.append(item)
    return results


@app.get("/images/{filename}")
async def get_image(filename: str):
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(file_path)


@app.get("/suggest/")
async def get_outfit(event: str = Query(default="casual day", description="Event or occasion")):
    """Generate outfit suggestions using uploaded wardrobe items."""
    
    # FIXED: Use uploaded items metadata instead of wardrobe.json
    meta = load_metadata()  # This gets the uploaded items from vector store
    
    print(f"=== DEBUG: Found {len(meta)} uploaded items ===")
    
    if not meta:
        # Fallback to static wardrobe.json if no uploads
        try:
            wardrobe_path = "data/wardrobe.json"
            if os.path.exists(wardrobe_path):
                with open(wardrobe_path, "r") as f:
                    fallback_data = json.load(f)
                print(f"Using fallback wardrobe.json with {len(fallback_data)} items")
                
                # Convert wardrobe.json format to picks format
                picks = {}
                for item_id, item_data in fallback_data.items():
                    category = item_data.get("category", "top")  # assume category field exists
                    picks[category] = {
                        "id": item_id,
                        "filename": item_data.get("filename", ""),
                        "label": category,
                        "color_hex": item_data.get("color", "#000000"),
                        "path": ""
                    }
                
                if picks:
                    result = suggest_outfit(event, picks)
                    return result
        except Exception as e:
            print(f"Error loading fallback wardrobe: {e}")
        
        return {"message": "No wardrobe items found. Upload some clothing first!"}
    
    # Debug: Print all uploaded items
    for item_id, item_data in meta.items():
        print(f"Item {item_id}:")
        print(f"  - Filename: {item_data.get('filename', 'NO FILENAME')}")
        print(f"  - Label: {item_data.get('label', 'NO LABEL')}")
        print(f"  - Color: {item_data.get('color_hex', 'NO COLOR')}")
        print("---")
    
    # Group items by category for better selection
    items_by_category = defaultdict(list)
    for item_id, item_data in meta.items():
        label = item_data.get("label", "").lower().strip()
        
        # FIXED: More flexible label matching
        category = None
        if label in ["top", "shirt", "t-shirt", "tshirt", "blouse", "sweater", "hoodie"]:
            category = "top"
        elif label in ["bottom", "pants", "jeans", "trousers", "shorts", "skirt"]:
            category = "bottom"
        elif label in ["shoes", "shoe", "sneakers", "boots", "sandals"]:
            category = "shoes"
        elif label in ["jacket", "coat", "blazer", "cardigan"]:
            category = "jacket"
        else:
            # If we can't categorize, assume it's a top for now
            print(f"WARNING: Unknown category for label '{label}', assuming 'top'")
            category = "top"
        
        items_by_category[category].append({
            "id": item_id,
            "filename": item_data.get("filename", ""),
            "label": category,  # Use the normalized category
            "color_hex": item_data.get("color_hex", "#000000"),
            "path": item_data.get("path", "")
        })
    
    print(f"Items grouped by category: {dict(items_by_category)}")
    
    if not items_by_category:
        return {"message": "Need at least one clothing item to suggest outfits"}
    
    # Smart selection based on event type and variety
    picks = select_outfit_items(items_by_category, event)
    
    print(f"Selected items: {picks}")
    
    if not picks:
        return {"message": "Could not create a suitable outfit with available items"}
    
    # Call the LLM-powered outfit suggester
    try:
        result = suggest_outfit(event, picks)
        return result
    except Exception as e:
        print(f"Error in suggest_outfit: {e}")
        # Fallback if Ollama isn't running
        return {
            "backend": "fallback",
            "model": "none", 
            "advice": f"For {event}: Try pairing your uploaded items together! Upload more items for better suggestions.",
            "used_items": [item["filename"] for item in picks.values()],
            "error": str(e)
        }


def select_outfit_items(items_by_category: dict, event: str) -> dict:
    """
    Smart selection of outfit items based on event type and variety.
    """
    picks = {}
    
    print(f"=== Selecting items for {event} ===")
    print(f"Available categories: {list(items_by_category.keys())}")
    
    # Define event-based preferences
    event_preferences = {
        "office": {
            "priority": ["top", "bottom", "shoes", "jacket"],
            "avoid_colors": ["#ff0000", "#ffff00"],  # Avoid very bright colors
            "prefer_formal": True
        },
        "casual": {
            "priority": ["top", "bottom", "shoes"],
            "prefer_formal": False
        },
        "party": {
            "priority": ["top", "bottom", "shoes"],
            "prefer_bright": True,
            "prefer_formal": False
        }
    }
    
    # Get preferences for this event (default to casual)
    prefs = event_preferences.get(event.lower(), event_preferences["casual"])
    
    # Select items based on priority and add some randomness
    for category in prefs["priority"]:
        if category in items_by_category and items_by_category[category]:
            available_items = items_by_category[category]
            print(f"Found {len(available_items)} items in {category}")
            
            # Add some variety by occasionally picking different items
            if len(available_items) > 1:
                # 70% chance to pick randomly, 30% chance to pick first
                if random.random() > 0.3:
                    selected_item = random.choice(available_items)
                else:
                    selected_item = available_items[0]
            else:
                selected_item = available_items[0]
            
            picks[category] = selected_item
            print(f"Selected for {category}: {selected_item['filename']}")
        else:
            print(f"No items available for {category}")
    
    return picks


@app.get("/debug/metadata")
async def debug_metadata():
    """Debug endpoint to check uploaded items metadata"""
    try:
        meta = load_metadata()
        return {
            "total_items": len(meta),
            "items": meta
        }
    except Exception as e:
        return {
            "error": str(e),
            "total_items": 0,
            "items": {}
        }


@app.get("/wardrobe")
async def get_wardrobe():
    try:
        # Check if we have any uploaded items first
        metadata = load_metadata()
        
        if metadata:
            # Return uploaded items in the format the frontend expects
            wardrobe_items = []
            for item_id, item_data in metadata.items():
                wardrobe_items.append({
                    "id": item_id,
                    "label": item_data.get("label", "Unknown"),
                    "color": item_data.get("color_hex", "#000000"),
                    "image": f"images/{item_data.get('filename', '')}"  # Frontend expects this path format
                })
            return wardrobe_items
        
        # Fallback to wardrobe.json if no uploaded items
        wardrobe_path = "data/wardrobe.json"
        
        if not os.path.exists(wardrobe_path):
            # Return empty array instead of error if no wardrobe file
            return []
        
        with open(wardrobe_path, "r") as f:
            wardrobe_data = json.load(f)
        
        # Transform the data to match frontend expectations
        if isinstance(wardrobe_data, list):
            # If it's already a list, ensure proper format
            formatted_items = []
            for item in wardrobe_data:
                formatted_items.append({
                    "id": item.get("id", str(uuid.uuid4())),
                    "label": item.get("label", "Unknown"),
                    "color": item.get("color", "#000000"),
                    "image": item.get("image", "")
                })
            return formatted_items
        elif isinstance(wardrobe_data, dict):
            # If it's a dict with items, convert to list
            if "items" in wardrobe_data:
                return wardrobe_data["items"]
            else:
                # Convert dict to list format
                formatted_items = []
                for key, item in wardrobe_data.items():
                    formatted_items.append({
                        "id": key,
                        "label": item.get("label", "Unknown"),
                        "color": item.get("color", "#000000"),
                        "image": item.get("image", "")
                    })
                return formatted_items
        
        return []
        
    except json.JSONDecodeError:
        # Return empty array instead of error
        return []
    except Exception as e:
        # Log the error but return empty array to prevent frontend crashes
        print(f"Error reading wardrobe: {str(e)}")
        return []