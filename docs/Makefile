# Sphinx documentation — https://www.sphinx-doc.org/
SPHINXOPTS    ?=
SPHINXBUILD  ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

.PHONY: help openapi html clean

help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

# OpenAPI 3 YAML: корень репозитория (schema.yml) + копия для Sphinx
openapi:
	@mkdir -p _static
	cd .. && python manage.py spectacular --color --file schema.yml && cp schema.yml docs/_static/schema.yml

html: openapi
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)

clean:
	@$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS)
