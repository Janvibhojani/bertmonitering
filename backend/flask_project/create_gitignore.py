gitignore_content = """
# ----------------------
# Python
# ----------------------
__pycache__/
*.py[cod]
*.pyo
*.pyd
*.egg-info/
dist/
build/

# ----------------------
# Virtual Environment
# ----------------------
venv/
env/
.venv/

# ----------------------
# Environment variables
# ----------------------
.env
.env.*

# ----------------------
# Logs
# ----------------------
*.log

# ----------------------
# OS files
# ----------------------
.DS_Store
Thumbs.db
desktop.ini

# ----------------------
# VS Code
# ----------------------
.vscode/

# ----------------------
# Jupyter
# ----------------------
.ipynb_checkpoints/

# ----------------------
# Node / Frontend
# ----------------------
node_modules/

# ----------------------
# Local DB / JSON
# ----------------------
*.sqlite3
*.db
scrape_domain.json
"""

with open(".gitignore", "w", encoding="utf-8") as f:
    f.write(gitignore_content.strip())

print("✅ .gitignore file created successfully")
