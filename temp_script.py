import ast
import os

files = ['detect_humans_yolo.py', 'detect_humans_filehistory.py']

for fpath in files:
    print(f"\n" + "="*50)
    print(f"--- Analyzing {fpath} ---")
    print("="*50)
    if not os.path.exists(fpath):
        print("File not found.")
        continue
        
    with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        
    try:
        tree = ast.parse(content)
        doc = ast.get_docstring(tree)
        print("Docstring:\n  " + (doc.replace('\n', '\n  ') if doc else "None") + "\n")
        
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names: imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module: imports.append(node.module)
        print("Imports: " + (", ".join(sorted(set(imports))) if imports else "None"))
        
        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        print("Classes: " + (", ".join(classes) if classes else "None"))
        
        funcs = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
        print("Functions: " + (", ".join(funcs) if funcs else "None"))
        
        print("\nFirst 10 lines:")
        for i, line in enumerate(content.splitlines()[:10]):
            print(f"  {i+1:02d} | {line}")
            
    except Exception as e:
        print(f"Error parsing AST: {e}")
        print("\nFirst 10 lines:")
        for i, line in enumerate(content.splitlines()[:10]):
            print(f"  {i+1:02d} | {line}")

print("\n" + "="*50)
print("Analysis complete. Script preserved as requested.")
