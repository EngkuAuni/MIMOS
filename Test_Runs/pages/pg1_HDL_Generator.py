## HDL Code Generator
## Input HDL task --> Get Verilog code
## Display result & download option

import streamlit as st
import ollama

st.set_page_config(page_title = "HDL Generator", layout = "wide")
st.title("HDL Code Generator")
st.markdown ("Describe your desired logic module. This assistant will generate HDL code (Verilog) based on your input.")

# Module Type: Counter, MUX, D Flip-Flop, ALU (arithmatic & logical computations), State Machine (ctrls operation sequence)
example_tasks = {
    "4-bit Counter": "Generate a Verilog module for a 4-bit binary counter with enable and async reset.",
    "2-to-1 Multiplexer": "Generate Verilog HDL code for 2-to-1 multiplexer with select line.",
    "D Flip-Flop" : "Write Verilog code for a D Flip-Flop with async reset.",
    "Simple ALU" : "Generate Verilog HDL code for a simple 4-bit ALU with ADD and SUB operations.",
    "Moore FSM" : "Write Verilog HDL code for a 3-state Moore FSM: IDLE, Load, DONE."
}

# Dropdown preset
selected_example = st.selectbox("HDL Task Examples", ["-- Select --"]+list(example_tasks.keys()))
if selected_example != "-- Select --":
    task_description = example_tasks[selected_example]
else:
    task_description = st.text_area ("Describe HDL module task:", height = 200)

# Generate
if st.button("Generate HDL Code") and task_description:
    with st.spinner("Generating..."):
        try:
            prompt = f"""
You are an expert digital design engineer. Generate clean, well commented Verilog HDL code.
Task: {task_description}
Only return code and comments, no extra text.
            """

            response = ollama.chat(
                model = "mistral", 
                messages = [
                    {"role": "user", "content": prompt}
                ],
            )

            verilog_code = response["message"]["content"]

            st.success("Verilog HDL Generated:")
            st.code(verilog_code, language="verilog")

            st.download_button(
                label = "Download Verilog (.v)",
                data = verilog_code,
                file_name = "generated_module.v",
                mime = "text/plain"
            )

        except Exception as e:
            st.error(f"Error: {e}")