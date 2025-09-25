# Simulates HDL Code with testbench using Icarus Verilog
# Automatically fixes compatibility issues in HDL code
# Shows simulation output and offers .vcd waveform download for GTKWave.

import streamlit as st
import subprocess
import os
import re
import tempfile
import shutil

# Set fixed model
MODEL = "mistral"

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

# Comprehensive fixer function for all common issues
def auto_fix_verilog_code(hdl_code, tb_code):
    """Automatically fix common issues in Verilog code"""
    fixes_applied = []
    
    # Fix HDL code issues (less likely to have simulator-specific code)
    
    # Fix testbench code issues (more likely to have simulator-specific code)
    # 1. Fix missing waveform directives
    if '$dumpfile' not in tb_code:
        # Add dumpfile directive if missing
        if 'initial begin' in tb_code:
            tb_code = re.sub(
                r'(initial\s+begin)',
                r'\1\n    $dumpfile("sim_files/wave.vcd");\n    $dumpvars(0, simple_counter_tb);',
                tb_code
            )
            fixes_applied.append("Added missing waveform dump directives")
        else:
            # If no initial block, add one
            insert_point = tb_code.find('endmodule')
            if insert_point != -1:
                tb_code = tb_code[:insert_point] + '\n  initial begin\n    $dumpfile("sim_files/wave.vcd");\n    $dumpvars(0, simple_counter_tb);\n  end\n' + tb_code[insert_point:]
                fixes_applied.append("Added initial block with waveform dump directives")
    
    # 2. Fix path issues in waveform directives
    if '$dumpfile' in tb_code and 'sim_files/wave.vcd' not in tb_code:
        old_tb_code = tb_code
        tb_code = re.sub(r'\$dumpfile\("([^"]+)"\)', r'$dumpfile("sim_files/wave.vcd")', tb_code)
        if old_tb_code != tb_code:
            fixes_applied.append("Fixed path in $dumpfile directive")
    
    # 3. Fix $system() calls
    if '$system' in tb_code:
        old_tb_code = tb_code
        tb_code = re.sub(r'\$system\([^)]*\);', '// $system call removed (not supported in Icarus Verilog)', tb_code)
        if old_tb_code != tb_code:
            fixes_applied.append("Removed $system() calls (not supported in Icarus Verilog)")
    
    # 4. Fix force/release on array elements
    if re.search(r'force\s+\w+\.\w+\[\d+\]', tb_code):
        old_tb_code = tb_code
        tb_code = re.sub(r'(force\s+\w+\.\w+\[\d+\].*?;)', r'// \1 // Commented out (not supported in Icarus Verilog)', tb_code)
        if old_tb_code != tb_code:
            fixes_applied.append("Commented out 'force' commands on array elements (not supported in Icarus Verilog)")
    
    if re.search(r'release\s+\w+\.\w+\[\d+\]', tb_code):
        old_tb_code = tb_code
        tb_code = re.sub(r'(release\s+\w+\.\w+\[\d+\].*?;)', r'// \1 // Commented out (not supported in Icarus Verilog)', tb_code)
        if old_tb_code != tb_code:
            fixes_applied.append("Commented out 'release' commands on array elements (not supported in Icarus Verilog)")
    
    # 5. Fix top-level module name in $dumpvars if module name doesn't match filename
    if '$dumpvars' in tb_code:
        # Extract the module name from the testbench
        module_match = re.search(r'module\s+(\w+)', tb_code)
        if module_match:
            module_name = module_match.group(1)
            # Replace generic module names with the actual testbench module name
            if 'uut' in tb_code and f'$dumpvars(0, {module_name})' not in tb_code:
                tb_code = re.sub(r'\$dumpvars\(0,\s*uut\)', f'$dumpvars(0, {module_name})', tb_code)
                fixes_applied.append(f"Updated $dumpvars to use module name: {module_name}")
    
    return hdl_code, tb_code, fixes_applied

# Determine the best Verilog standard based on code content
def detect_verilog_standard(hdl_code, tb_code):
    """Automatically detect which Verilog standard to use"""
    combined_code = hdl_code + tb_code
    
    # Check for SystemVerilog features
    sv_features = [
        r'logic\s+',         # logic type
        r'interface\s+',     # interfaces
        r'always_comb',      # always_comb
        r'always_ff',        # always_ff
        r'always_latch',     # always_latch
        r'enum\s+',          # enums
        r'typedef\s+',       # typedefs
        r'class\s+',         # classes
        r'package\s+',       # packages
        r'import\s+',        # imports
        r'assert\s+'         # assertions
    ]
    
    for feature in sv_features:
        if re.search(feature, combined_code):
            return "System Verilog (-g2012)"
    
    # Check for Verilog-2005 features (not in Verilog-2001)
    v2005_features = [
        r'generate.*?endgenerate',  # generate blocks
        r'genvar\s+',               # genvars
        r'localparam\s+',           # localparams
        r'\{\{',                    # concatenation in concatenation
    ]
    
    for feature in v2005_features:
        if re.search(feature, combined_code):
            return "Basic (-g2005)"
    
    # Default to Verilog-2005
    return "Basic (-g2005)"

# Setup directories with more robust error handling
sim_dir = "sim_files"
try:
    os.makedirs(sim_dir, exist_ok=True)
except Exception as e:
    st.warning(f"Warning: Could not create directory {sim_dir}: {e}")
    # Use temp directory as fallback
    sim_dir = tempfile.mkdtemp()
    st.info(f"Using temporary directory: {sim_dir}")

# Create backup directory for original code
backup_dir = os.path.join(sim_dir, "backup")
os.makedirs(backup_dir, exist_ok=True)

hdl_path = os.path.join(sim_dir, "module.v")
tb_path = os.path.join(sim_dir, "testbench.v")
hdl_backup_path = os.path.join(backup_dir, "module_original.v")
tb_backup_path = os.path.join(backup_dir, "testbench_original.v")
vcd_path = os.path.join(sim_dir, "wave.vcd")
out_path = os.path.join(sim_dir, "sim.out")
log_path = os.path.join(sim_dir, "sim.log")

# Debug info 
with st.expander("Debug Information"):
    st.write(f"Working directory: {os.getcwd()}")
    st.write(f"Simulation directory: {sim_dir}")
    st.write(f"Backup directory: {backup_dir}")
    st.write(f"HDL path: {hdl_path}")
    st.write(f"Testbench path: {tb_path}")
    st.write(f"VCD path: {vcd_path}")
    st.write(f"Output path: {out_path}")

# Get updated code from session state
hdl_code_sim = st.session_state.get("hdl_code_sim", "")
tb_code_sim = st.session_state.get("tb_code_sim", "")

# Automatically apply fixes
fixed_hdl, fixed_tb, fixes_applied = auto_fix_verilog_code(hdl_code_sim, tb_code_sim)

# Save original code for reference
with open(hdl_backup_path, "w") as f:
    f.write(hdl_code_sim)
with open(tb_backup_path, "w") as f:
    f.write(tb_code_sim)

# Show applied fixes if any
if fixes_applied:
    with st.expander("Automatic Compatibility Fixes Applied"):
        st.info("The following compatibility fixes were automatically applied:")
        for fix in fixes_applied:
            st.markdown(f"- {fix}")
        
        # Offer option to see fixed code
        st.markdown("### Fixed Testbench Code:")
        st.code(fixed_tb, language="verilog")

# Save fixed code to files
try:
    with open(hdl_path, "w") as f:
        f.write(fixed_hdl)
    with open(tb_path, "w") as f:
        f.write(fixed_tb)
except Exception as e:
    st.error(f"Error saving files: {e}")

sim_output = ""
compile_output = ""
vcd_exists = False

# Auto-detect best Verilog standard
recommended_standard = detect_verilog_standard(hdl_code_sim, tb_code_sim)

# Add compilation options with smart defaults
iverilog_options = st.multiselect(
    "Iverilog Options", 
    ["Basic (-g2005)", "System Verilog (-g2012)", "Verbose (-v)", "Warnings (-Wall)"],
    default=[recommended_standard, "Warnings (-Wall)"]
)

# Get iverilog flags from options
iverilog_flags = []
if "Basic (-g2005)" in iverilog_options:
    iverilog_flags.append("-g2005")
if "System Verilog (-g2012)" in iverilog_options:
    iverilog_flags.append("-g2012")
if "Verbose (-v)" in iverilog_options:
    iverilog_flags.append("-v")
if "Warnings (-Wall)" in iverilog_options:
    iverilog_flags.append("-Wall")

# Function to parse errors and suggest specific fixes
def parse_iverilog_errors(error_text):
    """Parse Icarus Verilog error messages and suggest fixes"""
    error_patterns = {
        r'cannot %force/vec4': "Remove or comment out force/release statements on array elements",
        r'System task/function \$system\(\)': "Remove $system() calls, they're not supported in Icarus Verilog",
        r'near \"initial\": syntax error': "Check initial block syntax, there might be a missing semicolon",
        r'error: malformed statement': "Check for syntax errors like missing semicolons or brackets",
        r'syntax error': "Syntax error in Verilog code - check for typos or missing punctuation",
        r'undefined module': "Module not found - check if the module name matches in both files",
        r'error: Unable to bind wire/reg/memory': "Port connection error - check port names and connections",
        r'error: Input is not connected': "Missing connection to an input port",
        r'Program not runnable': "Compilation succeeded but there were errors in the final linking step"
    }
    
    suggestions = []
    for pattern, suggestion in error_patterns.items():
        if re.search(pattern, error_text):
            suggestions.append(suggestion)
    
    return suggestions

if st.button("Run Simulation"):
    with st.spinner("Running simulation..."):
        try:
            # Clean old .vcd
            if os.path.exists(vcd_path):
                try:
                    os.remove(vcd_path)
                except Exception as e:
                    st.warning(f"Could not remove old VCD file: {e}")
            
            # Ensure we have code to compile
            if not fixed_hdl or not fixed_tb:
                st.error("Both HDL code and testbench are required.")
                st.stop()
            
            # Show what we're about to compile
            st.info(f"Compiling files with Icarus Verilog...")
            
            # Compile HDL and testbench with additional options
            compile_cmd = ["iverilog"] + iverilog_flags + ["-o", out_path, tb_path, hdl_path]
            st.code(" ".join(compile_cmd), language="bash")
            
            compile_proc = subprocess.run(compile_cmd, capture_output=True, text=True)
            compile_output = compile_proc.stdout + compile_proc.stderr
            
            # Show compile log
            st.text_area("Compile Log", value=compile_output, height=70)
           
            # If compilation failed, provide specific help
            if not os.path.exists(out_path):
                st.error("Compilation failed. See suggestions below.")
                
                # Offer specific suggestions based on error patterns
                suggestions = parse_iverilog_errors(compile_output)
                if suggestions:
                    st.markdown("### Suggested Fixes:")
                    for suggestion in suggestions:
                        st.markdown(f"- {suggestion}")
                    
                    # Offer to edit the testbench directly
                    with st.expander("Need More Help?"):
                        st.markdown("""
                        Try these common solutions:
                        
                        1. **Use the Simple Counter Example** (below) to verify your environment
                        2. **Try System Verilog mode** if you're using advanced features
                        3. **Simplify your testbench** - remove complex features like force/release
                        4. **Check module instantiation** - make sure the instance name matches what's in $dumpvars
                        """)
                st.stop()
                
            # Run simulation
            st.info("Running simulation...")
            run_cmd = ["vvp", out_path]
            run_proc = subprocess.run(run_cmd, capture_output=True, text=True)
            sim_output = run_proc.stdout + run_proc.stderr

            # Save log
            with open(log_path, "w") as f:
                f.write("=== Compile Output ===\n")
                f.write(compile_output)
                f.write("\n=== Simulation Output ===\n")
                f.write(sim_output)
            
            # Show simulation output
            st.text_area("Simulation Log", value=sim_output, height=200)
           
            # Check for VCD file
            vcd_exists = os.path.exists(vcd_path)
            if vcd_exists:
                st.success("Simulation complete! Waveform (.vcd) generated.")
                # Get file size for information
                vcd_size = os.path.getsize(vcd_path)
                st.info(f"VCD file size: {vcd_size/1024:.2f} KB")
                
                # Offer download
                with open(vcd_path, "rb") as f:
                    vcd_data = f.read()
                    st.download_button("Download Waveform (.vcd)", vcd_data, file_name="wave.vcd")
                
                st.info("To view waveforms, open wave.vcd in GTKWave.")
            else:
                # Check if simulation actually ran but no VCD was generated
                if "Simulation complete" in sim_output or "$finish" in sim_output:
                    st.warning("Simulation ran but no waveform (.vcd) was generated.")
                    
                    # Try to figure out why
                    if "$dumpfile" not in fixed_tb:
                        st.error("Missing $dumpfile directive in the testbench even after fixes.")
                    elif "$dumpvars" not in fixed_tb:
                        st.error("Missing $dumpvars directive in the testbench even after fixes.")
                    else:
                        module_match = re.search(r'module\s+(\w+)', fixed_tb)
                        if module_match:
                            module_name = module_match.group(1)
                            st.markdown(f"""
                            Try manually adding these lines to your testbench's initial block:
                            ```verilog
                            $dumpfile("sim_files/wave.vcd");
                            $dumpvars(0, {module_name});
                            ```
                            """)
                else:
                    # Simulation might have failed during runtime
                    st.error("Simulation may have failed during runtime.")
                    
                    # Check for common runtime errors
                    if "Program not runnable" in sim_output:
                        st.markdown("Simulation executable could not be run properly.")
                    elif "ERROR:" in sim_output:
                        error_match = re.search(r'ERROR:(.*?)(?:\n|$)', sim_output)
                        if error_match:
                            st.markdown(f"**Simulation error:** {error_match.group(1).strip()}")
                
            # Always offer log download
            with open(log_path, "r") as f:
                log_data = f.read()
                st.download_button("Download Full Log", log_data, file_name="sim.log")
        
        except Exception as e:
            st.error(f"Simulation error: {e}")

# --- GenAI explanation of the simulation log ---
if st.button("Explain Simulation Results"):
    import ollama
    
    # Check if log exists, otherwise use session output
    if os.path.exists(log_path):
        with open(log_path, "r") as f:
            log_contents = f.read()
    else:
        log_contents = sim_output if sim_output else "No simulation results available."
    
    prompt = f"""
You are an expert digital IC verification engineer.
Given the following HDL code, testbench, and simulation log, please:

1. Summarize what the code is supposed to do
2. Explain what happened during simulation
3. Identify any errors or issues in the compilation or simulation
4. Suggest specific fixes for any problems found
5. If the simulation was successful, explain the key results

HDL Code:
```verilog
{fixed_hdl}
    ```
    """