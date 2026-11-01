import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

# ตั้งค่า path ก่อน import อะไร
from common.state_dir import state_root_str
workspace = state_root_str()
print(f"📂 Workspace: {workspace}")

from agent.memory.config import get_default_memory_config
config = get_default_memory_config()
print(f"✅ Config loaded: embedding={config.embedding_provider}/{config.embedding_model}")

# เรียกฟังก์ชันสร้างดัชนี
from agent.memory.embedding.rebuild import main
sys.exit(main())
