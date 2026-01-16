chmod +x /workspace/entry_point.sh
uv sync
source .venv/bin/activate
streamlit run "🛰️ 数字射频战场仿真系统.py"