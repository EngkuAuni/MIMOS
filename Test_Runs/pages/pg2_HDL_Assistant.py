## What would an IC designer find useful about this app?
# HDL Code Explainer
# Input HDL code or IC design queries --> Get explanation
# Display result (Q&A or code explaination)

import streamlit as st
import ollama

st.set_page_config(page_title = "HDL Assistant", layout = "wide")
st.title("HDL Assistant")
st.markdown ("Ask anything about HDL or IC design. You can also paste Verilog code to get an explaination")

# Exampple input: HDL code or design queries
example_inputs = {
    "Explain HDL Code" : "module counter(input clk, reset, output reg [3:0] count); always @(posedge clk or posedge reset) begin if (reset) count <= 0; else count + 1; end endmodule",
    "Q&A - FSM" :"What is the difference between a Moore and Mealy FSM?",
    "Q&A - Reset Types" : "Why is asynchronous reset sometimes prefered in HDL design?"
}

# Dropdown preset
selected_example = st.selectbox("Examples", ['-- Select --']+list(example_inputs.keys()))
if selected_example != "-- Select --":
    user_input = example_inputs[selected_example]
else:
    user_input = st.text_area ("Enter HDL code or IC design queries:", height = 300)

# Generate
if st.button("Submit") and user_input:
    with st.spinner("Analyzing..."):
        try:
            prompt = f"""
You are an expert digital IC design engineer and techincal writer.
If the input is Verilog HDL code, explain it clearly.
If it's a question about IC/HDL concepts, provide an accurate explaination.
Be concise and helpful.
Input: {user_input}
            """

            response = ollama.chat(
                model = "mistral",
                messages = [
                    {"role": "user", "content": prompt}
                ],
            )

            answer = response["message"]["content"]

            st.success("Assistant response:")
            st.markdown(answer)

        except Exception as e:
            st.error(f"Error: {e}")