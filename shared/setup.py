from setuptools import setup, find_packages

setup(
    name="api-management-shared",
    version="1.0.0",
    description="Shared utilities for API Management microservices",
    packages=find_packages(),
    install_requires=[
        "Django>=4.2.0",
        "djangorestframework>=3.14.0",
        "requests>=2.28.0",
        "grpcio>=1.71.0",
        "protobuf<6.0dev,>=5.26.1",
    ],
    python_requires=">=3.11",
    zip_safe=False,
)