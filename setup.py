from setuptools import setup


def readme():
    with open("README.rst") as f:
        return f.read()


setup(
    name="ijmfttxt",
    version="1.7.1",
    description="Erweiterung zu ftrobopy",
    long_description_content_type="text/x-rst",
    long_description=readme(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Education",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.9",
        "Topic :: Education",
    ],
    keywords="ftrobopy fischertechnik txt ijm",
    url="https://github.com/IJMTutorSES/ijmfttxt",
    author="Sebastian Specht",
    author_email="s.specht@ijm-online.de",
    license="MIT",
    packages=["ijmfttxt", "ijmfttxt/ftrobopy"],
    install_requires=[
        "pynput",
    ],
    include_package_data=True,
    zip_safe=False,
)
