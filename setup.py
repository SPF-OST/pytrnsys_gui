import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytrnsys-gui",
    author="Martin Neugebauer",
    version_config=True,
    author_email="martin.neugebauer@ost.ch",
    description="A GUI for Trnsys",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SPF-OST/pytrnsys",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "pytrnsys",
        "PyQT5",
        "matplotlib",
        "numpy",
        "pandas",
        "bokeh",
        "appdirs",
    ],
    setup_requires=["setuptools-git-versioning"],
    python_requires=">=3.9",
)
