import importlib.util
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "skills"
    / "x-article-publisher"
    / "scripts"
    / "optimize_media_blocks.py"
)
SPEC = importlib.util.spec_from_file_location("optimize_media_blocks", MODULE_PATH)
optimize_media_blocks = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(optimize_media_blocks)


class AdaptiveCollageTests(unittest.TestCase):
    def test_five_images_use_balanced_grid_without_cropping(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            image_paths = []
            colors = [
                (255, 0, 0),
                (0, 255, 0),
                (0, 0, 255),
                (255, 255, 0),
                (255, 0, 255),
            ]
            sizes = [(1200, 700), (700, 700), (900, 400), (850, 380), (750, 320)]

            for index, (color, size) in enumerate(zip(colors, sizes)):
                image = Image.new("RGB", size, color)
                if index == 0:
                    draw = ImageDraw.Draw(image)
                    draw.rectangle((0, 0, 80, 80), fill=(0, 255, 255))
                    draw.rectangle(
                        (size[0] - 81, size[1] - 81, size[0] - 1, size[1] - 1),
                        fill=(255, 255, 255),
                    )
                path = root / f"source-{index}.png"
                image.save(path)
                image_paths.append(path)

            output = root / "collage.png"
            layout = optimize_media_blocks.make_collage(
                image_paths,
                output,
                width=1200,
                padding=20,
            )

            self.assertEqual(layout["layout"], "adaptive_grid")
            self.assertEqual(layout["row_counts"], [2, 3])
            self.assertEqual(layout["width"], 1200)
            self.assertLess(layout["height"] / layout["width"], 1.2)

            with Image.open(output) as collage:
                rendered_colors = set(collage.convert("RGB").getdata())
            for color in colors + [(0, 255, 255), (255, 255, 255)]:
                self.assertIn(color, rendered_colors)

    def test_optimizer_reduces_media_count_and_reports_grid_layout(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            static = root / "static"
            static.mkdir()
            markdown_parts = ["# Test", "![Cover](static/cover.png)", "Anchor"]

            Image.new("RGB", (600, 400), "black").save(static / "cover.png")
            for index in range(5):
                image_path = static / f"body-{index}.png"
                Image.new("RGB", (600 + index * 20, 400), "white").save(image_path)
                markdown_parts.append(f"![](static/{image_path.name})")

            markdown = root / "article.md"
            markdown.write_text("\n\n".join(markdown_parts), encoding="utf-8")
            output = root / "article.optimized.md"
            result = optimize_media_blocks.optimize(
                markdown,
                output,
                max_body_media=1,
                width=1200,
                padding=20,
            )

            self.assertEqual(result["body_media_before"], 5)
            self.assertEqual(result["body_media_after"], 1)
            self.assertEqual(result["collages"][0]["row_counts"], [2, 3])
            self.assertIn("static/x_article_collage_01.png", output.read_text())


if __name__ == "__main__":
    unittest.main()
