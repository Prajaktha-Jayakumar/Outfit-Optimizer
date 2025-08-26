import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any
import random

def extract_info_from_filename(filename: str) -> Dict[str, Any]:
    """Extract clothing information from filename patterns."""
    filename_lower = filename.lower()
    
    # Determine category based on filename patterns
    category = "unknown"
    if any(word in filename_lower for word in ['top', 'shirt', 'blouse', 'tank', 'crop', 'tee']):
        category = "top"
    elif any(word in filename_lower for word in ['pant', 'jean', 'trouser', 'bottom', 'skirt', 'short']):
        category = "bottom"
    elif any(word in filename_lower for word in ['shoe', 'boot', 'sneaker', 'sandal', 'heel']):
        category = "shoe"
    elif any(word in filename_lower for word in ['dress']):
        category = "dress"
    elif any(word in filename_lower for word in ['jacket', 'coat', 'blazer', 'cardigan']):
        category = "outerwear"
    
    # Extract color from filename if possible
    color_mappings = {
        'black': '#000000',
        'white': '#FFFFFF',
        'red': '#FF0000',
        'blue': '#0000FF',
        'green': '#008000',
        'yellow': '#FFFF00',
        'pink': '#FFC0CB',
        'purple': '#800080',
        'orange': '#FFA500',
        'brown': '#A52A2A',
        'gray': '#808080',
        'grey': '#808080',
        'navy': '#000080',
        'beige': '#F5F5DC',
        'rust': '#B7410E',
        'gold': '#FFD700',
        'silver': '#C0C0C0',
        'maroon': '#800000',
        'teal': '#008080',
        'olive': '#808000',
    }
    
    detected_color = None
    detected_hex = None
    
    for color_name, hex_code in color_mappings.items():
        if color_name in filename_lower:
            detected_color = color_name.title()
            detected_hex = hex_code
            break
    
    # If no color detected, assign a random one or use default
    if not detected_color:
        detected_color = "Unknown"
        detected_hex = "#808080"  # Gray as default
    
    # Generate a readable label
    label = generate_label(filename, category, detected_color)
    
    return {
        "filename": filename,
        "label": label,
        "category": category,
        "color": detected_color,
        "color_hex": detected_hex,
        "image": f"user_images/{filename}"  # Path relative to backend
    }

def generate_label(filename: str, category: str, color: str) -> str:
    """Generate a human-readable label from filename."""
    
    # Remove file extension
    base_name = os.path.splitext(filename)[0]
    
    # Remove common prefixes/suffixes
    base_name = re.sub(r'(image\d*|img\d*)', '', base_name, flags=re.IGNORECASE)
    
    # If it's a very long filename, try to extract meaningful parts
    if len(base_name) > 50:
        # Look for brand names, product types, etc.
        parts = re.split(r'[-_\s]+', base_name)
        meaningful_parts = []
        
        for part in parts[:5]:  # Take first 5 parts max
            if len(part) > 2 and not re.match(r'^[a-f0-9]+$', part):  # Skip hex codes
                meaningful_parts.append(part.title())
        
        if meaningful_parts:
            label = ' '.join(meaningful_parts)
        else:
            label = f"{color} {category.title()}"
    else:
        # For shorter filenames, clean them up
        label = re.sub(r'[-_]+', ' ', base_name).title()
    
    # Ensure category is mentioned if not already in label
    if category != "unknown" and category not in label.lower():
        label = f"{color} {category.title()}"
    
    return label

def scan_user_images(images_dir: str = "data/user_images") -> List[Dict[str, Any]]:
    """Scan user_images directory and extract metadata for all images."""
    
    if not os.path.exists(images_dir):
        print(f"❌ Directory {images_dir} not found!")
        return []
    
    supported_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}
    wardrobe_items = []
    
    print(f"🔍 Scanning {images_dir} for images...")
    
    for filename in os.listdir(images_dir):
        file_path = os.path.join(images_dir, filename)
        
        # Skip directories and non-image files
        if not os.path.isfile(file_path):
            continue
            
        file_ext = os.path.splitext(filename)[1].lower()
        if file_ext not in supported_extensions:
            print(f"⏭️  Skipping {filename} (not an image)")
            continue
        
        print(f"📸 Processing: {filename}")
        
        # Extract metadata from filename
        item_data = extract_info_from_filename(filename)
        wardrobe_items.append(item_data)
        
        print(f"   ✅ Added: {item_data['label']} ({item_data['category']}) - {item_data['color']}")
    
    return wardrobe_items

def update_wardrobe_metadata(
    wardrobe_items: List[Dict[str, Any]],
    metadata_file: str = "data/wardrobe.json"  # <-- renamed output file
):
    """Update the wardrobe metadata JSON file with a list format."""
    
    os.makedirs(os.path.dirname(metadata_file), exist_ok=True)
    
    # Write as a list, not a dictionary
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(wardrobe_items, f, indent=2, ensure_ascii=False)
    
    print(f"Saved wardrobe as a list to {metadata_file} with {len(wardrobe_items)} items")


def main():
    """Main function to populate wardrobe metadata."""
    
    print("🚀 Starting automatic wardrobe population...")
    
    # Configuration
    images_directory = "data/user_images"
    metadata_file = "data/wardrobe.json"
    
    # Check if images directory exists
    if not os.path.exists(images_directory):
        print(f"❌ Images directory '{images_directory}' not found!")
        print("Please make sure you have the correct path to your user_images folder.")
        return
    
    # Scan for images
    wardrobe_items = scan_user_images(images_directory)
    
    if not wardrobe_items:
        print("❌ No images found to process!")
        return
    
    # Show summary
    print(f"\n📊 Summary:")
    print(f"   Total items found: {len(wardrobe_items)}")
    
    # Count by category
    categories = {}
    for item in wardrobe_items:
        cat = item['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    for category, count in categories.items():
        print(f"   {category.title()}: {count}")
    
    # Ask for confirmation
    print(f"\n🤔 This will update {metadata_file}")
    confirm = input("Proceed? (y/N): ").strip().lower()
    
    if confirm in ['y', 'yes']:
        # Update metadata file
        update_wardrobe_metadata(wardrobe_items, metadata_file)
        print("✅ Wardrobe metadata updated successfully!")
        
        # Show sample items
        print(f"\n📋 Sample items added:")
        for item in wardrobe_items[:3]:
            print(f"   • {item['label']} ({item['filename'][:50]}{'...' if len(item['filename']) > 50 else ''})")
        
        if len(wardrobe_items) > 3:
            print(f"   ... and {len(wardrobe_items) - 3} more items")
            
    else:
        print("❌ Operation cancelled.")

# Function to run as a watcher (bonus feature)
def watch_and_update():
    """Watch for new files and auto-update metadata."""
    import time
    
    print("👀 Watching for changes in user_images directory...")
    print("Press Ctrl+C to stop")
    
    images_dir = "data/user_images"
    metadata_file = "data/wardrobe.json"
    
    last_files = set()
    if os.path.exists(images_dir):
        last_files = set(os.listdir(images_dir))
    
    try:
        while True:
            if os.path.exists(images_dir):
                current_files = set(os.listdir(images_dir))
                new_files = current_files - last_files
                
                if new_files:
                    print(f"🆕 New files detected: {new_files}")
                    wardrobe_items = scan_user_images(images_dir)
                    update_wardrobe_metadata(wardrobe_items, metadata_file)
                    last_files = current_files
            
            time.sleep(5)  # Check every 5 seconds
            
    except KeyboardInterrupt:
        print("\n👋 Stopping file watcher...")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--watch":
        watch_and_update()
    else:
        main()