import json
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'skills/x-article-publisher/scripts'))
import parse_markdown as parser
import prepare_article_source as source
import optimize_media_blocks as optimizer


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.article = self.root / 'article.md'

    def image(self, name, color='red', size=(60, 40)):
        path = self.root / name
        Image.new('RGB', size, color).save(path)
        return path

    def test_mixed_media_cover_and_code_anchor(self):
        self.image('cover.png')
        self.image('body.png')
        (self.root / 'clip.mp4').write_bytes(b'fixture')
        self.article.write_text('# Title\n\n![cover](cover.png)\n\n```\nlast code line\n```\n\n<video src="clip.mp4"></video>\n\n![body](body.png)\n\n---\n')
        result = parser.parse_markdown_file(str(self.article))
        self.assertEqual(result['title'], 'Title')
        self.assertEqual([m['type'] for m in result['content_media']], ['video', 'image'])
        self.assertEqual(result['content_media'][0]['after_text'], 'last code line')
        self.assertEqual(result['missing_media'], 0)
        self.assertEqual(len(result['dividers']), 1)
        self.assertNotIn('___CODE_BLOCK_', result['html'])

    def test_same_anchor_video_order_and_idempotence(self):
        self.article.write_text('# Title\n\nAnchor paragraph\n\nTail\n')
        paths = {}
        items = []
        for index, token in enumerate(('one', 'two', 'three')):
            path = self.root / (token + '.mp4')
            path.write_bytes(b'fixture')
            paths[token] = path
            items.append(dict(token=token, root_index=index, anchor_text='Anchor paragraph'))
        count, errors = source.insert_videos_to_markdown(self.article, items, paths)
        self.assertEqual((count, errors), (3, []))
        text = self.article.read_text()
        self.assertLess(text.index('one.mp4'), text.index('two.mp4'))
        self.assertLess(text.index('two.mp4'), text.index('three.mp4'))
        self.assertLess(text.index('three.mp4'), text.index('Tail'))
        self.assertEqual(source.insert_videos_to_markdown(self.article, items, paths), (0, []))

    def test_callout_cleanup_preserves_lines(self):
        self.article.write_text('# Title\n\n> [!TIP]\n> first\n>\n> second\n')
        self.assertEqual(source.normalize_feishu_callouts(self.article), 1)
        result = parser.parse_markdown_file(str(self.article))
        self.assertIn('<blockquote>first<br><br>second</blockquote>', result['html'])
        self.assertNotIn('[!TIP]', self.article.read_text())

    def test_quote_body_marker_is_preserved(self):
        self.article.write_text('> ordinary quotation\n> Tip\n> final line\n')
        self.assertEqual(source.normalize_feishu_callouts(self.article), 0)
        self.assertIn('Tip', parser.markdown_to_html(self.article.read_text()))

    def test_direct_and_wrapped_video_files(self):
        dump = self.root / 'dump.json'
        blocks = [dict(block_id='root', children=['text', 'direct', 'view']),
                  dict(block_id='text', text={'elements': [{'text_run': {'content': 'Anchor'}}]}),
                  dict(block_id='direct', block_type=23, file={'token':'one','name':'one.mp4'}),
                  dict(block_id='view', block_type=33, children=['other','wrapped']),
                  dict(block_id='other', block_type=2),
                  dict(block_id='wrapped', block_type=23, file={'token':'two','name':'two.mp4'})]
        dump.write_text(json.dumps({'document': {'document_id':'root'}, 'blocks': blocks}))
        videos = source.extract_video_file_tokens_with_anchor(dump)
        self.assertEqual([v['token'] for v in videos], ['one','two'])
        self.assertEqual([v['anchor_text'] for v in videos], ['Anchor','Anchor'])

    def test_url_domain_boundary(self):
        self.assertTrue(source.is_feishu_url('https://team.feishu.cn/docx/abc'))
        self.assertTrue(source.is_feishu_url('https://team.larksuite.com/wiki/abc'))
        self.assertFalse(source.is_feishu_url('https://evilfeishu.cn/docx/abc'))
        self.assertFalse(source.is_feishu_url('https://feishu.cn.evil.example/docx/abc'))

    def test_missing_anchor_reports_error(self):
        self.article.write_text('# Title\n\nText\n')
        path = self.root / 'clip.mp4'
        path.write_bytes(b'fixture')
        count, errors = source.insert_videos_to_markdown(self.article, [dict(token='clip', anchor_text='Absent')], {'clip': path})
        self.assertEqual(count, 0)
        self.assertEqual(len(errors), 1)
        self.assertNotIn('<video', self.article.read_text())

    def make_media_article(self):
        for name, color in [('cover.png','white'), ('a.png','red'), ('b.png','blue')]:
            self.image(name, color)
        (self.root / 'clip.mp4').write_bytes(b'fixture')
        self.article.write_text('# Title\n\n![cover](cover.png)\n\n> quoted first\n>\n> quoted second\n\nAnchor\n\n![a](a.png)\n\n![b](b.png)\n\n<video src="clip.mp4"></video>\n')

    def test_optimized_paths_in_other_directory(self):
        self.make_media_article()
        output = self.root / 'other' / 'result.md'
        summary = optimizer.optimize(self.article, output, 2, 400, 10)
        result = parser.parse_markdown_file(str(output))
        self.assertEqual(summary['body_media_after'], 2)
        self.assertIn('<blockquote>quoted first<br><br>quoted second</blockquote>', result['html'])
        self.assertEqual(result['missing_media'], 0)
        self.assertEqual([m['type'] for m in result['content_media']], ['image', 'video'])
        self.assertEqual(Path(result['cover_image']).resolve(), (self.root / 'cover.png').resolve())

    def test_unmerged_paths_in_other_directory(self):
        self.make_media_article()
        output = self.root / 'other' / 'result.md'
        summary = optimizer.optimize(self.article, output, 24, 400, 10)
        self.assertFalse(summary['changed'])
        self.assertEqual(parser.parse_markdown_file(str(output))['missing_media'], 0)

    def test_no_crop_collage(self):
        image = self.image('tall.png', size=(20, 200))
        with Image.open(image) as im:
            im.putpixel((0, 0), (0, 255, 0))
            im.putpixel((19, 199), (0, 0, 255))
            im.save(image)
        output = self.root / 'collage.png'
        optimizer.make_collage([image], output, 100, 5)
        with Image.open(output) as im:
            colors = set(im.getdata())
        self.assertTrue(any(g > 50 for r, g, b in colors if r != 255))
        self.assertTrue(any(b > 50 for r, g, b in colors if r != 255))


if __name__ == '__main__':
    unittest.main()
