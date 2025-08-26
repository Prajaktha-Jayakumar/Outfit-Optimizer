import os
import json
import requests
from typing import List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

LLM_BACKEND = os.getenv("LLM_BACKEND", "ollama").lower()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b")


def build_prompt(event: str, picks: Dict[str, Dict[str, Any]]) -> str:
    """Build event-specific prompt for the LLM with actual filenames."""
    
    # Event-specific context
    event_contexts = {
        "office": "professional work environment. Focus on business-appropriate, polished looks that convey competence and professionalism.",
        "casual": "relaxed, everyday activities. Emphasize comfort, versatility, and effortless style.",
        "party": "social celebration or evening event. Consider more bold choices, statement pieces, and festive elements.",
        "formal": "formal occasion requiring elegant attire. Focus on sophisticated, refined combinations.",
        "weekend": "leisurely weekend activities. Prioritize comfort while maintaining a put-together appearance."
    }
    
    # Get event context (default to casual if not found)
    context = event_contexts.get(event.lower(), f"{event} occasion. Consider what's appropriate for this specific event type.")
    
    lines = [
        "You are an expert fashion stylist with years of experience in outfit coordination.",
        f"EVENT: {event.upper()}",
        f"CONTEXT: This outfit is for a {context}",
        "",
        "AVAILABLE WARDROBE ITEMS:"
    ]
    
    # List all available items with their actual filenames and details
    filenames_mentioned = []
    for cat, item in picks.items():
        color = item.get("color_hex", "")
        filename = item.get("filename", "")
        filenames_mentioned.append(filename)
        lines.append(f"• {cat.upper()}: {filename} (Color: {color})")
    
    lines.extend([
        "",
        f"STYLING TASK:",
        f"Create a specific outfit recommendation for {event} using these exact items.",
        "Your response should include:",
        "1. Which specific items to wear (use EXACT filenames)",
        "2. Why this combination works for the occasion",
        "3. Color coordination explanation", 
        "4. Style tips for the event type",
        "5. Optional accessories that would complement the look",
        "",
        "Be specific about how each piece contributes to the overall look and why it's suitable for the occasion.",
        f"Remember: This is for {event}, so tailor your advice accordingly!"
    ])
    
    return "\n".join(lines)


def suggest_outfit(event: str = "casual day", picks: Dict[str, Dict[str, Any]] = None) -> Dict[str, Any]:
    """Generate event-specific outfit suggestion using actual filenames."""
    if picks is None:
        picks = {}
    
    if not picks:
        return {
            "backend": "none",
            "model": "none",
            "advice": "No items available for outfit suggestion. Please upload some clothing items first!",
            "used_items": []
        }
    
    prompt = build_prompt(event, picks)
    
    # Get list of actual filenames for later extraction
    actual_filenames = [item.get("filename", "") for item in picks.values() if item.get("filename")]
    
    try:
        # Ollama API call with higher temperature for more variety
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "options": {
                "temperature": 0.8,  # Increased for more variety
                "top_p": 0.9,        # Add some randomness
                "repeat_penalty": 1.1
            },
            "stream": False,
        }
        
        r = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        
        # Support either 'message' or 'response' depending on Ollama version
        text = data.get("message", {}).get("content") or data.get("response", "").strip()
        
        # Extract filenames that are actually mentioned in the response
        mentioned_files = extract_mentioned_filenames(text, actual_filenames)
        
        # If no specific files mentioned, include all available files
        if not mentioned_files:
            mentioned_files = actual_filenames
        
        return {
            "backend": "ollama",
            "model": OLLAMA_MODEL,
            "advice": text,
            "used_items": actual_filenames,  # send all picks explicitly
            "event": event,
            "items_selected": len(picks)
        }
        
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        # Fallback response
        return create_event_specific_fallback(event, picks, actual_filenames, str(e))


def extract_mentioned_filenames(advice_text: str, available_filenames: List[str]) -> List[str]:
    """Extract actual filenames mentioned in the advice text."""
    mentioned = []
    for filename in available_filenames:
        if filename in advice_text:
            mentioned.append(filename)
    return mentioned


def create_event_specific_fallback(event: str, picks: Dict[str, Dict[str, Any]], filenames: List[str], error: str) -> Dict[str, Any]:
    """Create event-specific fallback suggestion when Ollama is not available."""
    
    # Event-specific advice templates
    event_advice = {
        "office": {
            "intro": "Perfect professional outfit for the office:",
            "tips": [
                "The combination creates a polished, business-appropriate look",
                "Colors work together to convey professionalism", 
                "Suitable for meetings and workplace interactions",
                "Consider adding a blazer if available for extra polish"
            ]
        },
        "casual": {
            "intro": "Great casual outfit for everyday comfort:",
            "tips": [
                "This combination balances style with comfort",
                "Perfect for running errands or meeting friends",
                "Colors coordinate well without being too formal",
                "Add sneakers or casual shoes to complete the look"
            ]
        },
        "party": {
            "intro": "Stylish party outfit that will make you stand out:",
            "tips": [
                "This combination has the right balance of fun and sophistication",
                "Great for social events and celebrations",
                "The colors work well together for evening occasions",
                "Consider adding statement jewelry or accessories"
            ]
        }
    }
    
    # Get event-specific advice or default
    advice_template = event_advice.get(event.lower(), {
        "intro": f"Great outfit suggestion for {event}:",
        "tips": [
            "This combination works well for the occasion",
            "The pieces complement each other nicely",
            "Colors coordinate harmoniously together",
            "Perfect balance of style and appropriateness"
        ]
    })
    
    outfit_items = []
    for category, item in picks.items():
        filename = item.get("filename", "")
        color = item.get("color_hex", "#000000")
        outfit_items.append(f"• {category.title()}: {filename} ({color})")
    
    advice = f"""{advice_template['intro']}

{chr(10).join(outfit_items)}

Why this works for {event}:
{chr(10).join(f"• {tip}" for tip in advice_template['tips'])}

Complete the look with appropriate accessories and you're ready to go!

Note: AI styling assistant is temporarily unavailable."""

    return {
        "backend": "fallback",
        "model": "none",
        "advice": advice,
        "used_items": filenames,
        "event": event,
        "error": error
    }