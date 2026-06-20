import os

def generate_codebase_summary(root_dir, output_file):
    """
    Traverses the project directory, creates a tree structure,
    and appends the content of relevant files.
    """
    # Exclude directories that do not contain source code
    ignore_dirs = {'.git', '__pycache__', 'venv', 'env', '.idea', '.vscode'}
    
    # Target specific file types relevant to SATE Financial System MVP
    allowed_extensions = {'.py', '.sql', '.md', '.json', '.env.example'}

    with open(output_file, 'w', encoding='utf-8') as outfile:
        # 1. Document the Directory Structure
        outfile.write("# Directory Structure\n")
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            level = root.replace(root_dir, '').count(os.sep)
            indent = ' ' * 4 * level
            outfile.write(f"{indent}{os.path.basename(root)}/\n")
            sub_indent = ' ' * 4 * (level + 1)
            for f in files:
                if any(f.endswith(ext) for ext in allowed_extensions):
                    outfile.write(f"{sub_indent}{f}\n")

        outfile.write("\n\n# File Contents\n")
        outfile.write("="*50 + "\n\n")

        # 2. Append the Content of Each Target File
        for root, dirs, files in os.walk(root_dir):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            for f in files:
                if any(f.endswith(ext) for ext in allowed_extensions):
                    file_path = os.path.join(root, f)
                    relative_path = os.path.relpath(file_path, root_dir)
                    
                    outfile.write(f"## File: {relative_path}\n")
                    outfile.write("-" * 30 + "\n")
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as infile:
                            outfile.write(infile.read() + "\n\n")
                    except Exception as e:
                        outfile.write(f"[Error reading file: {e}]\n\n")

if __name__ == "__main__":
    # Run in the current SATE_Fin_Dev directory
    project_path = "." 
    output_filename = "SATE_codebase_context.md"
    generate_codebase_summary(project_path, output_filename)
    print(f"Success! Please upload '{output_filename}' to the chat.")