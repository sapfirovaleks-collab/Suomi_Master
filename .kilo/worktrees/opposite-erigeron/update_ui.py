import re

path = "templates/index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Делаем боковую панель адаптивной для мобильных
content = content.replace("width:420px;", "width:100%; max-width:420px;")

# Отображаем навигационные вкладки гибкой сеткой
content = re.sub(r'(\.nav-tabs\s*\{[^}]*display:)\s*grid;', r'\1 flex; flex-wrap: wrap;', content)
content = re.sub(r'(\.nav-tabs-2\s*\{[^}]*display:)\s*grid;', r'\1 flex; flex-wrap: wrap;', content)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("UI updated successfully")
