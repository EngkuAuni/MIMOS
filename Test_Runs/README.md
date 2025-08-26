# HDL Assistant: A GenAI Tool for Verilog Code, Documentation, and IC Design Queries

This project is part of my GenAI internship initiative at MIMOS Berhad under the direction of Dr. Zulaikha. The overall objective is to develop generative AI applications across several domains. One of the proposed Proof-of-Concept (PoC) projects involves creating a GenAI assistant to support **integrated circuit (IC) design tasks**, including:

    1. HDL code generation (Verilog)
    2. IC-related design queries and documentation

Given this scope, I decided to focus on **HDL (Hardware Description Language)** as the core of this assistant for the following reasons:

- HDL is the **main language interface for IC design** workflows, especially digital design.  
- It has **structured syntax and patterns**, making it highly suitable for prompt-based generation using LLMs.  
- Tasks such as writing Verilog modules, generating FSMs, or explaining timing behavior align well with the strengths of GenAI.  
- HDL-specific support (like auto-generating modules or answering design trade-offs) offers **immediate, practical value** to IC designers.

This assistant is designed to run fully offline using **local LLMs** via [Ollama](https://ollama.com), ensuring zero API cost and improved privacy. Users will have to have the same model installed and running locally + clone the repo (setup instructions to be included)

---

## Project Outputs

This PoC aims to build a functional and lightweight HDL assistant that:

- Generates **Verilog modules** based on user requirements
- Provides **inline documentation** or comments for generated code
- Answers **common HDL and IC design questions**
- Supports FSM generation (Moore only), counters, muxes, and other fundamental modules
- Runs entirely **offline** using local LLMs (e.g. Mistral/CodeLlama)

### Modules

#### 1. `HDL Generator` (pg1)

> Generates Verilog HDL code for logic modules based on user prompts.

- Preset dropdowns for common modules (FSM, counter, MUX, etc.)
- Clean, commented Verilog code
- Downloadable `.v` file output
- Powered by local LLMs (Mistral, CodeLlama via Ollama)

#### 2. `HDL Assistant` (pg2)

> Explains HDL code or answers IC design-related questions.

- Accepts either HDL code or design queries
- Uses structured prompts to generate:

  - A summary
  - Line-by-line code commentary (if applicable)
  - Extra tips or related concepts
- Returns a JSON-formatted response (parsed and cleanly displayed in the app)

---

## Example Prompts

```
Generate Verilog code for an 8-bit up counter with enable and asynchronous reset.

Explain the difference between a D-latch and a D-flip flop.

Create a Verilog module for a 2-to-1 multiplexer with testbench.

Write a Moore FSM in Verilog with 3 states and a reset condition. 
```

## APP Structure

[ Streamlit Frontend ]  
                                 ↓  
[ Prompt Formatter ]  
                                 ↓  
[ Local LLM (Ollama API) ]  
                                 ↓  
[ Response Parser ]  
                                 ↓  
[ Display: Code, Docs, Q&A ]

- **Frontend (Streamlit)**: Input form, dropdowns and response display
- **Prompt Handler**: Builds the instructions or query for the LLM
- **LLM Backend**: Model served locally using Ollama (Mistral or CodeLlama)
- **Response Formatter**: Parsers the LLM's raw output into  readable/verifiable segments


<details>

### Notes/Reference
### Tried OpenAi but its not free, most open source aren't so we're gonna go with local models via Ollama app (Local LLM engine and server)
    - codellama:7b      # Open source language models
    - mistral

# FSM(Finite State Machine)
    - Mealy (output depends on both current state + current input) (faster response time but prone to asynchronous inputs)
    - Moore (output only depends on current state) (predictable with synchronized outputs, require more states)     # We'll focus on Moore due to their simpler output logic structure.

# Parsers (JSON/LangChain?)
    - Crucial for making LLM outputs usable and actionable in various applications by transforming LLM's raw text into structured data that applications can readily utilize
    - Ensure consistent data extraction and structure

</details>