import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

from distutils.core import setup
setuptools.setup(
    name="pyvmodule",
    version="2.0.5",
    author="H.Z.Tan",
    author_email="tanhongze@loongson.cn",
    description="pyvmodule:an advanded verilog coding toolkit",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tanhongze/pyvmodule",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)

