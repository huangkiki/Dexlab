"""Reading routes must stay local without changing pinned source evidence."""

import unittest

from scripts.learning_docs import load_sources, prepare_markdown, rewrite_url


class LearningDocsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = load_sources()
        cls.sim = next(item for item in cls.sources if item['slug'] == 'sim')
        cls.mujoco = next(item for item in cls.sources if item['slug'] == 'mujoco')

    def test_course_navigation_is_local_but_pinned_citations_stay_exact(self):
        path = 'docs/solver-guide/03-friction.md'
        local = rewrite_url('https://github.com/huangkiki/mujoco-learning/blob/main/docs/contact-models.md',
                            self.sim, path, self.sources)
        self.assertEqual(local, '../../../mujoco/docs/contact-models.md')
        historical = 'https://github.com/huangkiki/mujoco-learning/blob/1082e1281acbf405f3483a79576cde4d755dc87a/docs/solver-reading-guide.md'
        self.assertEqual(rewrite_url(historical, self.sim, path, self.sources), historical)

    def test_relative_chapters_and_directory_links_keep_anchors(self):
        self.assertEqual(rewrite_url('02-contact.md#法向', self.sim, 'docs/solver-guide/03-friction.md', self.sources),
                         '02-contact.md#法向')
        self.assertEqual(rewrite_url('https://github.com/huangkiki/sim-learning/tree/main/docs/solver-guide',
                                    self.mujoco, 'docs/guide.md', self.sources), '../../sim/docs/solver-guide/README.md')

    def test_code_examples_are_not_rewritten_as_reading_links(self):
        url = 'https://github.com/huangkiki/mujoco-learning/blob/main/docs/contact-models.md'
        example = f'```python\nexample = "[read]({url}) $`x`$"\n```'
        text = f'[read]({url})\n\n$`x^2`$\n\n{example}\n\n```math\nx^2\n```'
        rendered = prepare_markdown(text, self.sim, 'docs/foundations.md', self.sources)
        self.assertIn('[read](../../mujoco/docs/contact-models.md)', rendered)
        self.assertIn('$x^2$', rendered)
        self.assertIn(example, rendered)
        self.assertIn('```{math}\nx^2', rendered)

    def test_source_code_links_are_frozen_instead_of_becoming_broken_pages(self):
        url = rewrite_url('../examples/contact-solvers/check.py', self.mujoco, 'docs/guide.md', self.sources)
        self.assertEqual(url, f'https://github.com/huangkiki/mujoco-learning/blob/{self.mujoco["revision"]}/examples/contact-solvers/check.py')


if __name__ == '__main__':
    unittest.main()
