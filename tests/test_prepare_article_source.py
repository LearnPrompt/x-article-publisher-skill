import importlib.util
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "skills"
    / "x-article-publisher"
    / "scripts"
    / "prepare_article_source.py"
)
SPEC = importlib.util.spec_from_file_location("prepare_article_source", MODULE_PATH)
prepare_article_source = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(prepare_article_source)


class FeishuDownloadCommandTests(unittest.TestCase):
    def test_wiki_page_url_is_downloaded_as_single_document(self):
        source_url = "https://example.feishu.cn/wiki/page-token?from=copy"
        completed = subprocess.CompletedProcess([], 0, "", "")

        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.object(
                prepare_article_source.subprocess,
                "run",
                return_value=completed,
            ) as run:
                prepare_article_source.run_feishu2md_download(
                    source_url, Path(temp_dir)
                )

        command = run.call_args.args[0]
        self.assertNotIn("--wiki", command)
        self.assertEqual(command[-1], source_url)


if __name__ == "__main__":
    unittest.main()
