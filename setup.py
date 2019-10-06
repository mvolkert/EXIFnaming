import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="EXIFnaming",
    version="0.0.1",
    author="Marco Volkert",
    author_email="marco.volkert24@gmx.de",
    description="collection of Tag operations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MarcoVolkert/EXIFnaming",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)