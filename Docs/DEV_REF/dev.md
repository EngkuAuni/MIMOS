## Cmd Refs
# Rebuild image only for system/dependenciy changes 
docker build -t quranverf .
# Run container with Volume Mount to enable live code sync
docker run -it --rm -p 8501:8501 -v $(pwd):/app quranverf
# The QuranVerf venv is used for one-time utils (initialize_hash, descriptor_generator)
# Streamlit web UI: 
http://localhost:8501
# Remove old descriptors when adding more ref images for ORB + SIFT
rm -rf Data/assets/orb_sift/*
python app/generate_descriptors.py --input Data/reference_imgs --edition Uthmani

# Run stremlit natively
streamlit run app/main.py