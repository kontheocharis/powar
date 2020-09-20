import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="powar",
    version="1.0.3",
    author="Constantine Theocharis",
    author_email="kontheocharis@gmail.com",
    description="A configuration manager unlike any other!",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kontheocharis/powar",
    packages=setuptools.find_packages(),

    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Unix",
    ],
    python_requires='>=3.6',
    install_requires=open('requirements.txt').read().splitlines(),
    entry_points={
        'console_scripts': [
            'powar=powar.main:main',
        ],
    },
)
