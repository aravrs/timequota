import setuptools

setuptools.setup(
    name="timequota",
    version="0.0.6",
    author="AravRS",
    description="Manage the time of your script",
    long_description=open("PyPI.md").read(),
    long_description_content_type="text/markdown",
    url="https://aravrs.github.io/timequota",
    project_urls={
        "Source": "https://github.com/AravRS/timequota",
        "Documentation": "https://aravrs.github.io/timequota/timequota",
        "Changelog": "https://github.com/aravrs/timequota/blob/main/CHANGELOG.md",
    },
    license="MIT",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "colorama",
        "tabulate",
        "typeguard",
    ],
)
