from setuptools import setup, find_packages

setup(
    name="beanstack",
    version="0.1.0",
    description="A brief description of your package",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    author="Ricardo Walford",
    author_email="ricardo.walford@gmail.com",
    url="https://github.com/riky126/beanstack",
    packages=find_packages(),  # Automatically finds `my_package` and sub-packages
    install_requires=[
        # "requests",  # Example dependencies
        # "numpy",
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
)

# python setup.py bdist_wheel