# Simulates HDL Code with testbench using Icarus Verilog
# Allows file uploads as a fallback.
# Shows simulation output and offers .vcd waveform download for GTKWave.

import streamlit as st
import subprocess
import os

st.set_page_config(page_title="HDL Simulation", layout="wide")
st.title("HDL Simulation & Waveform Viewer")

st.markdown("""
**Simulate your HDL design using Icarus Verilog:**  
- Code and testbench are loaded from previous steps.  
- You can also upload your own files.  
- Download the waveform (.vcd) for viewing in GTKWave.  
- Use GenAI to explain simulation results!
""")

# Pre-fill with generated HDL & tb or allow file upload
hdl_code = st.session_state.get("hdl_code", "")
tb_code = st.session_state.get("testbench_code", "")

tab1, tab2 = st.tabs(["From Previous Steps", "Upload Files"])
with tab1:
    st.text_area("HDL Code", value=hdl_code, height=150, key="hdl_code_sim")
    st.text_area("Testbench Code", value=tb_code, height=150, key="tb_code_sim")

with tab2:
    hdl_file = st.file_uploader("Upload HDL (.v) file", type=["v"])
    tb_file = st.file_uploader("Upload Testbench (.v) file", type=["v"])
    if hdl_file:
        hdl_code = hdl_file.read().decode()
        st.session_state["hdl_code_sim"] = hdl_code
    if tb_file:
        tb_code = tb_file.read().decode()
        st.session_state["tb_code_sim"] = tb_code

# Prepare sim files
sim_dir = "sim_files"
os.makedirs(sim_dir, exist_ok=True)
hdl_path = os.path.join(sim_dir, "module.v")
tb_path = os.path.join(sim_dir, "testbench.v")
vcd_path = os.path.join(sim_dir, "wave.vcd")
out_path = os.path.join(sim_dir, "sim.out")
log_path = os.path.join(sim_dir, "sim.log")

# Save HDL and testbench to files
with open(hdl_path, "w") as f:
    f.write(st.session_state.get("hdl_code_sim", ""))
with open(tb_path, "w") as f:
    f.write(st.session_state.get("tb_code_sim", ""))

sim_output = ""
compile_output = ""
vcd_exists = False

if st.button("Run Simulation"):
    with st.spinner("Running simulation..."):
        try:
            # Compile
            compile_cmd = ["iverilog", "-o", out_path, tb_path, hdl_path]
            compile_proc = subprocess.run(compile_cmd, capture_output=True, text=True)
            compile_output = compile_proc.stdout + compile_proc.stderr
            # Run
            run_cmd = ["vvp", out_path]
            run_proc = subprocess.run(run_cmd, capture_output=True, text=True)
            sim_output = run_proc.stdout + run_proc.stderr
            # Save log
            with open(log_path, "w") as f:
                f.write("=== Compile Output ===\n")
                f.write(compile_output)
                f.write("\n=== Simulation Output ===\n")
                f.write(sim_output)
            # Check for VCD file
            vcd_exists = os.path.exists(vcd_path)
            if vcd_exists:
                st.success("Simulation complete! Waveform (.vcd) generated.")
                st.download_button("Download Waveform (.vcd)", open(vcd_path, "rb").read(), file_name="wave.vcd")
                st.info("To view waveforms, open wave.vcd in GTKWave.")
            else:
                st.warning("Simulation ran, but no waveform (.vcd) generated. Make sure your testbench contains $dumpfile and $dumpvars statements.")
            # Show simulation log
            st.text_area("Simulation Log", value=sim_output, height=200)
            st.download_button("Download Full Log", open(log_path).read(), file_name="sim.log")
        except Exception as e:
            st.error(f"Simulation error: {e}")

# --- GenAI explanation of the simulation log ---
if st.button("Explain Simulation Results (GenAI)"):
    import ollama
    log_contents = open(log_path).read() if os.path.exists(log_path) else sim_output
    prompt = f"""
You are an expert digital IC verification engineer.
Given the following HDL code, testbench, and simulation log, explain the results, highlight any problems, and suggest fixes.

HDL Code:
{st.session_state.get("hdl_code_sim", "")}

Testbench Code:
{st.session_state.get("tb_code_sim", "")}

Simulation Log:
{log_contents}
"""
    with st.spinner("Analyzing..."):
        try:
            response = ollama.chat(
                model="mistral",
                messages=[{"role": "user", "content": prompt}]
            )
            st.markdown(response["message"]["content"])
        except Exception as e:
            st.error(f"GenAI explanation error: {e}")

st.write("---")
st.markdown("""
**Open Source Workflow:**  
- All simulation is local, using Icarus Verilog.  
- For waveform viewing, use [GTKWave](http://gtkwave.sourceforge.net/) to open the downloaded `.vcd` file.
""")
# Future upgrades:
## Add Verilator support (verilator --cc ... then run the C++ sim)
## Add web-based waveform viewer (e.g., WaveDrom)
## Move simulation to server/cloud for heavy workloads