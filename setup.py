import setuptools

setuptools.setup(
    name="timequota",
    version="0.0.2",
    author="AravRS",
    description="Limit the time of your script",
    long_description=open("README.md").read() + "\n\n" + open("CHANGELOG.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/AravRS/timequota",
    license="MIT",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=["numpy", "prettytable"],
)