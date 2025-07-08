import os
import ast

COGS_DIR = "cogs"

def has_setup_function(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        print(f"❌ Syntax error in {filepath}: {e}")
        return True  # Skip broken files

    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name == "setup":
            return True
    return False

def get_first_cog_class(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        source = f.read()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return None

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            for base in node.bases:
                if isinstance(base, (ast.Name, ast.Attribute)):
                    if getattr(base, "id", "") == "Cog" or getattr(base, "attr", "") == "Cog":
                        return node.name
    return None

def append_setup_function(filepath, cog_class):
    setup_code = f"""

async def setup(bot):
    await bot.add_cog({cog_class}(bot))
"""
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(setup_code)
    print(f"✅ Added setup(bot) to: {filepath}")

def main():
    print("🔍 Scanning cogs/ for missing setup functions...\n")
    for filename in os.listdir(COGS_DIR):
        if not filename.endswith(".py") or filename.startswith("_"):
            continue

        path = os.path.join(COGS_DIR, filename)
        if has_setup_function(path):
            print(f"✔️  {filename} already has setup()")
        else:
            cog_class = get_first_cog_class(path)
            if cog_class:
                append_setup_function(path, cog_class)
            else:
                print(f"⚠️  No Cog class found in {filename}, skipped.")

if __name__ == "__main__":
    main()
