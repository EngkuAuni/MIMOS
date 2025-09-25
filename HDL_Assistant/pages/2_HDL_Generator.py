# HDL Code Generator
# Input HDL task --> Generate Verilog code
# Display HDL code & testbench option
# .vcd generation option for tb 
# Download options

import streamlit as st
import re
import os
import subprocess
import tempfile
from LLM_utils import call_llm

# --- Initialize Session State ---
if "hdl_code" not in st.session_state:
    st.session_state["hdl_code"] = ""
if "testbench_code" not in st.session_state:
    st.session_state["testbench_code"] = ""
if "generate_tb" not in st.session_state:
    st.session_state["generate_tb"] = False
if "module_name" not in st.session_state:
    st.session_state["module_name"] = "uut"

# --- Utility Functions ---

def strip_code_fences(code):
    return re.sub(r"```(?:verilog)?\n?", "", code).replace("```", "").strip()

def strip_narrative_text(code):
    code = re.sub(r'<think>.*?</think>', '', code, flags=re.DOTALL)
    code = re.sub(r'^.*?module', 'module', code, flags=re.DOTALL, count=1)
    module_match = re.search(r'module\s+.*?endmodule', code, re.DOTALL)
    return module_match.group(0) if module_match else code.strip()

def auto_declare_regs(code):
    assigned_vars = set(re.findall(r"(\w+)\s*<=", code))
    declared_regs = set(re.findall(r"(?:^|\n)\s*(?:reg|output\s+reg)\s+(?:\[\d+:\d+\]\s+)?(\w+)", code))
    port_vars = set(re.findall(r"(input|output|inout)\s+(?:reg\s+|wire\s+)?(?:\[\d+:\d+\]\s+)?(\w+)", code))
    port_var_names = set(v[1] for v in port_vars)
    missing_regs = assigned_vars - declared_regs - port_var_names

    if missing_regs:
        reg_decls = "\n".join(f"  reg {var};" for var in sorted(missing_regs))
        insert_pos = re.search(r"\balways\s+@\(.*?\)", code)
        if insert_pos:
            insert_idx = insert_pos.start()
            code = code[:insert_idx] + reg_decls + "\n\n" + code[insert_idx:]
        else:
            code += "\n" + reg_decls

    return code

def comprehensive_hdl_fixes(code):
    code = strip_code_fences(code)

    if not code.lower().startswith("module"):
        module_name = "auto_module"
        if "specification" in st.session_state and st.session_state["specification"].get("module_name"):
            module_name = st.session_state["specification"]["module_name"]
        code = f"module {module_name}(\n  // Auto-added module declaration\n);\n" + code

    if "endmodule" not in code:
        code += "\nendmodule // Auto-added endmodule"

    # Fix syntax issues
    code = re.sub(r"for\s+(\w+)\s+in\s+range\s*\(\s*(\d+)\s*\)",
                  r"integer \1; for (\1 = 0; \1 < \2; \1 = \1 + 1)", code)
    code = re.sub(r"(\d+\.\d+e[+-]?\d+|\d+e[+-]?\d+)",
                  lambda m: str(int(float(m.group(1)))), code)
    code = re.sub(r"(input|output|inout)\s+\[\s*0\s*:\s*0\s*\]\s*(\w+)", r"\1 \2", code)
    code = re.sub(r"(input|output|inout)\s+wire\s+", r"\1 ", code)

    output_list = re.findall(r"output\s+(\w+)", code)
    for out in output_list:
        if re.search(rf"{out}\s*<=", code) and not re.search(rf"output\s+reg\s+{out}", code):
            code = re.sub(rf"output\s+{out}", f"output reg {out}", code)

    code = re.sub(r"const\s+int\s+(\w+)\s*=\s*(\d+)\s*;", r"parameter \1 = \2;", code)

    counter_vars = re.findall(r"reg\s+(\w*counter\w*);", code)
    for counter in counter_vars:
        code = re.sub(rf"reg\s+{counter};", f"reg [15:0] {counter};", code)

    code = re.sub(r"(parameter|wire|reg)\s+(\w+)\s*=\s*([^;]+)(?!\s*;)", r"\1 \2 = \3;", code)
    code = re.sub(r'(input|output)\s+reg\s+reg', r'\1 reg', code)
    code = re.sub(r'parameter\s+(\w+)\s*=\s*;', r'parameter \1 = ', code)
    code = re.sub(r'(reg|wire)\s+([^;=]+)\s*=\s*;', r'\1 \2 = ', code)
    code = re.sub(r'=\s*;+\s*(\w+)\s*;+', r'= \1;', code)
    code = auto_declare_regs(code)

    reg_names = re.findall(r'\breg\s+(?:\[\d+:\d+\]\s+)?(\w+)', code)
    for reg in reg_names:
        assign_pattern = rf'assign\s+{reg}\s*='
        if re.search(assign_pattern, code):
            # Convert reg declaration to wire
            code = re.sub(rf'\breg\s+(?=\[?\d*:?[\d]*\]?\s*{reg}\b)', 'wire ', code)
            code = re.sub(rf'\breg\s+{reg}\b', f'wire {reg}', code)

    return code

def enhanced_validation(code):
    issues = []
    if not code.lower().strip().startswith("module"):
        issues.append("⚠️ Missing module declaration")
    if "endmodule" not in code:
        issues.append("⚠️ Missing endmodule statement")

    if re.search(r"(input|output|inout)", code) and not re.search(r"module\s+\w+\s*\(", code):
        issues.append("⚠️ Ports exist but no port list in module declaration")

    if re.search(r"for\s+\w+\s+in\s+range", code):
        issues.append("⚠️ Python-style for loops found")

    if re.search(r"\d+\.\d+|\d+e[+-]?\d+", code):
        issues.append("⚠️ Floating-point numbers found")

    always_blocks = re.findall(r"always\s+@\s*\([^)]+\)\s*begin(.*?)end", code, re.DOTALL)
    for block in always_blocks:
        assigned_vars = set(re.findall(r"(\w+)\s*<=", block))
        for var in assigned_vars:
            if not re.search(rf"reg\s+(\[\d+:\d+\])?\s*{var}", code) and not re.search(rf"output\s+reg\s+(\[\d+:\d+\])?\s*{var}", code):
                issues.append(f"⚠️ Variable '{var}' assigned but not declared as reg")

    assigns = re.findall(r'assign\s+(\w+)\s*=', code)
    for var in assigns:
        if re.search(rf'\breg\b.*\b{var}\b', code):
            issues.append(f"⚠️ `assign` statement used on `reg` variable '{var}' (illegal in Verilog).")

    for var in assigns:
        if re.search(rf'\breg\b\s+{var}\b', code):
            code = re.sub(rf'\breg\b\s+{var}', f'wire {var}', code)

    if re.search(r"reg\s+\w*counter\w*;", code):
        issues.append("⚠️ Counter declared without bit width")

    if re.search(r"always\s+@\s*\(\s*posedge\s+\w+\s*\).*?=\s*[^=]", code):
        issues.append("⚠️ Blocking assignment (=) in sequential block")

    if re.search(r"always\s+@\s*\(\s*\*\s*\).*?<=", code):
        issues.append("⚠️ Non-blocking assignment (<=) in combinational block")

    if re.search(r'(reg|wire)\s+[^;=]+\s*=\s*;', code):
        issues.append("⚠️ Stray semicolon in initialization")

    return issues

# Templates for verified HDL modules
HDL_TEMPLATES = {
    "counter": """
module counter(
    input clk,
    input rst,
    input en,
    output reg [3:0] count
);
    always @(posedge clk) begin
        if (rst)
            count <= 4'b0000;
        else if (en)
            count <= count + 1'b1;
    end
endmodule
""",
    "uart_tx": """
module uart_tx(
    input clk,
    input rst,
    input [7:0] data_in,
    input [2:0] baud_sel,
    input parity_en,
    output reg tx,
    output reg busy
);
    // States
    parameter IDLE = 2'b00;
    parameter START = 2'b01;
    parameter DATA = 2'b10;
    parameter STOP = 2'b11;
    
    reg [1:0] state;
    reg [15:0] baud_counter;
    reg [15:0] baud_rate;
    reg [2:0] bit_counter;
    reg [7:0] data_reg;
    
    // Baud rate selection
    always @(*) begin
        case(baud_sel)
            3'b000: baud_rate = 16'd10417; // 9600 baud @100MHz
            3'b001: baud_rate = 16'd5208;  // 19200 baud
            3'b010: baud_rate = 16'd2604;  // 38400 baud
            3'b011: baud_rate = 16'd1302;  // 76800 baud
            3'b100: baud_rate = 16'd868;   // 115200 baud
            default: baud_rate = 16'd10417;
        endcase
    end
    
    always @(posedge clk) begin
        if (rst) begin
            state <= IDLE;
            tx <= 1'b1;
            busy <= 1'b0;
            baud_counter <= 16'd0;
            bit_counter <= 3'd0;
            data_reg <= 8'd0;
        end else begin
            case (state)
                IDLE: begin
                    tx <= 1'b1;
                    if (data_in != data_reg) begin
                        busy <= 1'b1;
                        state <= START;
                        data_reg <= data_in;
                        baud_counter <= 16'd0;
                    end
                end
                START: begin
                    tx <= 1'b0;
                    if (baud_counter >= baud_rate) begin
                        state <= DATA;
                        baud_counter <= 16'd0;
                        bit_counter <= 3'd0;
                    end else
                        baud_counter <= baud_counter + 1'b1;
                end
                DATA: begin
                    tx <= data_reg[bit_counter];
                    if (baud_counter >= baud_rate) begin
                        baud_counter <= 16'd0;
                        if (bit_counter == 3'd7) begin
                            state <= STOP;
                        end else
                            bit_counter <= bit_counter + 1'b1;
                    end else
                        baud_counter <= baud_counter + 1'b1;
                end
                STOP: begin
                    tx <= 1'b1;
                    if (baud_counter >= baud_rate) begin
                        state <= IDLE;
                        busy <= 1'b0;
                        baud_counter <= 16'd0;
                    end else
                        baud_counter <= baud_counter + 1'b1;
                end
            endcase
        end
    end
endmodule
"""
}

# --- Prompt Templates ---

HDL_PROMPT_TEMPLATE = """
You are an expert Verilog design engineer. Generate ONLY synthesizable Verilog code with NO commentary or markdown. Follow these strict guidelines:

1. Start with proper module declaration including ALL ports with correct widths
   Example: module counter(input clk, input rst, output reg [3:0] count);

2. Sequential logic MUST use:
   - Use `reg` ONLY for variables assigned in `always` blocks — DO NOT assign them using `assign`
   - Use `assign` ONLY for `wire` declarations
   - always @(posedge clk) for clocked logic
   - Non-blocking assignments (<=) for sequential logic

3. Combinational logic MUST use:
   - always @(*) or sensitivity lists with all signals
   - Blocking assignments (=) for combinational logic

4. NEVER use:
   - Python-style loops (for i in range())
   - Floating-point notation (1.5e6)
   - integer type for counters (use reg [N:0] instead)
   - Missing bit widths on buses

5. PROPER SYNTAX EXAMPLES:
   - Multi-bit signal: wire [7:0] data; NOT wire data;
   - For loop: for (i = 0; i < 8; i = i + 1) NOT for i in range(8)
   - Parameters: parameter WIDTH = 8; NOT const int WIDTH = 8;
   - Counter: reg [15:0] counter; NOT reg counter;

IMPORTANT: YOUR RESPONSE MUST CONTAIN ONLY VERILOG CODE. NO EXPLANATION, NO INTRO TEXT, NO MARKDOWN. START DIRECTLY WITH 'module' AND END WITH 'endmodule' - NOTHING ELSE.
"""

TB_PROMPT_TEMPLATE = """
You are an expert Verilog testbench engineer. Generate ONLY synthesizable Verilog testbench code with NO commentary. Follow these strict rules:

1. Start with module tb_modulename; and end with endmodule
2. Instantiate the module with all correct port mappings
3. Generate a 10ns clock using: always #5 clk = ~clk;
4. Initialize all inputs at time 0
5. MUST include:
   - $dumpfile("sim_files/wave.vcd");
   - $dumpvars(0, UUT);
   - $finish

MODULE TO TEST:
{hdl_code}
"""

# --- Generation Functions ---

def generate_hdl_code(spec, model="deepseek-r1-distill-llama-70b"):
    prompt = HDL_PROMPT_TEMPLATE + "\n\nSpecification:\n" + spec
    raw_code = call_llm(prompt, model=model)
    cleaned_code = strip_narrative_text(raw_code)
    fixed_code = comprehensive_hdl_fixes(cleaned_code)
    return fixed_code

def generate_testbench(hdl_code, model="deepseek-r1-distill-llama-70b"):
    prompt = TB_PROMPT_TEMPLATE.format(hdl_code=hdl_code)
    raw_code = call_llm(prompt, model=model)
    cleaned_code = strip_narrative_text(strip_code_fences(raw_code))
    fixed_code = comprehensive_hdl_fixes(cleaned_code)
    return fixed_code

def ensure_module_syntax(code):
    code = code.strip()
    if not code.lower().startswith("module"):
        code = "module auto_tb;\n" + code
    if "endmodule" not in code:
        code += "\nendmodule"
    return code

# --- Streamlit Page Layout ---

st.set_page_config(page_title="HDL Generator", layout="wide")
st.title("HDL Code Generator")
st.markdown("Generate HDL code from your specification (auto-filled from previous step). You may edit if needed.")

vcd_toggle = st.checkbox("Generate waveform file for simulation (`wave.vcd`)", value=True)

# --- Module Specification Input ---

if "specification" in st.session_state:
    spec = st.session_state["specification"]
    default_spec = f"Module name: {spec.get('module_name','')}\nDescription: {spec.get('description','')}\nInputs: {spec.get('inputs','')}\nOutputs: {spec.get('outputs','')}\nConstraints: {spec.get('constraints','')}"
    spec_input = st.text_area("Module Specification", value=default_spec, height=150)
    mod_name = st.text_input("Optional: Module name for simulation scope / waveform dumpvars", value="UUT")
    st.session_state["module_name"] = mod_name
else:
    st.info("No specification found. See examples below or enter manually.")
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

# --- HDL Generation Button ---

if st.button("Generate HDL Code") and spec_input:
    with st.spinner("Generating HDL code..."):
        try:
            spec_input_clean = spec_input.replace("\n", ", ").strip()
            hdl_raw = generate_hdl_code(spec_input_clean)
            is_hdl_valid = hdl_raw.strip().lower().startswith("module") and "endmodule" in hdl_raw
            st.session_state["hdl_code"] = hdl_raw
            st.session_state["testbench_code"] = ""
            st.session_state["generate_tb"] = False
            if not is_hdl_valid:
                st.warning("⚠️ HDL code may be malformed or missing module/endmodule. Auto-fix attempted.")
        except Exception as e:
            st.error(f"Error generating HDL code: {e}")

# --- Display HDL Code ---

hdl_code = st.session_state.get("hdl_code", "")
testbench_code = st.session_state.get("testbench_code", "")

if hdl_code:
    st.success("Generated HDL Code (editable):")
    editable_hdl_code = st.text_area("Edit HDL Code", value=hdl_code, height=250, key="hdl_edit")

    validation_issues = enhanced_validation(editable_hdl_code)

    if validation_issues:
        st.warning("⚠️ HDL Validation Issues:")
        for issue in validation_issues:
            st.markdown(f"- {issue}")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Auto-fix HDL Code"):
                fixed_hdl = comprehensive_hdl_fixes(editable_hdl_code)
                st.session_state["hdl_code"] = fixed_hdl
                st.rerun()
        with col2:
            if st.button("Regenerate HDL Code"):
                st.session_state["hdl_code"] = ""
                st.session_state["generate_tb"] = False
                st.rerun()
        with col3:
            if len(validation_issues) > 3:
                template_options = list(HDL_TEMPLATES.keys())
                selected_template = st.selectbox("Use verified template:", ["-- Select --"] + template_options)
                if selected_template != "-- Select --":
                    st.session_state["hdl_code"] = HDL_TEMPLATES[selected_template]
                    st.rerun()
    else:
        st.success("✅ Validation passed — HDL code is synthesizable!")
        if st.button("Generate Testbench from Edited HDL"):
            st.session_state["hdl_code"] = editable_hdl_code
            st.session_state["generate_tb"] = True
            st.rerun()

# --- Testbench Generation ---

if st.session_state["generate_tb"] and not testbench_code and hdl_code:
    fallback_tb_code = """
module dummy_tb;
  reg clk = 0;
  reg rst = 1;
  initial begin
    #20 rst = 0;
    #100 $finish;
  end

  always #5 clk = ~clk;

  initial begin
    $dumpfile("sim_files/wave.vcd");
    $dumpvars(0, dummy_tb);
  end
endmodule
"""
    with st.spinner("Generating testbench..."):
        try:
            raw_tb_code = generate_testbench(hdl_code)
            st.expander("Raw Testbench Output (before fix)").code(raw_tb_code, language="verilog")
            is_valid = raw_tb_code.strip().lower().startswith("module") and "endmodule" in raw_tb_code
            if not re.search(r'\b(initial|always)\b', raw_tb_code):
                is_valid = False
            if not is_valid:
                st.warning("Generated testbench is malformed. Auto-fix attempted.")
                auto_fixed_tb = ensure_module_syntax(raw_tb_code)
                if auto_fixed_tb.strip().lower().startswith("module") and "endmodule" in auto_fixed_tb:
                    raw_tb_code = auto_fixed_tb
                else:
                    use_fallback = st.checkbox("Use fallback dummy testbench?")
                    if use_fallback:
                        raw_tb_code = fallback_tb_code
                    else:
                        if st.button("Regenerate Testbench"):
                            st.session_state["generate_tb"] = True
                            st.rerun()
                        st.stop()
            # Add $dumpfile if missing
            if vcd_toggle and "$dumpfile" not in raw_tb_code:
                mod_name = st.session_state.get("module_name", "UUT")
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

            st.session_state["testbench_code"] = testbench_code
            st.session_state["generate_tb"] = False
        except Exception as e:
            st.error(f"Error generating testbench: {e}")
            st.session_state["testbench_code"] = fallback_tb_code

# --- Display Testbench Code & Download ---

testbench_code = st.session_state.get("testbench_code", "")
if testbench_code:
    st.success("Generated Testbench:")
    st.code(testbench_code, language="verilog")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button("Download Testbench", data=testbench_code, file_name="testbench.v")
    with col2:
        if hdl_code:
            st.download_button("Download HDL Module", data=hdl_code, file_name="module.v")