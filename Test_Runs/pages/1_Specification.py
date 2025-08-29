# Example specs for quick start
# Collects and saves requirements in st.session_state for use across pages
# Shows last saved spec and allows download as JSON

import streamlit as st

st.set_page_config(page_title="IC Design Specification", layout="wide")
st.title("IC Design Specification")
st.markdown("""
**Step 1: Specify your IC/module requirements.**  
This will guide the HDL generation, verification, and review process.<br>
Fill out the fields below, or choose a template example to get started.
""", unsafe_allow_html=True)

example_specs = {
    "UART Transmitter": {
        "module_name": "uart_tx",
        "description": "UART transmitter with configurable baud rate, 8-bit data input, start/stop bits, and optional parity.",
        "inputs": "clk, rst, data_in[7:0], baud_sel[2:0], parity_en",
        "outputs": "tx, busy",
        "constraints": "Max frequency 100MHz. Low power. Parity select optional.",
        "notes": "Should handle framing errors. Baud rate selection via baud_sel."
    },
    "SPI Master": {
        "module_name": "spi_master",
        "description": "SPI master with configurable clock polarity/phase, 8-bit data transfer, chip select support.",
        "inputs": "clk, rst, mosi, miso, sclk, cs",
        "outputs": "data_out[7:0], ready",
        "constraints": "Supports SPI modes 0-3. Max SCLK 50MHz.",
        "notes": "Provide option for programmable clock divider."
    },
    "Synchronous Counter": {
        "module_name": "counter",
        "description": "4-bit synchronous up/down counter with reset and direction control.",
        "inputs": "clk, rst, up_down",
        "outputs": "count[3:0]",
        "constraints": "Synchronous reset preferred.",
        "notes": "Add enable input for counting."
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

# Session state for code persistence
if submitted:
    st.session_state["specification"] = {
        "module_name": module_name,
        "description": description,
        "inputs": inputs,
        "outputs": outputs,
        "constraints": constraints,
        "notes": notes
    }
    st.success("Specification saved! Proceed to HDL Generation via the sidebar.")
    st.json(st.session_state["specification"])
    st.download_button(
        "Download Specification (JSON)",
        data=st.session_state["specification"] if isinstance(st.session_state["specification"], str) else str(st.session_state["specification"]),
        file_name="specification.json"
    )
else:
    st.info("Fill in your specification and click 'Save Specification'. Your input will be available to other pages.")

if "specification" in st.session_state:
    with st.expander("Last Saved Specification"):
        st.json(st.session_state["specification"])
        