import streamlit as st
import os

# Page config
st.set_page_config(
    page_title="MARIA AP7",
    page_icon="🚗",
    layout="wide"
)

# Title
st.title("🚗 Predicció de Trànsit - MARIA AP7")

# Basic environment info
st.write("## Environment Information")
st.write(f"Current working directory: {os.getcwd()}")
st.write(f"Files in current directory:")

try:
    files = os.listdir('.')
    for file in sorted(files):
        if os.path.isfile(file):
            st.write(f"📄 {file}")
        else:
            st.write(f"📁 {file}/")
except Exception as e:
    st.write(f"Error listing files: {e}")

# Look for database file specifically
st.write("## Database File Search")
db_path = 'maria_ap7.duckdb'
st.write(f"Looking for: {db_path}")
st.write(f"Absolute path: {os.path.abspath(db_path)}")
st.write(f"File exists: {os.path.exists(db_path)}")

# Look in parent directory too
parent_path = f"../{db_path}"
st.write(f"Parent directory path: {os.path.abspath(parent_path)}")
st.write(f"Exists in parent: {os.path.exists(parent_path)}")

# Try to find any .duckdb files
st.write("## Searching for any .duckdb files")
try:
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.duckdb'):
                full_path = os.path.join(root, file)
                st.write(f"Found: {full_path}")
except Exception as e:
    st.write(f"Error searching: {e}")

st.write("## Next Steps")
st.write("Based on the file locations shown above, we can determine:")
st.write("1. Where the database file actually is")
st.write("2. What the correct path should be")
st.write("3. Whether we need to upload or create the database file")

st.success("Diagnostic version running successfully!")