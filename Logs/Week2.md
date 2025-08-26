# Internship Log — Week 2 (Aug 18–22)

### Project: HDL Assistant — GenAI for IC Design Support

This week focused on developing a local GenAI-powered HDL assistant that can help generate HDL code, IC design documentation, and answer design queries.

---

### Tasks Completed

* Set up local LLM environment using Ollama to bypass API limitations (OpenAI tokens exhausted).
* Installed and configured models (Mistral, CodeLlama) for offline inference.
* Developed first module of the HDL Assistant web app: `HDL Generator`.
* This module takes in user HDL design task and generates Verilog HDL code using local LLM.
* Designed dropdown presets and flexible prompt interface for FSM, counters, mux, etc.
* Second module developed: `HDL Assistant`, which explains HDL code or answers IC-related queries.
* Integrated both modules into a multi-page Streamlit app per project outline.
* Documented HDL-related concepts (FSM, HDL syntax, use cases) in README.
* Refined GitHub repo structure, organized by project folders and logs.
* Improved Week 1 object detection project docs (results folder, video, `.ipynb` included).

---

### Tools & Platforms Used

* Ollama (local LLM deployment)
* Mistral, CodeLlama
* Streamlit (multi-page app)
* Python
* GitHub (repo structure, commit tracking)
* Markdown (README, weekly logs)

---

### Notes

* Running local models requires sufficient disk space and uninterrupted downloads.
* Prompt formatting significantly affects LLM output quality for Verilog generation.
* Model inference time varies — small models like Mistral offer faster local performance.
* Documented the design structure and intent clearly to aid onboarding/future contributions.
* Plan to explore further tools for output formatting and potential circuit diagram generation.

