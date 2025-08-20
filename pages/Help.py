import streamlit as st
import os

st.title("Help")

# Construct the absolute path to README.md
readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "README.md")

with open(readme_path, "r", encoding="utf-8") as f:
    readme_content = f.read()

st.markdown(readme_content, unsafe_allow_html=True)