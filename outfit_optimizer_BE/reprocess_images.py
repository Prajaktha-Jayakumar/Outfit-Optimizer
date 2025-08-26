#!/usr/bin/env python3
"""
Script to re-process existing images in user_images folder
and add them to the vector store metadata
"""

import os
import sys
from pathlib import Path

# Add the parent directory to the path so we can import our modules
sys.path.append('.')

from clothes_classifier import classify_image
from vector_store import add_item, load_metadata
from color_utils import dominant_color

UPLOAD_FOLDER = "data/user_images"

def reprocess_existing_images():
    """Process all images in user_images folder and add to vector store"""
    
    if not os.path.exists(UPLOAD_FOLDER):
        print(f"Upload folder {UPLOAD_FOLDER} does not exist!")
        return
    
    # Get current metadata to avoid duplicates
    existing_meta = load_metadata()
    existing_filenames = {item_data.get("filename") for item_data in existing_meta.values()}
    
    print(f"Found {len(existing_meta)} existing items in metadata")
    print(f"Existing filenames: {existing_filenames}")
    
    # Get all image files
    image_files = []
    for filename in os.listdir(UPLOAD_FOLDER):
        if filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
            image_files.append(filename)
    
    print(f"\nFound {len(image_files)} image files in {UPLOAD_FOLDER}")
    
    processed_count = 0
    skipped_count = 0
    
    for filename in image_files:
        if filename in existing_filenames:
            print(f"⏭️  Skipping {filename} (already in metadata)")
            skipped_count += 1
            continue
        
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file_path = os.path.abspath(file_path)
        
        try:
            print(f"🔄 Processing {filename}...")
            
            # Classify image → get label + embedding
            label, embedding = classify_image(file_path)
            print(f"   Classified as: {label}")
            
            # Extract dominant color
            color = dominant_color(file_path)
            color_hex = color[1] if color else "#000000"
            print(f"   Dominant color: {color_hex}")
            
            # Store in FAISS + metadata
            record = {
                "filename": filename,
                "label": label,
                "color_hex": color_hex,
                "path": file_path,
            }
            
            item_id = add_item(embedding, record)
            print(f"   ✅ Added to vector store with ID: {item_id}")
            processed_count += 1
            
        except Exception as e:
            print(f"   ❌ Error processing {filename}: {e}")
    
    print(f"\n=== Summary ===")
    print(f"Processed: {processed_count} new items")
    print(f"Skipped: {skipped_count} existing items")
    print(f"Total items now: {len(load_metadata())} items")
    
    # Show final metadata summary
    final_meta = load_metadata()
    categories = {}
    for item_data in final_meta.values():
        label = item_data.get("label", "unknown")
        categories[label] = categories.get(label, 0) + 1
    
    print(f"\nItems by category:")
    for category, count in sorted(categories.items()):
        print(f"  {category}: {count}")

if __name__ == "__main__":
    print("Re-processing existing images...")
    print("=" * 50)
    reprocess_existing_images()
    print("=" * 50)
    print("Done! You can now test /suggest endpoint with more variety.")