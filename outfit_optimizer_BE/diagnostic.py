#!/usr/bin/env python3
"""
Diagnostic script to check wardrobe data sources and API endpoints
"""
import os
import json
import sys
from pathlib import Path

def check_wardrobe_json():
    """Check if wardrobe.json exists and what it contains"""
    print("📄 CHECKING WARDROBE.JSON")
    print("=" * 40)
    
    json_paths = [
        "wardrobe.json",
        "data/wardrobe.json", 
        "./wardrobe.json",
        "data/user_data/wardrobe.json"
    ]
    
    found_json = False
    for json_path in json_paths:
        if os.path.exists(json_path):
            found_json = True
            print(f"✅ Found wardrobe.json at: {json_path}")
            
            try:
                with open(json_path, 'r') as f:
                    data = json.load(f)
                
                print(f"📊 Contains {len(data)} items")
                
                if data:
                    # Show sample item
                    sample_item = data[0] if isinstance(data, list) else list(data.values())[0]
                    print(f"📋 Sample item structure:")
                    for key, value in sample_item.items():
                        print(f"   {key}: {value}")
                
                return json_path, data
                
            except Exception as e:
                print(f"❌ Error reading {json_path}: {e}")
    
    if not found_json:
        print("❌ No wardrobe.json found in common locations")
        
    return None, None

def check_vector_store():
    """Check vector store metadata"""
    print("\n🗄️  CHECKING VECTOR STORE")
    print("=" * 40)
    
    try:
        sys.path.append('.')
        from vector_store import load_metadata
        
        metadata = load_metadata()
        print(f"✅ Vector store contains {len(metadata)} items")
        
        if metadata:
            sample_id, sample_data = next(iter(metadata.items()))
            print(f"📋 Sample vector store item:")
            print(f"   ID: {sample_id}")
            for key, value in sample_data.items():
                print(f"   {key}: {value}")
        
        return metadata
        
    except ImportError:
        print("❌ Cannot import vector_store module")
        return None
    except Exception as e:
        print(f"❌ Error loading vector store: {e}")
        return None

def check_fastapi_endpoints():
    """Check what endpoints might exist in your FastAPI app"""
    print("\n🌐 CHECKING FASTAPI ENDPOINTS")
    print("=" * 40)
    
    # Look for main FastAPI file
    possible_files = ["main.py", "app.py", "server.py", "api.py"]
    
    for filename in possible_files:
        if os.path.exists(filename):
            print(f"📁 Found FastAPI file: {filename}")
            
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                
                # Look for relevant endpoints
                endpoints = []
                lines = content.split('\n')
                
                for line in lines:
                    line = line.strip()
                    if '@app.get(' in line or '@app.post(' in line:
                        endpoints.append(line)
                
                print(f"🔗 Found endpoints:")
                for endpoint in endpoints:
                    print(f"   {endpoint}")
                    
                # Check if there's a wardrobe endpoint
                wardrobe_endpoints = [ep for ep in endpoints if 'wardrobe' in ep.lower()]
                if wardrobe_endpoints:
                    print(f"👔 Wardrobe-related endpoints:")
                    for ep in wardrobe_endpoints:
                        print(f"   ✅ {ep}")
                else:
                    print(f"❌ No wardrobe-related endpoints found")
                
                return content
                
            except Exception as e:
                print(f"❌ Error reading {filename}: {e}")
    
    print("❌ No FastAPI files found")
    return None

def check_images_folder():
    """Check what's actually in the images folder"""
    print("\n📸 CHECKING IMAGES FOLDER")
    print("=" * 40)
    
    upload_folder = "data/user_images"
    
    if os.path.exists(upload_folder):
        files = [f for f in os.listdir(upload_folder) 
                if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp'))]
        
        print(f"✅ Found {len(files)} image files in {upload_folder}")
        
        if files:
            print(f"📋 Sample files:")
            for i, filename in enumerate(files[:5]):
                file_path = os.path.join(upload_folder, filename)
                file_size = os.path.getsize(file_path)
                print(f"   {i+1}. {filename} ({file_size} bytes)")
        
        return files
    else:
        print(f"❌ Upload folder {upload_folder} does not exist")
        return []

def diagnose_flutter_issue(json_data, vector_data, image_files):
    """Provide recommendations based on findings"""
    print("\n💡 DIAGNOSIS & RECOMMENDATIONS")
    print("=" * 50)
    
    # Check data source mismatch
    if json_data and vector_data:
        json_count = len(json_data)
        vector_count = len(vector_data)
        
        if json_count != vector_count:
            print(f"⚠️  Data mismatch:")
            print(f"   wardrobe.json: {json_count} items")
            print(f"   vector_store: {vector_count} items")
            print(f"   → Your app might be reading from the wrong source!")
    
    # Check if Flutter is calling the right endpoint
    print(f"\n🔍 Your Flutter app calls: ApiService.fetchWardrobe()")
    print(f"   This should correspond to a FastAPI endpoint like:")
    print(f"   @app.get('/wardrobe') or @app.get('/items') etc.")
    
    # Check image serving
    print(f"\n🖼️  Image serving analysis:")
    print(f"   Flutter expects: /images/{'{filename}'}")
    print(f"   You have FastAPI route: @app.get('/images/{'{filename}'}')")
    print(f"   Images available: {len(image_files)} files")
    
    if not image_files:
        print(f"   ❌ No images found - this is why images don't display!")
    else:
        print(f"   ✅ Images are available")
    
    # Recommendations
    print(f"\n🔧 RECOMMENDED ACTIONS:")
    
    if not image_files:
        print(f"1. 📸 Upload some images to data/user_images/")
        print(f"2. 🔄 Run your image processing script")
    
    if json_data and not vector_data:
        print(f"3. 🗄️  Your app is probably reading from wardrobe.json")
        print(f"   Make sure your FastAPI endpoint returns this data")
    elif vector_data and not json_data:
        print(f"3. 🗄️  Your app should read from vector store metadata")
        print(f"   Make sure your FastAPI endpoint queries vector_store")
    
    print(f"4. 🧪 Test your API endpoint directly:")
    print(f"   curl http://localhost:8000/wardrobe")
    print(f"5. 🧪 Test image serving:")
    if image_files:
        print(f"   curl http://localhost:8000/images/{image_files[0]}")

def main():
    print("🔍 WARDROBE DATA FLOW DIAGNOSTIC")
    print("=" * 60)
    
    # Check all data sources
    json_path, json_data = check_wardrobe_json()
    vector_data = check_vector_store()
    fastapi_content = check_fastapi_endpoints()
    image_files = check_images_folder()
    
    # Provide diagnosis
    diagnose_flutter_issue(json_data, vector_data, image_files)
    
    print("\n" + "=" * 60)
    print("✅ Diagnostic complete!")

if __name__ == "__main__":
    main()