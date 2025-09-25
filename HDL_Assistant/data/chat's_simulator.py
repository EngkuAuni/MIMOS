import streamlit as st
import subprocess
import os
import tempfile
from datetime import datetime

st.set_page_config(page_title="HDL Simulation", layout="wide")
st.title("🔬 HDL Simulation & Waveform Viewer")

# Initialize session state
for key in ['verilog_code', 'testbench_code', 'simulation_output', 'vcd_generated', 'vcd_path']:
    if key not in st.session_state:
        st.session_state[key] = ""

# Helper: Save code to temporary file
def save_to_temp_file(code, suffix=".v"):
    temp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix, mode="w")
    temp.write(code)
    temp.close()
    return temp.name

# Helper: Check if testbench has `initial` block and $dumpfile
def validate_testbench(tb_code):
    if 'initial' not in tb_code or '$dumpfile' not in tb_code or '$dumpvars' not in tb_code:
        return False, "Testbench must include an `initial` block and both `$dumpfile` and `$dumpvars` for VCD generation."
    return True, ""

# Code Editor Inputs
st.subheader("🧾 HDL & Testbench Input")

st.session_state.verilog_code = st.text_area(
    "Enter your Verilog HDL Code (.v):", 
    value=st.session_state.verilog_code, 
    height=300,
    placeholder="module my_module(input clk, ...);"
)

st.session_state.testbench_code = st.text_area(
    "Enter your Verilog Testbench Code:", 
    value=st.session_state.testbench_code, 
    height=300,
    placeholder="`timescale 1ns/1ps\nmodule tb;\n  ... \nendmodule"
)

# Simulate Button
if st.button("▶️ Run Simulation"):
    st.session_state.simulation_output = ""
    st.session_state.vcd_generated = False
    st.session_state.vcd_path = ""

    # Validate inputs
    if not st.session_state.verilog_code.strip():
        st.error("Verilog HDL code is required.")
    elif not st.session_state.testbench_code.strip():
        st.error("Testbench code is required.")
    else:
        valid_tb, error_msg = validate_testbench(st.session_state.testbench_code)
        if not valid_tb:
            st.error(error_msg)
        else:
            try:
                # Save HDL and TB to temp files
                hdl_path = save_to_temp_file(st.session_state.verilog_code)
                tb_path = save_to_temp_file(st.session_state.testbench_code)

                # Compile with Icarus Verilog
                vvp_output = tempfile.NamedTemporaryFile(delete=False, suffix=".out").name
                compile_cmd = ["iverilog", "-o", vvp_output, hdl_path, tb_path]
                compile_proc = subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

                # Show compilation result
                if compile_proc.returncode != 0:
                    st.error("❌ Compilation Failed")
                    st.code(compile_proc.stderr, language='bash')
                else:
                    # Run simulation
                    sim_proc = subprocess.run(["vvp", vvp_output], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    output = sim_proc.stdout + "\n" + sim_proc.stderr
                    st.session_state.simulation_output = output

                    # Look for .vcd file generated
                    vcd_files = [f for f in os.listdir() if f.endswith(".vcd")]
                    if vcd_files:
                        st.session_state.vcd_generated = True
                        st.session_state.vcd_path = vcd_files[0]
                        st.success("✅ Simulation Successful & Waveform Generated")
                    else:
                        st.warning("Simulation ran, but no .vcd file was generated. Ensure `$dumpfile` and `$dumpvars` are present.")

            except Exception as e:
                st.error(f"Unexpected error occurred: {str(e)}")

# Output Section
if st.session_state.simulation_output:
    st.subheader("📄 Simulation Output")
    st.code(st.session_state.simulation_output, language='verilog')

# VCD Download & Instructions
if st.session_state.vcd_generated and os.path.exists(st.session_state.vcd_path):
    with open(st.session_state.vcd_path, "rb") as f:
        st.download_button(
            label="📥 Download Waveform (.vcd)",
            data=f,
            file_name=st.session_state.vcd_path,
            mime="application/octet-stream"
        )

    st.info("Open the downloaded `.vcd` file using [GTKWave](http://gtkwave.sourceforge.net/) or your preferred waveform viewer.")

# Footer / About
st.markdown("---")
st.caption("This HDL simulator uses **Icarus Verilog** backend and generates `.vcd` waveform files. Ensure your testbench includes `$dumpfile` and `$dumpvars` for waveform output.")