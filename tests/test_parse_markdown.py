import importlib.util
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "skills"
    / "x-article-publisher"
    / "scripts"
    / "parse_markdown.py"
)
SPEC = importlib.util.spec_from_file_location("parse_markdown", MODULE_PATH)
parse_markdown = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(parse_markdown)


class AnchorNormalizationTests(unittest.TestCase):
    def extract_anchor(self, preceding_text: str) -> str:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            image_path = temp_path / "image.png"
            image_path.touch()
            markdown = f"{preceding_text}\n\n![]({image_path})"
            media, _, _, _ = parse_markdown.extract_media_and_dividers(
                markdown, temp_path
            )
        self.assertEqual(len(media), 1)
        return media[0]["after_text"]

    def test_strips_leading_list_markers_from_media_anchors(self):
        for marker in ("-", "*", "+", "•"):
            with self.subTest(marker=marker):
                self.assertEqual(
                    self.extract_anchor(f"{marker} A rendered list item"),
                    "A rendered list item",
                )

    def test_normalizes_anchor_before_truncating_to_eighty_characters(self):
        payload = "A" * 90
        anchor = self.extract_anchor(f"- {payload}")
        self.assertEqual(anchor, payload[:80])
        self.assertEqual(len(anchor), 80)

    def test_preserves_hyphens_inside_normal_text(self):
        text = "GPT-5.6 remains part of the anchor"
        self.assertEqual(self.extract_anchor(text), text)

    def test_applies_same_normalization_to_divider_anchors(self):
        markdown = "- Section ending\n\n---"
        _, dividers, _, _ = parse_markdown.extract_media_and_dividers(
            markdown, Path.cwd()
        )
        self.assertEqual(dividers[0]["after_text"], "Section ending")


if __name__ == "__main__":
    unittest.main()
