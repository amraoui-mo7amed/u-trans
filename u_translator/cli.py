import argparse
import json
import os
from .translator import Translator
from decouple import config

def load_config():
    """Tries to load config.json from local dir or home dir (~/.u-translator/config.json)."""
    local_path = os.path.abspath("config.json")
    home_path = os.path.expanduser("~/.u-translator/config.json")
    
    # Priority: Local project folder > Home directory
    paths = [local_path, home_path]
    for path in paths:
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    return json.load(f), path
            except Exception as e:
                print(f"Warning: Failed to load {path}: {e}")
    
    return {}, local_path

def get_args(defaults):
    """Parses CLI arguments with config.json as fallback for defaults."""
    parser = argparse.ArgumentParser(description="u-translator: Professional .po file translator.")
    parser.add_argument("file", nargs="?", help="Path to the .po file (optional if using --list-models).")
    parser.add_argument("--provider", 
                        choices=["gemini", "groq", "nvidia"], 
                        default=defaults.get("default_provider", "gemini"), 
                        help=f"AI provider (default: {defaults.get('default_provider', 'gemini')}).")
    parser.add_argument("--model", help="AI model name (overwrites config/default).")
    parser.add_argument("--list-models", action="store_true", help="List all available models for the selected provider.")
    parser.add_argument("--lang", 
                        default=defaults.get("lang", "Arabic"), 
                        help=f"Target language (default: {defaults.get('lang', 'Arabic')}).")
    parser.add_argument("--batch-size", 
                        type=int, 
                        default=defaults.get("batch_size", 10), 
                        help=f"Items per API call (default: {defaults.get('batch_size', 10)}).")
    parser.add_argument("--prompt", 
                        default=defaults.get("prompt"), 
                        help="Specific system prompt for the AI.")
    parser.add_argument("--context", help="Path to a README or context file to improve translation accuracy.")
    return parser.parse_args()

def main():
    """Main application entry point."""
    defaults, config_full_path = load_config()
    args = get_args(defaults)
    
    # Model Selection Logic
    model = args.model
    if not model:
        default_models = defaults.get("default_model", {})
        model = default_models.get(args.provider)
        if not model:
            if args.provider == "gemini": model = "gemini-1.5-flash"
            elif args.provider == "groq": model = "llama-3.1-70b-versatile"
            elif args.provider == "nvidia": model = "meta/llama-3.1-8b-instruct"
            
    # API Key retrieval from config.json first
    api_keys = defaults.get("api_keys", {})
    api_key = api_keys.get(args.provider)
    
    if not api_key or "your_" in str(api_key):
        api_key = config(f"{args.provider.upper()}_API_KEY", default=None)
        if not api_key and args.provider == "gemini":
            api_key = config("GOOGLE_API_KEY", default=None)
            
    if not api_key or "your_" in str(api_key):
        print(f"\n[!] Error: API key for {args.provider.upper()} is missing.")
        print(f"    Please edit your configuration here: {config_full_path}")
        return
        
    translator = Translator(api_key, model, args.provider)

    # --- Interactive Section: List Models ---
    if args.list_models:
        print(f"\n--- Fetching models for {args.provider.upper()} ---")
        models = translator.list_models()
        print(f"Available models:")
        for m in models:
            print(f"  - {m}")
        return

    if not args.file:
        print("\n[!] Error: No .po file specified. Provide a file path or use --help.")
        return

    # Load context if provided
    context_content = ""
    if args.context:
        if os.path.exists(args.context):
            try:
                with open(args.context, "r", encoding="utf-8") as f:
                    context_content = f.read()
                print(f" Context:    {args.context} (Loaded)")
            except Exception as e:
                print(f" Warning: Could not read context file: {e}")
        else:
            print(f" Warning: Context file not found: {args.context}")

    # Prompt formatting
    base_prompt = args.prompt or defaults.get("prompt") or "Translate following phrases precisely to {lang}."
    formatted_prompt = base_prompt.replace("{lang}", args.lang)

    print(f"\n" + "="*50)
    print(f" u-trans CLI - Localization Tool")
    print(f" Config file: {config_full_path}")
    print(f" Tip: Edit config.json to change your default model or key.")
    print(f"="*50)
    print(f" File:       {args.file}")
    print(f" Provider:   {args.provider.upper()}")
    print(f" Model:      {model}")
    print(f" Language:   {args.lang}")
    print(f" Batch Size: {args.batch_size}")
    if args.context:
        print(f" Context:    {args.context}")
    print(f"="*50 + "\n")
    
    try:
        result = translator.translate_po_file(
            args.file,
            formatted_prompt,
            args.lang,
            batch_size=args.batch_size,
            context=context_content
        )
        print(f"\nResult: {result}")
    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()