# HDL Code Generator
# Input HDL task --> Generate Verilog code
# Display HDL code & testbench option
# .vcd generation option for tb 
# Download options

import streamlit as st
import ollama
import re

def strip_code_fences(code):
    """
    Remove any ``` or ```verilog code fences from LLM output
    """
    return re.sub(r"```(?:verilog)?\n?", "", code).replace("```", "").strip()

def fix_pythonic_for_loops(code):
    """
    Rewrites Python-style 'for i in range(n)' to Verilog 'for (i = 0; i < n; i++)'
    """
    pattern = r"for\s+(\w+)\s+in\s+range\((\d+)\)"
    def repl(match):
        var = match.group(1)
        limit = match.group(2)
        return f"integer {var}; for ({var} = 0; {var} < {limit}; {var} = {var} + 1)"
    return re.sub(pattern, repl, code)

# Few-shot prompt templates (improve generation accuracy)

HDL_PROMPT_TEMPLATE = """
You are an expert Verilog design engineer. Your task is to generate **only valid, synthesizable Verilog code** — no markdown, no commentary. Follow these strict rules:

- Start with `module` and end with `endmodule`
- All ports must have widths (e.g., `input clk`, `output [7:0] data`)
- Use `always @(posedge clk)` for sequential logic
- Use `<=` for non-blocking assignments
- Use `=` only for combinational assignments
- Declare all `reg` variables outside `always` blocks
- Never use real numbers like `50e6` — write full integers (e.g., `50000000`)
- Avoid Python-style loops like `for i in range(...)` — use Verilog `for (i = 0; i < n; i++)`
"""

TB_PROMPT_TEMPLATE = """
You are an expert Verilog testbench engineer. Output a valid synthesizable Verilog testbench that:

- Instantiates the given module
- Generates a clock using an always block
- Stimulates the inputs clearly
- Includes $dumpfile("sim_files/wave.vcd"); $dumpvars; and $finish
- Uses **no markdown or commentary** — just plain Verilog code.

MODULE TO TEST:
{hdl_code}

FEW-SHOT TESTBENCH:
module counter_tb;
  reg clk = 0;
  reg rst;
  reg en;
  wire [3:0] count;
  counter uut(.clk(clk), .rst(rst), .en(en), .count(count));
  always #5 clk = ~clk;
  initial begin
    $dumpfile("sim_files/wave.vcd");
    $dumpvars;
    rst = 1; en = 0;
    #12 rst = 0; en = 1;
    #200 $finish;
  end
endmodule
"""

def generate_hdl_code(spec, model="mistral"):
    prompt = HDL_PROMPT_TEMPLATE.format(spec=spec)
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "user", "content": prompt}]
    )
    raw_code = response["message"]["content"]
    return strip_code_fences(raw_code)

def generate_testbench(hdl_code, model="mistral"):
    prompt = TB_PROMPT_TEMPLATE.format(hdl_code=hdl_code)
    response = ollama.chat(
        model=model,
        messages=[
            {"role": "user", "content": prompt}]
    )
    raw_code = response["message"]["content"]
    cleaned_code = strip_code_fences(raw_code)
    fixed_code = fix_pythonic_for_loops(cleaned_code)
    return fixed_code

st.set_page_config(page_title="HDL Generator", layout="wide")
st.title("HDL Code Generator")
st.markdown("Generate HDL code from your specification (auto-filled from previous step). You may edit if needed.")

# VCD toggle UI
vcd_toggle = st.checkbox("Generate waveform file for simulation (`wave.vcd`)", value=True)

# Pre-fill with spec from Specification page if available
if "specification" in st.session_state:
    spec = st.session_state["specification"]
    default_spec = f"Module name: {spec.get('module_name','')}\nDescription: {spec.get('description','')}\nInputs: {spec.get('inputs','')}\nOutputs: {spec.get('outputs','')}\nConstraints: {spec.get('constraints','')}\nNotes: {spec.get('notes','')}"
    spec_input = st.text_area("module Specification", value=default_spec, height=150)
    mod_name = st.text_input("Optional: Module name for simulation scope / waveform dumpvars", value = "uut")
    st.session_state["module_name"] = mod_name 
else:
    st.info("No specification found. See examples below or enter manually or go to Specification page.")
    example_specs = {
        "4-bit Counter": "Create a synchronous 4-bit up counter with reset and clock inputs.",
        "D Flip-Flop": "Generate a D flip-flop module with asynchronous reset.",
        "SPI Master": "Create an SPI master module with clock divider and 4 SPI modes."
    }
    selected_example = st.selectbox("Examples", ['-- Select --'] + list(example_specs.keys()))
    if selected_example != "-- Select --":
        spec_input = st.text_area("Enter module specification:", value=example_specs[selected_example], height=150)
    else:
        spec_input = st.text_area("Enter module specification:", height=150)


# State session variables for code persistence
if "hdl_code" not in st.session_state:
    st.session_state["hdl_code"] = ""
if "testbench_code" not in st.session_state:
    st.session_state["testbench_code"] = ""
if "generate_tb" not in st.session_state:
    st.session_state["generate_tb"] = False

if st.button("Generate HDL Code") and spec_input:
    with st.spinner("Generating..."):
        try:
            spec_input_clean = spec_input.replace("\n", ", ").strip()
            hdl_raw = generate_hdl_code(spec_input_clean)

            # Check if HDL starts with module and ends with endmodule
            is_hdl_valid = hdl_raw.strip().lower().startswith("module") and "endmodule" in hdl_raw
            if not is_hdl_valid:
                st.warning("⚠️ Generated HDL code might be malformed or missing `module`/`endmodule`.")

            st.session_state["hdl_code"] = hdl_raw
            st.session_state["testbench_code"] = ""  # Reset testbench
            st.session_state["generate_tb"] = False
        except Exception as e:
            st.error(f"Error generating HDL code: {e}")

hdl_code = st.session_state["hdl_code"]
testbench_code = st.session_state["testbench_code"]

if hdl_code:
    
# HDL Syntax Validator
    def is_verilog_valid(code):
        issues = []
        if 'let ' in code:
            issues.append("⚠️ Uses invalid keyword `let` (Verilog does not support this).")
        if re.search(r'for\s+\w+\s+in\s+range', code):
            issues.append("⚠️ Uses Python-style `for` loop (not valid Verilog).")
        if re.search(r'\d+\.\d+|\de[+-]?\d+', code):
            issues.append("⚠️ Contains floating-point numbers (Verilog requires integers).")
        if not code.strip().lower().startswith("module"):
            issues.append("⚠️ HDL does not start with `module`.")
        if "endmodule" not in code:
            issues.append("⚠️ HDL missing `endmodule`.")
        return issues

# Editable HDL Area
    st.success("Generated HDL Code (editable):")
    editable_hdl_code = st.text_area("Edit HDL Code (fix syntax if needed)", value=hdl_code, height=250, key="hdl_edit")

# Run validation on edited HDL
    validation_issues = is_verilog_valid(editable_hdl_code)
    if validation_issues:
        st.warning("⚠️ HDL Validation Issues Detected:")
        for issue in validation_issues:
            st.markdown(f"- {issue}")
        if st.button("Regenerate HDL Code"):
            st.session_state["generate_tb"] = False
            st.session_state["hdl_code"] = ""
            st.rerun()
        st.stop()  # Stop testbench generation

# Allow user to confirm and proceed
    if st.button("Generate Testbench from Edited HDL"):
        st.session_state["hdl_code"] = editable_hdl_code
        st.session_state["generate_tb"] = True
        st.rerun()

# This block runs after the button is pressed, in the next rerun
if st.session_state["generate_tb"] and not testbench_code and hdl_code:
    fallback_tb_code = """
module dummy_tb;
    reg clk;
    initial begin
        clk = 0;
        #100 $finish;
    end
    always #5 clk = ~clk;

    initial begin
        $dumpfile("sim_files/wave.vcd");
        $dumpvars;
    end
endmodule
    """

    with st.spinner("Generating Testbench..."):
        try:
            raw_tb_code = generate_testbench(hdl_code)

            # Always show what the model returned
            st.expander("Raw Testbench Output (before fix)").write(raw_tb_code)

            # Initialize validity flag
            is_valid = True

            # Check for basic structure
            if not raw_tb_code.strip().lower().startswith("module") or "endmodule" not in raw_tb_code:
                is_valid = False

            # Check for presence of simulation logic
            if not re.search(r'\b(initial|always)\b', raw_tb_code):
                is_valid = False

            # Handle fallback if invalid
            if not is_valid:
                st.warning("Generated testbench is malformed or incomplete.")
                use_fallback = st.checkbox("Use fallback dummy testbench instead?")
                if use_fallback:
                    raw_tb_code = fallback_tb_code
                    is_valid = True
                else:
                    if st.button("Regenerate Testbench"):
                        st.session_state["generate_tb"] = True
                        st.rerun()
                    st.stop()

            ## VCD Injection logic
            if vcd_toggle:
                mod_name = st.session_state.get("module_name", "uut")
                vcd_block = f"""
initial begin
    $dumpfile("sim_files/wave.vcd");
    $dumpvars(0, {mod_name});
end
"""
                if "endmodule" in raw_tb_code:
                    testbench_code = re.sub(r'endmodule\b', vcd_block + "\nendmodule", raw_tb_code, flags=re.MULTILINE)
                else:
                    testbench_code = raw_tb_code + "\n" + vcd_block
            else:
                testbench_code = raw_tb_code

            # Save the testbench
            st.session_state["testbench_code"] = testbench_code
            st.session_state["generate_tb"] = False  # Reset after generation

        except Exception as e:
            st.error(f"Error generating testbench: {e}")

testbench_code = st.session_state["testbench_code"]

if testbench_code:
    st.success("Generated Testbench:")
    st.code(testbench_code, language="verilog")
    st.download_button("Download Testbench", data=testbench_code, file_name="testbench.v")
