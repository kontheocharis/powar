import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="powar",
    version="1.0.0",
    author="Constantine Theocharis",
    author_email="kontheocharis@gmail.com",
    description="A configuration manager unlike any other!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kontheocharis/powar",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
    ],
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'powar=powar.main:main',
        ],
    },
)
