from google import genai
from google.genai import types
from decouple import config
import re
import json
from tqdm import tqdm

class Translator:
    def __init__(self, API_KEY, MODEL, PROVIDER="gemini"):
        self.provider = PROVIDER.lower()
        self.model = MODEL
        if self.provider == "gemini":
            self.client = genai.Client(api_key=API_KEY)
        elif self.provider == "groq":
            from groq import Groq
            self.client = Groq(api_key=API_KEY)
        elif self.provider == "nvidia":
            from openai import OpenAI
            self.client = OpenAI(
                base_url="https://integrate.api.nvidia.com/v1",
                api_key=API_KEY
            )
        else:
            raise ValueError(f"Provider {PROVIDER} is not supported.")

    def generate_content(self, input_text="", prompt=""):
        try:
            if self.provider == "gemini":
                response = self.client.models.generate_content(
                    model=self.model,
                    contents=input_text,
                    config=types.GenerateContentConfig(
                        system_instruction=prompt,
                    ),
                )
                return response.text
            
            elif self.provider in ["groq", "nvidia"]:
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": prompt},
                        {"role": "user", "content": input_text or "Please process this request"}
                    ],
                    temperature=0.1,
                )
                return completion.choices[0].message.content
        except Exception as e:
            error_msg = str(e)
            if "404" in error_msg or "not found" in error_msg.lower():
                raise Exception(f"Model '{self.model}' not found for provider '{self.provider}'. Please check available models using --list.")
            if "exhausted" in error_msg.lower() or "rate limit" in error_msg.lower() or "429" in error_msg:
                raise Exception(f"Rate limit exceeded for '{self.provider}'. Please wait a moment or increase your quota.")
            raise e

    def list_models(self):
        """Lists available models for the current provider."""
        try:
            if self.provider == "gemini":
                # Filter for models that support 'generateContent' and clean up the 'models/' prefix
                models = self.client.models.list(config={'page_size': 50})
                return [m.name.replace("models/", "") for m in models if "generateContent" in m.supported_generation_methods]
            
            elif self.provider == "groq":
                models = self.client.models.list()
                return [m.id for m in models.data]
            
            elif self.provider == "nvidia":
                models = self.client.models.list()
                return [m.id for m in models.data]
        except Exception as e:
            return [f"Error listing models: {str(e)}"]
        return []

    def translate_po_file(self, file_path, custom_prompt, lang, batch_size=10, context=""):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Regular expression to find msgid and msgstr pairs
        pattern = re.compile(r'msgid "(.*?)"\nmsgstr "(.*?)"', re.DOTALL)
        matches = list(pattern.finditer(content))
        
        # Filter for only untranslated entries (empty msgstr)
        untranslated = [(m.group(1), m.group(0)) for m in matches if not m.group(2)]
        
        total_strings = len(matches)
        untranslated_count = len(untranslated)
        translated_count = total_strings - untranslated_count
        
        print("-" * 50)
        print(f"PO File Statistics for: {file_path}")
        print(f"Total phrases:        {total_strings}")
        print(f"Already translated:   {translated_count}")
        print(f"Pending translation:   {untranslated_count}")
        print("-" * 50)
        
        if untranslated_count == 0:
            return "No untranslated messages found. Everything is already translated!"

        new_content = content
        
        # Translate in batches
        print(f"Starting bulk translation of {untranslated_count} items...")
        for i in tqdm(range(0, len(untranslated), batch_size), desc=f"Translating to {lang} (batches of {batch_size})"):
            batch = untranslated[i:i + batch_size]
            batch_msgids = [b[0] for b in batch]
            
            # Format the batch prompt to return JSON
            context_section = f"\nTranslation Context (README/Docs):\n{context}\n" if context else ""
            translation_prompt = (
                f"{custom_prompt}\n"
                f"{context_section}"
                f"Target Language: {lang}\n"
                f"Requirement: Translate the following items. Return the results as a plain JSON list of strings, e.g., [\"translation1\", \"translation2\", ...]. "
                f"Ensure the list order exactly matches the input order. Do not include any extra text or explanations.\n\n"
                f"Items to translate:\n{json.dumps(batch_msgids, ensure_ascii=False)}"
            )
            
            try:
                # print(f"\n[DEBUG] Sending batch {i//batch_size + 1} with {len(batch)} items...")
                response_text = self.generate_content("", translation_prompt).strip()
                
                # Clean up markdown code blocks if present
                if "```json" in response_text:
                    response_text = response_text.split("```json")[-1].split("```")[0].strip()
                elif "```" in response_text:
                    response_text = response_text.split("```")[-1].split("```")[0].strip()
                
                if not response_text:
                    raise ValueError("Empty response received from AI provider.")

                translated_batch = json.loads(response_text)
                
                if len(translated_batch) == len(batch):
                    for (msgid, old_entry), translated_text in zip(batch, translated_batch):
                        new_entry = f'msgid "{msgid}"\nmsgstr "{translated_text}"'
                        new_content = new_content.replace(old_entry, new_entry, 1)
                else:
                    print(f"\n\033[91m[ERROR] Batch size mismatch. Expected {len(batch)}, got {len(translated_batch)}. Skipping this batch.\033[0m")
            except Exception as e:
                error_msg = str(e)
                print(f"\n\033[91m[ERROR] Exception during batch translation: {error_msg}\033[0m")
                
                # If it's a rate limit or quota error, stop the process
                if "rate limit" in error_msg.lower() or "429" in error_msg or "quota" in error_msg.lower():
                    print("\033[93mStopping process due to rate limits. Progress saved.\033[0m")
                    break

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        
        return "Bulk translation complete."

