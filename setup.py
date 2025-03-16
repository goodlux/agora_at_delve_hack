from setuptools import setup, find_packages

setup(
    name="agora_at",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "pydantic>=2.0.0",
        "pytest>=7.0.0",
    ],
    author="",
    author_email="",
    description="Integration between Agora Protocol and AT Protocol",
    keywords="agora, atproto, agents, decentralized, social",
    url="",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.9",
)
