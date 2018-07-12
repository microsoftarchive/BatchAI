import os
from setuptools import setup


def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name="azure-batchai-utils",
    version="0.1",
    author="Microsoft Corporation",
    license="MIT",
    description="A collection of tools for creating and monitoring jobs using "
                "the Azure Batch AI Python SDK.",
    packages=["azure-batchai-utils"],
    install_requires=["future",
                      "six",
                      "jsonschema",
                      "requests",
                      "numpy",
                      "azure",
                      "azure-mgmt-batchai"],
    long_description=read("README.md")
)
