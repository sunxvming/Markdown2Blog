# ----- Imports ----- #

import os
import pkg_resources as pkg
import shutil
import markdown
from jinja2 import Template
from markdown.extensions.toc import TocExtension

# ----- Setup ----- #

_SCRIPT_TAG = '\n<script type="text/javascript" src="./{}"></script>'
_LINK_TAG = '<link rel="stylesheet" href="./{}">'

_TEMPLATE_DIR = 'templates'
_STATIC_DIR = 'static'
_TEMPLATES_PATH = pkg.resource_filename(__name__, _TEMPLATE_DIR)     # blog-engine-master\blog_engine\templates
_STATIC_PATH = pkg.resource_filename(__name__, _STATIC_DIR)
_BASE_TEMPLATE = os.path.join(_TEMPLATES_PATH, 'base.html')
_LIST_TEMPLATE = os.path.join(_TEMPLATES_PATH, 'list.html')

_SITE_DIR = 'site'


# ----- Functions ----- #

def _read_template(filename):

	"""Reads a Jinja2 template from file."""

	with open(filename, 'r', encoding="utf-8") as templ_file:
		template = Template(templ_file.read())

	return template


def _static_files(page, metadata):

	"""Adds links to static files (js, css) to the page."""

	head = ''

	if 'scripts' in metadata:

		for script in metadata['scripts']:
			page += _SCRIPT_TAG.format(script)

	if 'stylesheets' in metadata:

		for stylesheet in metadata['stylesheets']:
			head += _LINK_TAG.format(stylesheet)

	return head, page


def _render_page(input_file, output_file, template):

	"""Renders a markdown file to a given output file."""

	md = markdown.Markdown(extensions=['meta', 'def_list','fenced_code', 'codehilite',TocExtension(baselevel=3, title='内容纲要')])

	with open(input_file, 'r', encoding="utf-8") as f:
		page = md.convert(f.read())

	head, page = _static_files(page, md.Meta)
	title = md.Meta['title'][0] if 'title' in md.Meta else None

	rendered = template.render(content=page, title=title, head=head)

	with open(output_file, 'w',encoding="utf-8") as outf:
		outf.write(rendered)

	return title


def _build_article(file, parent_dir, build_dir, template):

	"""Builds an individual article."""
	name, extension = os.path.splitext(file)
	print("_build_article:",name)
	filename = name + '.md'
	pagename = name + '.html'
	filepath = os.path.join(parent_dir, filename)
	build_file = os.path.join(build_dir, pagename)


	article_name = _render_page(filepath, build_file, template)

	return {'name': name, 'link': pagename}


def _remove_build(build_dir):

	"""Wipes the previous build directory."""

	try:
		shutil.rmtree(build_dir, ignore_errors = True)
		dir = os.path.join(build_dir, "articles")
		os.makedirs(dir)
	except FileNotFoundError:
		print(FileNotFoundError)


# ----- Engine Class ----- #

class Engine():

	"""The main Engine object, used to generate the static site from source."""

	_articles_build_dir = 'articles'
	_articles_url = '/' + _articles_build_dir + '/'
	_articles_src_dir = 'articles'

	def __init__(self, src='in', build='out'):

		"""Sets up source and build directories."""

		self._src = src
		self._build = build

	def _read_templates(self, base_template, list_template):

		"""Reads the site templates in from file."""

		self._base_template = _read_template(base_template or _BASE_TEMPLATE)
		self._list_template = _read_template(list_template or _LIST_TEMPLATE)

	def _build_list(self, articles):

		"""Builds the articles list from template."""
		
		content = self._list_template.render(articles=articles)
		rendered = self._base_template.render(content=content,
			title='Article List', head='')

		output_file = os.path.join(self._build, 'list.html')

		with open(output_file, 'w', encoding="utf-8") as outf:
			outf.write(rendered)

	def _build_articles(self):

		"""Builds all the articles in the static site."""

		articles_src_dir = os.path.join(self._src, self._articles_src_dir)
		articles_build_dir = os.path.join(self._build, self._articles_build_dir)

		articles = []

		for file in os.scandir(articles_src_dir):

			info = _build_article(file.name, articles_src_dir, articles_build_dir,
				self._base_template)

			info['link'] = self._articles_url + info['link']
			articles.append(info)

		return articles

	def _build_site(self):

		"""Builds any general site pages (e.g. index, about)."""

		site_path = os.path.join(self._src, _SITE_DIR)

		if os.path.isdir(site_path):

			for file in os.scandir(site_path):

				filename, extension = os.path.splitext(file.name)

				if extension == '.md':

					out_file = os.path.join(self._build, filename + '.html')
					_render_page(file.path, out_file, self._base_template)

				else:

					shutil.copy(file.path, self._build)

	@property
	def articles_build_dir(self):

		"""Getter for the articles build directory."""

		return self._articles_build_dir

	@articles_build_dir.setter
	def articles_build_dir(self, value):

		"""Sets the name in the build directory for articles."""

		self._articles_build_dir = value
		self._articles_url = '/' + value + '/'

	@property
	def articles_src_dir(self):

		"""Getter for the articles src directory."""

		return self._articles_src_dir

	@articles_src_dir.setter
	def articles_src_dir(self, value):

		"""Sets the name in the src directory for articles."""

		self._articles_src_dir = value

	def build(self, base_template=None, list_template=None):

		"""Builds the static site, saves to build directory."""

		_remove_build(self._build)
		self._read_templates(base_template, list_template)

		shutil.copytree(_STATIC_PATH, self._build, dirs_exist_ok=True)
		self._build_site()

		articles = self._build_articles()
		self._build_list(articles)
