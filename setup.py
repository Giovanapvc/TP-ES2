# setup.py
from setuptools import setup

setup(
    name="tpes2",
    version="0.1",
    py_modules=["cli", "entities", "export_html", "repo", "service"],
    install_requires=[
        "click",      # se usar click
        # outras libs que seu código precisa
    ],
)
