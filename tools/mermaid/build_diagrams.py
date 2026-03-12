"""
Mermaid 圖表批次轉換工具
將 tools/mermaid/*.mmd 轉為 PNG，輸出至 docs/images/

用法：
    py tools/mermaid/build_diagrams.py
"""

import os
import subprocess
import sys


def build_all() -> None:
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, "../.."))
    output_dir = os.path.join(project_root, "docs", "images")
    os.makedirs(output_dir, exist_ok=True)

    mmd_files = [f for f in os.listdir(script_dir) if f.endswith(".mmd")]

    if not mmd_files:
        print("⚠️ No .mmd files found in tools/mermaid/")
        return

    for mmd_file in mmd_files:
        input_path = os.path.join(script_dir, mmd_file)
        output_name = mmd_file.replace(".mmd", ".png")
        output_path = os.path.join(output_dir, output_name)

        print(f"🔄 Converting {mmd_file} → docs/images/{output_name}")
        try:
            # Windows: npm global bins are .cmd files, use shell=True to resolve
            result = subprocess.run(
                f'mmdc -i "{input_path}" -o "{output_path}" -b transparent -s 2',
                check=True,
                capture_output=True,
                shell=True,
            )
            print(f"   ✅ Done")
        except subprocess.CalledProcessError as e:
            stderr = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
            print(f"   ❌ Failed: {stderr}")
        except FileNotFoundError:
            print("❌ mmdc not found. Install: npm install -g @mermaid-js/mermaid-cli")
            sys.exit(1)

    print(f"\n🎉 All diagrams saved to docs/images/")


if __name__ == "__main__":
    build_all()
