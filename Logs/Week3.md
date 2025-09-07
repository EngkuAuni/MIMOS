# Internship Log — Week 3 (Aug 26–29)

### Project: HDL Assistant — GenAI for IC Design Support

This week focused on developing a local GenAI-powered HDL assistant that can help generate HDL code, IC design documentation, and answer design queries.

---

### Tasks Completed

- Set up local LLM environment using Ollama to bypass API limitations (OpenAI tokens exhausted).
- Installed and configured models (Mistral) for offline inference.
- Developed first module of the HDL Assistant web app: `HDL Generator`.
- Designed dropdown presets and flexible prompt interface for FSM, counters, mux, etc.
- This module takes in user HDL design task and generates Verilog HDL code using local LLM.
- Second module developed: `HDL Assistant`, which explains HDL code or answers IC-related queries.
- Ensured the app runs fully offline using local models and responds accurately to user queries.

###### Added IC design specification page
- HDL Code generator: 
   - option to generate waveform file (.vcd) in the Verilog Code for simulation use later
   - option to generate testbench
   - option to use generated code from previous page (needs clean up)
   - validity of generated code is questionable (cross-checked with chatgpt, try to run with other models/multi model


- Simulation page

---

### Tools & Platforms Used

- Ollama (local LLM engine & server)
- Mistral7B (open source LLM)
- Streamlit 
- Python

---

### Notes

- Opted for local LLM as its more doable on current device MacBook Air M1 (2020).
- Prompt formatting significantly affects LLM output quality for Verilog generation.
- Model inference time varies — small models like Mistral offer faster local performance.
- Clean module ssparation supports expandability (future testbench generation, visualization, etc)
- Plan to explore further tools for output formatting and potential circuit diagram generation.

