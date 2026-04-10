# u-trans

A professional, multi-provider CLI tool for translating `.po` files en masse using state-of-the-art AI models.

## Features

- **Multi-Provider Support**: Switch seamlessly between **Google Gemini**, **Groq**, and **NVIDIA** (NIM).
- **Context-Aware Translations**: Provide a `README.md` or any text file as context to improve translation accuracy and terminology consistency.
- **Robust PO Parsing**: Handles multiline strings, escaped quotes, and complex file formatting natively.
- **Intelligent Batching**: Translates multiple strings in a single API call to save on rate limits and speed up processing.
- **Auto-Stop & Save**: Automatically stops the process if rate limits are hit, ensuring all successful translations are saved immediately.
- **Rich Feedback**: Colorized terminal output, progress bars, and statistical summaries for a professional experience.
- **Smart Filtering**: Automatically ignores PO metadata/headers, focusing only on your actual text.

## Installation

### Option 1: Global Installation (Recommended)
This installs `u-trans` in an isolated environment and makes it available system-wide:

```bash
pipx install .
```

### Option 2: Editable/Development Installation
Use this if you plan on modifying the source code:

```bash
pip install -e .
```

## Configuration & Persistence

`u-trans` looks for its `config.json` file in two locations:
1.  **Local Folder**: The directory where you launched the command.
2.  **Home Folder**: `~/.u-trans/config.json` (Recommended for persistent settings).

### `config.json` Structure

```json
{
    "api_keys": {
        "gemini": "YOUR_GEMINI_API_KEY",
        "groq": "YOUR_GROQ_API_KEY",
        "nvidia": "YOUR_NVIDIA_API_KEY"
    },
    "default_provider": "gemini",
    "default_model": {
        "gemini": "gemini-1.5-flash",
        "groq": "llama-3.1-70b-versatile",
        "nvidia": "meta/llama-3.1-8b-instruct"
    },
    "batch_size": 10,
    "lang": "Arabic",
    "prompt": "Translate following phrases precisely to {lang}."
}
```

### Important Note on Installation:
If you installed the tool in **editable mode** (`pip install -e .`), deleting the project folder **will break the u-trans command**. 

**Recommended Setup:**
*   Move your `config.json` to `~/.u-trans/config.json` to ensure your API keys and settings are preserved even if you change or delete the source code.
*   The CLI will always print the path to the current config file it is using.

## CLI Usage

Basic command structure:

```bash
u-trans [FILE_PATH] [OPTIONS]
```

### Options:
- `--list-models`: List all available models for a provider (e.g. `u-trans --provider groq --list-models`).
- `--provider`: Choose `gemini`, `groq`, or `nvidia`.
- `--lang`: Target language (defaults to Arabic).
- `--batch-size`: Number of phrases per request (default: 10).
- `--model`: Manually specify a model.
- `--context`: Path to a text file (like `README.md`) to provide translation context.

### Examples:

1. **List available models (Groq):**
   ```bash
   u-trans --provider groq --list-models
   ```

2. **Translate with context for better accuracy:**
   ```bash
   u-trans django.po --context README.md --lang Arabic
   ```

3. **Translate using custom settings:**
   ```bash
   u-trans django.po --provider nvidia --batch-size 20
   ```

## Uninstallation

To remove `u-trans` from your system:

### If installed via pipx:
```bash
pipx uninstall u-translator
```

### If installed via pip:
```bash
pip uninstall u-translator
```

## Troubleshooting & Best Practices

### Handling Rate Limits
If you encounter a `Rate limit exceeded` error, `u-trans` will automatically stop and write current progress to the file. 
1. **Wait and resume**: Wait a few minutes and run the command again. It will skip already translated items.
2. **Switch providers**: If you hit a limit on Gemini, try switching to Groq or NVIDIA using `--provider`.

### Empty Response / Content Blocked
If you see `Empty response received from AI provider`, it usually means the AI safety filters blocked the translation or the prompt was too complex.
- **Identify the phrase**: `u-trans` logs the `Failed batch items` in the terminal for easy identification.
- **Lower Batch Size**: Run with `--batch-size 1` to isolate exactly which phrase is being blocked.
- **Clean your PO file**: If you see formatting artifacts in the failed items list, check your PO file structure.

### Optimization Tips
- **Use Context**: Always use the `--context` flag with your project's `README.md`. This helps the AI understand your specific domain and technical terms.
- **Batch Size adjustment**: 
    - Use larger batches (e.g., `20-50`) for speed if you have a high-tier API key.
    - Use smaller batches (`1-5`) for higher accuracy and to avoid safety blocks.

## License

Distributed under the MIT License. See `LICENSE` for more information.
