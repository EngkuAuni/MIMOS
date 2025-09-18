# Example specs for quick start
# Collects and saves requirements in st.session_state for use across pages
# Shows last saved spec and allows download as JSON

import streamlit as st
import json
import re

st.set_page_config(page_title="IC Design Specification", layout="wide")
st.title("IC Design Specification")
st.markdown("""
**Step 1: Specify your IC/module requirements.**  
This guides HDL generation, verification, and review.<br>
Fill out the fields below, or choose a template example to get started.
""", unsafe_allow_html=True)

example_specs = {
    "UART Transmitter": {
        "module_name": "uart_tx",
        "description": "UART transmitter with configurable baud rate, 8-bit data input, start/stop bits, and optional parity.",
        "inputs": "clk, rst, data_in[7:0], baud_sel[2:0], parity_en",
        "outputs": "tx, busy",
        "constraints": "Max clock frequency 100MHz. Low power. Parity enable is single-bit. Baud rate selected by baud_sel.",
        "notes": "Should handle framing errors. Parity selection via parity_en (1=enable, 0=disable)."
    },
    "SPI Master": {
        "module_name": "spi_master",
        "description": "SPI master with configurable clock polarity/phase, 8-bit data transfer, chip select support.",
        "inputs": "clk, rst, miso, sclk, cs",
        "outputs": "mosi, data_out[7:0], ready",
        "constraints": "Supports SPI modes 0-3. Max SCLK 50MHz.",
        "notes": "Provide option for programmable clock divider."
    },
    "Synchronous Counter": {
        "module_name": "counter",
        "description": "4-bit synchronous up/down counter with reset, enable, and direction control.",
        "inputs": "clk, rst, en, up_down",
        "outputs": "count[3:0]",
        "constraints": "Synchronous reset preferred.",
        "notes": "Enable input ('en') controls counting."
    }
}

selected_example = st.selectbox(
    "Example Modules", ['-- Select --'] + list(example_specs.keys())
)
if selected_example != "-- Select --":
    default = example_specs[selected_example]
else:
    default = {
        "module_name": "",
        "description": "",
        "inputs": "",
        "outputs": "",
        "constraints": "",
        "notes": ""
    }

with st.form("spec_form"):
    module_name = st.text_input("Module Name", value=default["module_name"])
    description = st.text_area("Functional Description", value=default["description"], height=80)
    inputs = st.text_area("Inputs (comma-separated, e.g. clk, rst, data[7:0])", value=default["inputs"], height=40)
    outputs = st.text_area("Outputs (comma-separated, e.g. tx, busy)", value=default["outputs"], height=40)
    constraints = st.text_area("Constraints (timing, area, power, etc.)", value=default["constraints"], height=40)
    notes = st.text_area("Additional Notes", value=default["notes"], height=40)
    submitted = st.form_submit_button("Save Specification")

def port_widths_check(port_string):
    """Warn if ports lack explicit bit width (e.g. data[7:0])"""
    ports = [p.strip() for p in port_string.split(',') if p.strip()]
    missing_widths = [
        p for p in ports if not re.search(r"\[.*:.*\]", p) and not re.match(
            r"(clk|rst|cs|en|tx|rx|miso|mosi|sclk|busy|ready|up_down|parity_en)$", p)
    ]
    return missing_widths

def validate_spec(spec):
    issues = []
    if not spec.get("module_name"):
        issues.append("Module Name is required.")
    if not spec.get("description"):
        issues.append("Description is required.")
    if not spec.get("inputs"):
        issues.append("At least one input port is required.")
    if not spec.get("outputs"):
        issues.append("At least one output port is required.")
    # Port widths check
    missing_input_widths = port_widths_check(spec.get("inputs", ""))
    missing_output_widths = port_widths_check(spec.get("outputs", ""))
    if missing_input_widths:
        issues.append(f"Inputs missing bit width: {', '.join(missing_input_widths)}")
    if missing_output_widths:
        issues.append(f"Outputs missing bit width: {', '.join(missing_output_widths)}")
    return issues

if submitted:
    spec_dict = {
        "module_name": module_name.strip(),
        "description": description.strip(),
        "inputs": inputs.strip(),
        "outputs": outputs.strip(),
        "constraints": constraints.strip(),
        "notes": notes.strip()
    }
    issues = validate_spec(spec_dict)
    if issues:
        st.warning("Please address the following issues before proceeding:")
        for issue in issues:
            st.write(f"- {issue}")
    else:
        st.session_state["specification"] = spec_dict
        st.success("Specification saved! Proceed to HDL Generation via the sidebar.")
        st.json(spec_dict)
        st.download_button(
            "Download Specification (JSON)",
            data=json.dumps(spec_dict, indent=2),
            file_name="specification.json"
        )
else:
    st.info("Fill in your specification and click 'Save Specification'. Your input will be available to other pages.")

if "specification" in st.session_state:
    with st.expander("Last Saved Specification"):
        st.json(st.session_state["specification"])