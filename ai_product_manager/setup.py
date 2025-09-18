from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ai-product-manager",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="An autonomous AI system that performs product management tasks",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/ai-product-manager",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        'ai_product_manager': [
            'alembic.ini',
            'alembic/env.py',
            'alembic/versions/*.py',
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.8',
    install_requires=[
        'python-dateutil>=2.8.2',
        'requests>=2.28.1',
        'alembic>=1.13.1',
    ],
    extras_require={
        'dev': [
            'pytest>=7.0.0',
            'pytest-cov>=3.0.0',
            'pandas>=1.5.0',
            'matplotlib>=3.6.0',
            'nltk>=3.7',
            'spacy>=3.4.0',
            'flask>=2.1.0',
            'streamlit>=1.10.0',
        ],
    },
    entry_points={
        'console_scripts': [
            'ai-pm=ai_product_manager.__main__:main',
            'ai-pm-agent=ai_product_manager.agent:main',
            'ai-pm-db=ai_product_manager.tools.migrate:main',
        ],
    },
)
