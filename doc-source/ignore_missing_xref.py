# 3rd party
from docutils import nodes
from sphinx.application import Sphinx
from sphinx.errors import NoUri


def handle_missing_xref(app: Sphinx, env, node: nodes.Node, contnode: nodes.Node) -> None:
	if node.get("reftarget", '').startswith("dulwich."):
		raise NoUri


def setup(app: Sphinx):
	app.connect("missing-reference", handle_missing_xref, priority=950)
