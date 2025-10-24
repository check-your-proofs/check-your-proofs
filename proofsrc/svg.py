import subprocess
import hashlib
from pathlib import Path

def output_svg(latex_code: str) -> str:
    build_dir = Path("build")
    hash_value = hashlib.md5(latex_code.encode("utf-8")).hexdigest()
    tex_file = build_dir / "tex" / f"math_{hash_value}.tex"
    dvi_file = build_dir / "tex" / f"math_{hash_value}.dvi"
    svg_file = build_dir / "svg" / f"math_{hash_value}.svg"
    if not svg_file.exists():
        latex_code = latex_code.replace(r"\notin", r"\mathrel{\not\in}")
        tex_file.write_text(
            f"\\documentclass{{standalone}}\n"
            f"\\usepackage{{amsmath, amssymb}}\n"
            f"\\begin{{document}}\n"
            f"\\Large ${latex_code}$\n"
            f"\\end{{document}}",
            encoding="utf-8"
        )
        subprocess.run(["latex", "-interaction=nonstopmode", tex_file.name], check=True, cwd=str(build_dir / "tex"), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["dvisvgm", str(dvi_file), "-n", "-o", str(svg_file)], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return svg_file.read_text(encoding="utf-8")

if __name__ == "__main__":
    latex_code = r"\exists x\forall y(y\notin x)"
    svg_code = output_svg(latex_code)
    html_dir = Path("html")
    html_file = html_dir / "svg_test.html"
    html_file.write_text(
        f"""<!DOCTYPE html>
        <html>
        <head>
        <meta charset="UTF-8">
        <title>svg_test</title>
        </head>
        <body>
        <div class="math">{svg_code}</div>
        </body>
        </html>
        """,
        encoding="utf-8"
    )
