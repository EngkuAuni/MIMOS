# HDL Code & IC Design Explainer
# Input HDL code or IC design queries --> Get explanation
# Display result (Q&A or code explaination)

import streamlit as st
import re
import json
from LLM_utils import call_llm

def strip_narrative_text(code):
    """Remove LLM narrative like <think> tags or intros before `module` or JSON."""
    code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL)
    code = code.replace("```json", "").replace("```", "").strip()
    
    # Remove intro text
    code = re.sub(r"(?i)^here is.*?({|\[|module)", r"\1", code.strip(), flags=re.DOTALL)
    
    return code

def extract_json_from_response(text):
    """Extract JSON from LLM response, handling markdown and other formatting"""
    text = strip_narrative_text(text)
    
    # Try to find JSON object
    json_match = re.search(r'\{[\s\S]*\}', text)
    if json_match:
        json_str = json_match.group(0)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            pass
    
    # Try to parse the whole text
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        # If JSON parsing fails, create a structured response from text
        return {
            "type": "general_response",
            "summary": text,
            "code_comments": "",
            "additional_notes": ""
        }

def is_verilog_code(text):
    """Simple heuristic to detect Verilog code."""
    return bool(re.search(r'\bmodule\b.*\bendmodule\b', text, re.DOTALL))

def analyze_hdl(user_input, model="llama-3.1-8b-instant"):
    # Determine the input type
    input_type = "verilog_code" if is_verilog_code(user_input) else "design_question"

    prompt = f"""You are an expert digital IC design engineer and technical writer.

The following input is of type: {input_type}

Return your response STRICTLY in this JSON format (NO markdown, NO code fences, NO extra text):

{{
    "type": "{input_type}",
    "summary": "Brief explanation of what the code does or answer to the question.",
    "code_comments": "If input is Verilog HDL, add detailed line-by-line commentary.",
    "additional_notes": "Optional - design tips, common mistakes, related concepts."
}}

CRITICAL: Return ONLY the JSON object above, nothing else. No markdown, no explanations, no code fences.

Input: {user_input}"""
    response = call_llm(prompt, model=model)

    # FIX: If response is string, return it directly
    if isinstance(response, str):
        return response

    # If it's a dictionary as expected
    if isinstance(response, dict) and "message" in response and "content" in response["message"]:
        return response["message"]["content"]

    # Fallback: dump whole response
    return str(response)

st.set_page_config(page_title="HDL Assistant", layout="wide")
st.title("HDL Assistant")
st.markdown("If you generated HDL code in the previous step, it's auto-filled below for explaination." \
" Or paste any HDL code, or ask any IC design question!")

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
    user_input = st.text_area("Enter HDL code or IC design queries:", value=prefill, height=300)

if st.button("Submit") and user_input:
    with st.spinner("Analyzing..."):
        try:
            raw_output = analyze_hdl(user_input)
            parsed = extract_json_from_response(raw_output)
            
            # Display the response
            st.success("Assistant response:")
            
            # Show summary
            if parsed.get("summary"):
                st.subheader("Summary")
                st.markdown(parsed["summary"])
            
            # Show code commentary if present
            if parsed.get("code_comments"):
                with st.expander("Code Commentary"):
                    st.code(parsed["code_comments"], language="verilog")
            
            # Show additional notes if present
            if parsed.get("additional_notes"):
                with st.expander("Additional Notes"):
                    st.markdown(parsed["additional_notes"])
            
            # Download button
            st.download_button("Download JSON", data=json.dumps(parsed, indent=2), file_name="hdl_explanation.json")
            
        except Exception as e:
            st.error(f"Error: {e}")