import os
import sys
from pathlib import Path
import uvicorn
# 自动加路径
root_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(root_dir / "src"))
sys.path.insert(0, str(root_dir / "backend"))
sys.path.insert(0, str(root_dir))
if __name__ == "__main__":
    uvicorn.run(
        "backend.api.core.app:app",
        host="0.0.0.0",
        port=8001,
        reload=True
    )