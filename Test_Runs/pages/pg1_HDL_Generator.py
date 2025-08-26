import streamlit as st
import ollama

st.set_page_config(page_title="HDL Generator", layout="wide")
st.title("HDL Code Generator")
st.markdown(
    """
    ### Generate Verilog HDL from your logic specification

    Describe the logic module you want to create. This assistant will generate clean, well-commented Verilog code based on your input.  
    Select a module type from the examples below or write your own custom task.
    """
)

EXAMPLE_TASKS = {
    "4-bit Counter": "Generate a Verilog module for a 4-bit binary counter with enable and asynchronous reset.",
    "2-to-1 Multiplexer": "Generate Verilog HDL code for a 2-to-1 multiplexer with a select line.",
    "D Flip-Flop": "Write Verilog code for a D Flip-Flop with asynchronous reset.",
    "Simple ALU": "Generate Verilog HDL code for a simple 4-bit ALU with ADD and SUB operations.",
    "Moore FSM": "Write Verilog HDL code for a 3-state Moore FSM: IDLE, LOAD, DONE."
}

with st.expander("HDL Task Examples", expanded=True):
    selected_example = st.selectbox(
        "Choose a module type for HDL generation, or select custom:",
        ["-- Custom --"] + list(EXAMPLE_TASKS.keys())
    )

if selected_example != "-- Custom --":
    task_description = EXAMPLE_TASKS[selected_example]
    st.info(f"**Task description:** {task_description}")
else:
    task_description = st.text_area(
        "Describe your HDL module task below (e.g. 'Generate a 5-bit up/down counter with synchronous reset'):",
        height=160
    )

generate_button = st.button("Generate Verilog HDL")

if generate_button and task_description:
    with st.spinner("Generating Verilog HDL code..."):
        try:
            prompt = (
                "You are an expert digital design engineer. Generate clean, well-commented Verilog HDL code.\n"
                f"Task: {task_description}\n"
                "Only return code and comments, no extra text."
            )
            response = ollama.chat(
                model="mistral",
                messages=[{"role": "user", "content": prompt}],
            )

            verilog_code = response["message"]["content"]

            st.success("Verilog HDL Generated Below:")
            st.code(verilog_code, language="verilog")

            st.download_button(
                label="Download Verilog (.v)",
                data=verilog_code,
                file_name="generated_module.v",
                mime="text/plain"
            )
        except Exception as e:
            st.error(f"Error generating HDL code: {e}")