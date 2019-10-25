import setuptools

with open("README.md", "r") as file:
    long_description = file.read()

setuptools.setup(
    name="EXIFnaming",
    version="PYPIVERSION",
    author="Marco Volkert",
    author_email="marco.volkert24@gmx.de",
    description="Tools for organizing and tagging photos",
    long_description=long_description,
    long_description_content_type="text/markdown",
    license='MIT License',
    url="https://github.com/mvolkert/EXIFnaming",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Development Status :: 3 - Alpha",
        "Topic :: Multimedia :: Graphics :: Capture :: Digital Camera",
        "Topic :: Utilities",
        "Intended Audience :: Developers",
        "Intended Audience :: Other Audience",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Operating System :: Microsoft :: Windows :: Windows 10",
        "Natural Language :: English",
        "Natural Language :: German",
        "Typing :: Typed",
    ],
    keywords='exif exiftool photo tagging geotagging renaming photo-mode ordering python ' +
             'lumix panasonic camera digital-camera photos camera-model TZ101 organizing',
    python_requires='>=3.6',
    dependency_links=['https://sno.phy.queensu.ca/~phil/exiftool/'],
    install_requires=['numpy', 'sortedcollections', 'scikit-image', 'opencv-python', 'Pillow', 'googlemaps'],
)
