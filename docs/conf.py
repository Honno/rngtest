import os

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.coverage",
    "sphinx.ext.doctest",
    "sphinx.ext.extlinks",
    "sphinx.ext.ifconfig",
    "sphinx.ext.napoleon",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    "sphinx_click.ext",
]
source_suffix = ".rst"
master_doc = "index"
project = "coinflip"
year = "2020"
author = "Matthew Barber"
copyright = "{0}, {1}".format(year, author)
version = release = "version = release = '0.0.2'"

pygments_style = "trac"
templates_path = ["."]
extlinks = {
    "issue": ("https://github.com/Honno/coinflip/issues/%s", "#"),
    "pr": ("https://github.com/Honno/coinflip/pull/%s", "PR #"),
}

on_rtd = os.environ.get("READTHEDOCS", None) == "True"
if not on_rtd:  # set the theme if we're building docs locally
    html_theme = "sphinx_rtd_theme"

html_use_smartypants = True
html_last_updated_fmt = "%b %d, %Y"
html_split_index = False
html_sidebars = {
    "**": ["searchbox.html", "globaltoc.html", "sourcelink.html"],
}
html_short_title = "%s-%s" % (project, version)

napoleon_use_ivar = True
napoleon_use_rtype = False
napoleon_use_param = False
