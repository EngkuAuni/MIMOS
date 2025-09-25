# Cmd Refs
# Rebuild image after script patching
docker build -t quranverf .
# Run and remove container after stopping (streamlit port 8501)
docker run -it -p 8501:8501 --rm quranverf
