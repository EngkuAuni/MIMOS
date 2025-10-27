# 🤖 Groq LLM Models Reference

This is a curated list of available LLMs supported by Groq as of September 2025. Use this to configure or test different models in your HDL/EDA Streamlit app.

---

## ✅ Recommended Models for HDL/EDA Apps

| Model ID                             | Description                                                   |
|--------------------------------------|---------------------------------------------------------------|
| `llama-3.1-8b-instant`               | Fast, small, 131K context — ideal for code and Verilog tasks |
| `llama-3.3-70b-versatile`            | Powerful, large context, great at structured logic reasoning  |

---

## 🧠 General Instruction-Tuned Models

| Model ID                                      | Description                                 |
|-----------------------------------------------|---------------------------------------------|
| `openai/gpt-oss-20b`                          | Open-source instruction-following LLM       |
| `openai/gpt-oss-120b`                         | Larger version with better reasoning        |
| `meta-llama/llama-4-maverick-17b-128e-instruct` | Newer LLaMA 4 variant, experimental         |
| `meta-llama/llama-4-scout-17b-16e-instruct`   | LLaMA 4 tuned for task performance          |
| `moonshotai/kimi-k2-instruct-0905`            | Ultra high context (up to 256k tokens!)     |
| `moonshotai/kimi-k2-instruct`                | Instruction-tuned for reasoning             |

---

## 💬 Speech & Safety Models

| Model ID                             | Description                     |
|--------------------------------------|---------------------------------|
| `playai-tts`                         | Text-to-speech                  |
| `playai-tts-arabic`                 | TTS for Arabic                  |
| `whisper-large-v3`                   | Speech-to-text (OpenAI Whisper) |
| `whisper-large-v3-turbo`             | Fast Whisper variant            |
| `meta-llama/llama-guard-4-12b`       | Content moderation              |
| `meta-llama/llama-prompt-guard-2-22m`| Input prompt filtering          |
| `meta-llama/llama-prompt-guard-2-86m`| Larger prompt guard version     |

---

## ⚗️ Experimental / Regional Models

| Model ID                         | Description                                |
|----------------------------------|--------------------------------------------|
| `groq/compound`                 | General-purpose multitask LLM              |
| `groq/compound-mini`            | Compact version of the above               |
| `gemma2-9b-it`                  | Google’s instruction-tuned Gemma           |
| `qwen/qwen3-32b`                | Qwen model from Alibaba Cloud              |
| `allam-2-7b`                    | SDAIA model (likely optimized for Arabic)  |

---

## 📝 Usage Tips

- Set your model in the `LLM_utils.py` file using:  
  ```python
  response = client.chat.completions.create(
      model="llama-3.1-8b-instant",  # or any from above
      ...
  )
  ```

- For best HDL synthesis output, use:
  - `llama-3.1-8b-instant` (fast, lean, low-resource) **RECOMMENDED**
  - `llama-3.3-70b-versatile` (deep logic, best quality)

---

_Last updated: Sept 2025_
"""