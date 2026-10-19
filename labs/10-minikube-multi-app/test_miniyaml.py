"""Tests for miniyaml.py, so it can be trusted when it vouches for the manifests."""
import unittest

from miniyaml import load_all


class MiniYamlTests(unittest.TestCase):
    def test_scalars_and_types(self):
        doc, = load_all("a: 1\nb: -2\nc: true\nd: false\ne: text\nf: \"80\"\ng: 'x y'\n")
        self.assertEqual(doc, {"a": 1, "b": -2, "c": True, "d": False, "e": "text",
                               "f": "80", "g": "x y"})

    def test_nested_maps(self):
        doc, = load_all("a:\n  b:\n    c: 1\n  d: 2\ne: 3\n")
        self.assertEqual(doc, {"a": {"b": {"c": 1}, "d": 2}, "e": 3})

    def test_sequence_of_scalars(self):
        doc, = load_all("a:\n  - x\n  - 2\n  - \"--save\"\n")
        self.assertEqual(doc, {"a": ["x", 2, "--save"]})

    def test_sequence_of_maps_with_nested_content(self):
        text = ("ports:\n"
                "  - name: web\n"
                "    containerPort: 80\n"
                "    probe:\n"
                "      path: /health\n"
                "  - name: db\n"
                "    containerPort: 5432\n"
                "after: 1\n")
        doc, = load_all(text)
        self.assertEqual(doc["ports"][0], {"name": "web", "containerPort": 80,
                                           "probe": {"path": "/health"}})
        self.assertEqual(doc["ports"][1]["containerPort"], 5432)
        self.assertEqual(doc["after"], 1)

    def test_sequence_at_same_indent_as_key(self):
        doc, = load_all("a:\n- x\n- y\nb: 1\n")
        self.assertEqual(doc, {"a": ["x", "y"], "b": 1})

    def test_documents_and_comments(self):
        docs = load_all("# header\na: 1\n---\n# only a comment\n---\nb: 2\n")
        self.assertEqual(docs, [{"a": 1}, {"b": 2}])

    def test_values_containing_colons_and_slashes(self):
        doc, = load_all("image: lab10/app:1.0\nkey: kubernetes.io/hostname\n")
        self.assertEqual(doc, {"image": "lab10/app:1.0", "key": "kubernetes.io/hostname"})

    def test_empty_value_is_none(self):
        self.assertEqual(load_all("a:\nb: 1\n"), [{"a": None, "b": 1}])

    def test_rejects_unsupported_or_malformed_input(self):
        for bad in ("a: {b: 1}\n", "a: &x 1\n", "a: |\n  text\n", "a: 1 # note\n",
                    "a:\tb\n", "a: \"open\n", "a: 1\na: 2\n", "a: 1\n   b: 2\n",
                    "just text\n"):
            with self.assertRaises(ValueError, msg=repr(bad)):
                load_all(bad)

    def test_whole_k8s_directory_parses(self):
        import pathlib
        files = sorted((pathlib.Path(__file__).parent / "k8s").glob("*.yaml"))
        self.assertGreaterEqual(len(files), 4)
        for path in files:
            self.assertTrue(load_all(path.read_text(encoding="utf-8")), path.name)


if __name__ == "__main__":
    unittest.main()
