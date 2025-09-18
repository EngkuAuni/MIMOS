# Simulates HDL Code with testbench using Icarus Verilog
# Automatically fixes compatibility issues in HDL code
# Shows simulation output and offers .vcd waveform download for GTKWave.

import streamlit as st
import subprocess
import os
import re
import tempfile
import shutil
from LLM_utils import call_llm

# --- UTILITY FUNCTIONS ---

def auto_fix_verilog_code(hdl_code, tb_code):
    """
    Automatically fixes common compatibility issues in Verilog testbenches
    for Icarus Verilog.
    """
    fixes_applied = []
    
    # Return early if testbench code is empty to prevent errors
    if not tb_code:
        return hdl_code, tb_code, fixes_applied
    
    # 0. Remove stray backticks (`) or markdown fences 
    tb_code = tb_code.replace('`', '')
    tb_code = re.sub(r"```(?:verilog)?", "", tb_code)

    # 1. Ensure waveform dump directives are present
    if '$dumpfile' not in tb_code:
        # Find a suitable module name from the testbench for $dumpvars
        module_match = re.search(r'module\s+(\w+)', tb_code)
        tb_module_name = module_match.group(1) if module_match else "testbench"

        dump_directives = f"""
initial begin
  $dumpfile("wave.vcd");
  $dumpvars(0, {tb_module_name});
end
"""
        # Add the initial block before the endmodule statement
        if 'endmodule' in tb_code:
            tb_code = tb_code.replace('endmodule', f'{dump_directives}\nendmodule')
        else:
            # As a fallback, append to the end
            tb_code += dump_directives
        fixes_applied.append("Added missing `$dumpfile` and `$dumpvars` directives at end of file.")

    # 2. Correct the path for the dumpfile to be in the current directory
    if '$dumpfile' in tb_code and 'wave.vcd' not in tb_code:
        old_tb_code = tb_code
        tb_code = re.sub(r'\$dumpfile\(".*?"\)', '$dumpfile("wave.vcd")', tb_code)
        if old_tb_code != tb_code:
            fixes_applied.append("Corrected `$dumpfile` path to `wave.vcd`.")

    # 3. Comment out unsupported $system calls
    if '$system' in tb_code:
        old_tb_code = tb_code
        tb_code = re.sub(r'(\$system\(.*?\);)', r'// \1 // Commented out: Not supported in Icarus Verilog', tb_code)
        if old_tb_code != tb_code:
            fixes_applied.append("Commented out unsupported `$system()` calls.")

    # 4. Update $dumpvars to use the correct testbench module name
    module_match = re.search(r'module\s+(\w+)', tb_code)
    if module_match:
        tb_module_name = module_match.group(1)
        tb_code = re.sub(r'\$dumpvars\(\s*\d+\s*,\s*\w+\s*\);', f'$dumpvars(0, {tb_module_name});', tb_code)

    return hdl_code, tb_code, fixes_applied


def detect_verilog_standard(hdl_code, tb_code):
    """
    Automatically detect which Verilog standard to use based on keywords.
    Defaults to -g2005 if no specific features are found.
    """
    combined_code = hdl_code + tb_code
    sv_features = [
        'logic ', 'interface ', 'always_comb', 'always_ff', 'always_latch',
        'enum ', 'typedef ', 'class ', 'package ', 'import ', 'assert '
    ]
    if any(feature in combined_code for feature in sv_features):
        return "System Verilog (-g2012)"
    return "Basic (-g2005)"


def parse_iverilog_errors(error_text):
    """
    Parse Icarus Verilog error messages and suggest human-readable fixes.
    """
    suggestions = []
    error_patterns = {
        r'syntax error': "Syntax error — check for missing semicolons or invalid Verilog keywords.",
        r'undefined module': "Undefined module — verify your module names match.",
        r'Program not runnable': "Linking issue — possibly unsupported constructs.",
        r'Implicit definition': "Implicit wire — declare signals explicitly.",
        r'Stray tic': "Stray backtick (`) — remove stray preprocessor symbols or markdown remnants.",
    }
    for pattern, message in error_patterns.items():
        if re.search(pattern, error_text) and message not in suggestions:
            suggestions.append(message)
    if not suggestions and error_text:
        suggestions.append("Unknown error — please check the full compile log.")
    return suggestions

# --- INITIALIZE SESSION STATE ---

# This is crucial for persisting data across reruns
if "simulation_run" not in st.session_state:
    st.session_state.simulation_run = False
if "compile_log" not in st.session_state:
    st.session_state.compile_log = ""
if "sim_log" not in st.session_state:
    st.session_state.sim_log = ""
if "vcd_data" not in st.session_state:
    st.session_state.vcd_data = None
if "hdl_code" not in st.session_state:
    st.session_state.hdl_code = ""
if "testbench_code" not in st.session_state:
    st.session_state.testbench_code = ""
if "explanation" not in st.session_state:
    st.session_state.explanation = ""
if "hdl_to_sim" not in st.session_state:
    st.session_state.hdl_to_sim = ""
if "tb_to_sim" not in st.session_state:
    st.session_state.tb_to_sim = ""
if "fixes" not in st.session_state:
    st.session_state.fixes = []

# Enhanced Explaination Prompt Template
EXPLAINATION_PROMPT_TEMPLATE = """
You are an expert FPGA/ASIC verfification and Integrated Circuit enginner analyzing simulation results. Provide a STRUCTURED analysis with these sections ONLY:

## Code Summary
- Brief description of the HDL module's purpose and functionality.
- Key features of the testbench verification appproach.

## Simulation Analysis
- {compile_status}
- {simulation_status}

## Detailed Findinggs
- {compile_findings}
- {simulation_findings}

## Recommendations
- Clear, actionable steps to fix any issues or improve the design

IMPORTANT RULES:
1. DO NOT include your thinking process
2. DO NOT use <think> tags or similar constructs
3. Focus ONLY on technical analysis and recommendations
4. BE CONCISE and SPECIFIC
5. If compilation failed, focus on syntax errors
6. If simulation ran but shows issues, focus on functional/logical errors
"""

# --- UI LAYOUT ---

st.set_page_config(page_title="HDL Simulation", layout="wide")
st.title("HDL Simulation .vcd")

st.markdown("""
**Simulate your HDL design using Icarus Verilog:**
- Code and testbench can be loaded from previous steps or uploaded directly.
- Download the waveform (`.vcd`) file for offline analysis with tools like GTKWave.
- Use the GenAI assistant to explain the simulation results and identify issues.
""")

# Use session state to pre-fill text areas
hdl_code_input = st.session_state.get("hdl_code", "")
tb_code_input = st.session_state.get("testbench_code", "")

tab1, tab2 = st.tabs(["Code from Previous Steps", "Upload Files"])
with tab1:
    st.session_state.hdl_code = st.text_area("HDL Code", value=hdl_code_input, height=200, key="hdl_code_sim_main")
    st.session_state.testbench_code = st.text_area("Testbench Code", value=tb_code_input, height=200, key="tb_code_sim_main")

with tab2:
    hdl_file = st.file_uploader("Upload HDL (.v) file", type=["v"])
    tb_file = st.file_uploader("Upload Testbench (.v) file", type=["v"])
    if hdl_file:
        hdl_code_from_upload = hdl_file.read().decode()
        st.session_state.hdl_code = hdl_code_from_upload
    if tb_file:
        tb_code_from_upload = tb_file.read().decode()
        st.session_state.testbench_code = tb_code_from_upload

# --- CODE FIXES (outside of temporary directory) ---

# Auto-apply fixes and store in session state for later
hdl_to_sim, tb_to_sim, fixes = auto_fix_verilog_code(
    st.session_state.hdl_code, st.session_state.testbench_code
)
st.session_state.hdl_to_sim = hdl_to_sim
st.session_state.tb_to_sim = tb_to_sim
st.session_state.fixes = fixes

if fixes:
    with st.expander("Automatic Compatibility Fixes Applied"):
        st.info("To improve compatibility with Icarus Verilog, the following fixes were applied to your testbench:")
        for fix in fixes:
            st.markdown(f"- {fix}")
        st.code(tb_to_sim, language="verilog")

# Simulation controls
recommended_standard = detect_verilog_standard(hdl_to_sim, tb_to_sim)
iverilog_options = st.multiselect(
    "Icarus Verilog Options",
    ["Basic (-g2005)", "System Verilog (-g2012)", "Verbose (-v)", "Warnings (-Wall)"],
    default=[recommended_standard, "Warnings (-Wall)"]
)

# Correctly process iverilog flags
iverilog_flags = []
if "Basic (-g2005)" in iverilog_options:
    iverilog_flags.append("-g2005")
if "System Verilog (-g2012)" in iverilog_options:
    iverilog_flags.append("-g2012")
if "Verbose (-v)" in iverilog_options:
    iverilog_flags.append("-v")
if "Warnings (-Wall)" in iverilog_options:
    iverilog_flags.append("-Wall")

if st.button("Run Simulation", type="primary"):
    # Reset state for a new run
    st.session_state.simulation_run = True
    st.session_state.compile_log = ""
    st.session_state.sim_log = ""
    st.session_state.vcd_data = None
    st.session_state.explanation = ""

    if not st.session_state.hdl_to_sim or not st.session_state.tb_to_sim:
        st.error("Both HDL code and testbench code are required to run the simulation.")
        st.stop()

    # Create a temporary directory for simulation
    with tempfile.TemporaryDirectory() as sim_dir:
        hdl_path = os.path.join(sim_dir, "module.v")
        tb_path = os.path.join(sim_dir, "testbench.v")
        vcd_path = os.path.join(sim_dir, "wave.vcd")
        out_path = os.path.join(sim_dir, "sim.out")

        # Write the (potentially fixed) code to the temp files
        with open(hdl_path, "w") as f:
            f.write(st.session_state.hdl_to_sim)
        with open(tb_path, "w") as f:
            f.write(st.session_state.tb_to_sim)

        with st.spinner("Compiling and running simulation..."):
            try:
                # 1. Compile the code (only once)
                compile_cmd = ["iverilog"] + iverilog_flags + ["-o", out_path, tb_path, hdl_path]
                compile_proc = subprocess.run(compile_cmd, capture_output=True, text=True)
                st.session_state.compile_log = compile_proc.stdout + compile_proc.stderr

                # 2. Check for compilation errors
                if compile_proc.returncode != 0:
                    st.error("Compilation Failed!")
                else:
                    # 3. Run the simulation
                    run_cmd = ["vvp", out_path]
                    run_proc = subprocess.run(run_cmd, capture_output=True, text=True)
                    st.session_state.sim_log = run_proc.stdout + run_proc.stderr

                    # 4. Check for and read the VCD file
                    if os.path.exists(vcd_path):
                        persistent_path = os.path.join(os.getcwd(), "wave.vcd")
                        shutil.copy(vcd_path, persistent_path)

                        with open(persistent_path, "rb") as f:
                            st.session_state.vcd_data = f.read()

                        st.session_state.vcd_file_path = persistent_path
                        if not st.session_state.vcd_data:
                            st.info("No `.vcd` file was found. Ensure your testbench includes both `$dumpfile(\"wave.vcd\")` and `$dumpvars(...)` directives.")
                    else:
                        # Fallback: Search for any .vcd file in temp dir
                        for file in os.listdir(sim_dir):
                            if file.endswith(".vcd"):
                                fallback_vcd_path = os.path.join(sim_dir, file)

                                # Copy to persistent path
                                persistent_path = os.path.join(os.getcwd(), "wave.vcd")
                                shutil.copy(fallback_vcd_path, persistent_path)

                                with open(persistent_path, "rb") as f:
                                    st.session_state.vcd_data = f.read()

                                st.session_state.vcd_file_path = persistent_path
                                break
            except Exception as e:
                st.error(f"Simulation error: {e}")
                st.session_state.compile_log = f"ERROR: {str(e)}"

# --- DISPLAY RESULTS (conditionally, based on session state) ---

if st.session_state.simulation_run:
    st.divider()
    st.subheader("Simulation Results")

    # Display Compile Log
    with st.expander("Compile Log", expanded=bool(st.session_state.compile_log)):
        st.text_area("Compile Log", value=st.session_state.compile_log, height=150, key="compile_log_display", disabled=True)
        suggestions = parse_iverilog_errors(st.session_state.compile_log)
        if suggestions:
            st.warning("Compilation issues detected. Here are some suggestions:")
            for s in suggestions:
                st.markdown(f"- {s}")

    # Display Simulation Log
    with st.expander("Simulation Log", expanded=bool(st.session_state.sim_log)):
        st.text_area("Simulation Log", value=st.session_state.sim_log, height=150, key="sim_log_display", disabled=True)

    # Display VCD download and info
    if st.session_state.vcd_data and "vcd_file_path" in st.session_state:
        st.success("✅ Simulation completed and waveform file (`wave.vcd`) was generated.")
        vcd_size_kb = len(st.session_state.vcd_data) / 1024
        st.info(f"VCD file size: {vcd_size_kb:.2f} KB")

        with open(st.session_state.vcd_file_path, "rb") as f:
            st.download_button(
                label="⬇️ Download Waveform (.vcd)",
                data=f,
                file_name="wave.vcd",
                mime="application/octet-stream"
            )
    elif st.session_state.compile_log and not any(s for s in parse_iverilog_errors(st.session_state.compile_log)):
        st.warning("⚠️ Simulation ran, but no waveform file was generated. Check your testbench for correct `$dumpfile` and `$dumpvars` statements.")

# --- GenAI EXPLANATION SECTION ---
st.divider()
if st.button("🤖 Explain Simulation Results"):
    if not st.session_state.compile_log and not st.session_state.sim_log:
        st.warning("There are no simulation results to explain. Please run the simulation first.")
    else:
        try:
            with st.spinner("Generating explanation..."):
                # Determine status and findings based on logs
                compile_status = "Compilation Successful" if "Compilation failed" not in st.session_state.compile_log else "Compilation Failed"
                simulation_status = "Simulation Completed" if st.session_state.sim_log else "Simulation Not Run"
                
                # Extract key findings
                compile_findings = "No compilation issues detected" if "Compilation failed" not in st.session_state.compile_log else "Syntax errors detected in code"
                simulation_findings = "Review simulation output for functional behavior" if st.session_state.sim_log else "No simulation data available"
                
                prompt = EXPLAINATION_PROMPT_TEMPLATE.format(
                    compile_status=compile_status,
                    simulation_status=simulation_status,
                    compile_findings=compile_findings,
                    simulation_findings=simulation_findings
                )
                
                prompt += f"""
**HDL Code:**
```verilog
{st.session_state.hdl_code}
{st.session_state.testbench_code}
{st.session_state.compile_log if st.session_state.compile_log.strip() else "No compilation output."}
{st.session_state.sim_log if st.session_state.sim_log.strip() else "No simulation output."}
"""
                response = call_llm(prompt, model="deepseek-r1-distill-llama-70b")
                st.session_state.explanation = response

        except ImportError:
            st.error("Error importing the LLM utilities. Make sure your LLM_utils.py file is set up correctly.")
        except Exception as e:
            st.error(f"An error occurred while contacting the model {e}")

    if st.session_state.explanation:
        st.markdown(st.session_state.explanation)

#This section:
##Creates a divider in the UI
##Adds an "Explain Simulation Results" button
##When clicked, checks if there are simulation results to explain
##If results exist, sends the HDL code, testbench, and logs to the LLM
##Uses the deepseek-r1-distill-llama-70b model for generating the explanation
##Displays the explanation in the UI
##Includes error handling for import issues or API failures