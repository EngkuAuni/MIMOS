# HDL Code Generator
# Input HDL task --> Generate Verilog code
# Display HDL code & testbench option 
# Download options

import streamlit as st
import ollama

def generate_hdl_code(spec, model="mistral"):
    prompt = f"""
You are an expert digital IC design engineer.
Generate a Verilog module based on the following specification. Output only the code.
Specification: {spec}
    """
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    return response["message"]["content"]

def generate_testbench(hdl_code, model="mistral"):
    prompt = f"""
You are an expert digital IC design engineer.
Given the following Verilog module, generate a simple Verilog testbench to verify its functionality. 
Output only the testbench code.
Module code:
{hdl_code}
    """
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "user", "content": prompt}
        ],
    )
    return response["message"]["content"]

st.set_page_config(page_title="HDL Generator", layout="wide")
st.title("GenAI HDL Code Generator")
st.markdown("Generate HDL code from your specification (auto-filled from previous step). You may edit if needed.")

# Pre-fill with spec from Specification page if available
if "specification" in st.session_state:
    spec = st.session_state["specification"]
    default_spec = f"Module name: {spec.get('module_name','')}\nDescription: {spec.get('description','')}\nInputs: {spec.get('inputs','')}\nOutputs: {spec.get('outputs','')}\nConstraints: {spec.get('constraints','')}\nNotes: {spec.get('notes','')}"
    spec_input = st.text_area("module Specification", value=default_spec, height=150)
else:
    st.info("No specification found. See examples below or enter manually or go to Specification page.")
    example_specs = {
        "4-bit Counter": "Create a synchronous 4-bit up counter with reset and clock inputs.",
        "D Flip-Flop": "Generate a D flip-flop module with asynchronous reset.",
        "Comparator": "Design an 8-bit magnitude comparator."
    }
    selected_example = st.selectbox("Examples", ['-- Select --'] + list(example_specs.keys()))
    if selected_example != "-- Select --":
        spec_input = st.text_area("Enter module specification:", value=example_specs[selected_example], height=150)
    else:
        spec_input = st.text_area("Enter module specification:", height=150)

if "hdl_code" not in st.session_state:
    st.session_state["hdl_code"] = ""
if "testbench_code" not in st.session_state:
    st.session_state["testbench_code"] = ""
if "generate_tb" not in st.session_state:
    st.session_state["generate_tb"] = False

if st.button("Generate HDL Code") and spec_input:
    with st.spinner("Generating HDL code..."):
        try:
            st.session_state["hdl_code"] = generate_hdl_code(spec_input)
            st.session_state["testbench_code"] = ""  # Reset testbench when new HDL is generated
            st.session_state["generate_tb"] = False  # Reset testbench trigger
        except Exception as e:
            st.error(f"Error generating HDL code: {e}")

hdl_code = st.session_state["hdl_code"]
testbench_code = st.session_state["testbench_code"]

if hdl_code:
    st.success("Generated HDL Code:")
    st.code(hdl_code, language="verilog")
    st.download_button("Download HDL Code", data=hdl_code, file_name="module.v")
    if st.button("Generate Testbench"):
        st.session_state["generate_tb"] = True

# This block runs after the button is pressed, in the next rerun
if st.session_state["generate_tb"] and not testbench_code and hdl_code:
    with st.spinner("Generating Testbench..."):
        try:
            st.session_state["testbench_code"] = generate_testbench(hdl_code)
            st.session_state["generate_tb"] = False  # Reset after generation
        except Exception as e:
            st.error(f"Error generating testbench: {e}")

testbench_code = st.session_state["testbench_code"]

if testbench_code:
    st.success("Generated Testbench:")
    st.code(testbench_code, language="verilog")
    st.download_button("Download Testbench", data=testbench_code, file_name="testbench.v")
