# Will be used if the solution is exported as a package
from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = ["ipython>=6", "nbformat>=4", "nbconvert>=5", "requests>=2"]

setup(
    name="ett_utils",
    version="0.0.1",
    author="",
    author_email="",
    description="A package of tools to solve the examination timetabling problem",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
    ],
)