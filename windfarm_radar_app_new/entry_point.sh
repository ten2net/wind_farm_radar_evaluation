chmod +x /workspace/entry_point.sh
uv sync
source .venv/bin/activate
streamlit run main.py