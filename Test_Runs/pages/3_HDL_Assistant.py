# HDL Code & IC Design Explainer
# Input HDL code or IC design queries --> Get explanation
# Display result (Q&A or code explaination)

import streamlit as st
import ollama
import json

def analyze_hdl(user_input, model="mistral"):
    prompt = f"""
You are an expert digital IC design engineer and technical writer.
Given the following input (which may be Verilog HDL or a conceptual design question), provide your response in JSON format like this:
{{
    "type": "code_explanation" or "design_question",
    "summary": "Brief explanation of what the code does or answer to the question.",
    "code_comments": "If code, add detailed line-by-line commentary.",
    "additional_notes": "Optional - design tips, common mistakes, related concepts."
}}
Input: {user_input}
    """

    response = ollama.chat(
        model = model,
        messages = [
            {"role": "user", "content": prompt}
        ],
    )
    return response["message"]["content"]

st.set_page_config(page_title="HDL Assistant", layout="wide")
st.title("HDL Assistant")
st.markdown("Ask anything about HDL or IC design. You can also paste Verilog code to get an explanation.")

example_inputs = {
    "Explain HDL Code": "module counter(input clk, reset, output reg [3:0] count); always @(posedge clk or posedge reset) begin if (reset) count <= 0; else count + 1; end endmodule",
    "Q&A - FSM": "What is the difference between a Moore and Mealy FSM?",
    "Q&A - Reset Types": "Why is asynchronous reset sometimes preferred in HDL design?"
}

# Pre-fill with generated HDL code if available
prefill = ""
if "hdl_code" in st.session_state and st.session_state["hdl_code"]:
    prefill = st.session_state["hdl_code"]

selected_example = st.selectbox("Examples", ['-- Select --'] + list(example_inputs.keys()))
if selected_example != "-- Select --":
    user_input = st.text_area("Enter HDL code or IC design queries:", value=example_inputs[selected_example], height=300)
else:
    user_input = st.text_area("Enter HDL code or IC design queries:", height=300)

if st.button("Submit") and user_input:
    with st.spinner("Analyzing..."):
        try:
            raw_output = analyze_hdl(user_input)
            try:
                parsed = json.loads(raw_output)
                st.success("Assistant response:")
                st.subheader("Summary")
                st.markdown(parsed.get("summary", ""))
                if parsed.get("code_comments"):
                    with st.expander("Code Commentary"):
                        st.code(parsed["code_comments"], language="verilog")
                if parsed.get("additional_notes"):
                    with st.expander("Additional Notes"):
                        st.markdown(parsed["additional_notes"])
                st.download_button("Download JSON", data=json.dumps(parsed, indent=2), file_name="hdl_explanation.json")
            except json.JSONDecodeError:
                st.warning("Could not parse structured output. Showing raw response instead:")
                st.markdown(raw_output)
        except Exception as e:
            st.error(f"Error: {e}")
if st.button("Next: Simulation");
    st.experimental_set_query_params(page="4_Simulation")
    st.info("Navigate to the Simulation page using the sidebar.")