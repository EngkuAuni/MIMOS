import streamlit as st

st.title("Streamlit Test")
st.write("Wondering how to go on with your life?")

struggle = st.text_input("Current Stuggle(s): ")
if struggle:
    st.success(f"Oof, {struggle} is tough")