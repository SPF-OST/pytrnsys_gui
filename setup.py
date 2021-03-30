import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytrnsys_gui",
    author="Stefano Marti",
    author_email="stefano-marti@spf.ch",
    description="A GUI for Trnsys",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/pypa/sampleproject",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["pytrnsys", "PyQT5", "matplotlib", "numpy", "pandas", "bokeh"],
    setup_requires=["setuptools-git-versioning"],
    python_requires=">=3.5",
)
