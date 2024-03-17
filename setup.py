# -*- coding: utf-8 -*-
import os
import re

from setuptools import find_packages, setup  # type: ignore


def get_version() -> str:
    path = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), "lagrange", "__init__.py"
    )
    with open(path, "r", encoding="utf-8") as f:
        data = f.read()
    result = re.findall(r"(?<=__version__ = \")\S+(?=\")", data)
    return result[0]


def get_dis():
    with open("README.markdown", "r", encoding="utf-8") as f:
        return f.read()


packages = find_packages(exclude=("test", "tests.*", "test*"))


def main():
    version = get_version()

    dis = get_dis()
    setup(
        name="lagrange-python",
        version=version,
        url="https://github.com/LagrangeDev/lagrange-python",
        packages=packages,
        keywords=["asyncio", "NT", "QQ"],
        description="An Python Implementation of NTQQ PC Protocol",
        long_description_content_type="text/markdown",
        long_description=dis,
        author="synodriver",
        author_email="diguohuangjiajinweijun@gmail.com",
        maintainer="linwenxuan05",
        python_requires=">=3.8",
        install_requires=["typing-extensions", "cryptography", "ftea>=0.1.5"],
        license="GPLv3",
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Framework :: AsyncIO",
            "Operating System :: OS Independent",
            "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
            "Programming Language :: Python",
            "Programming Language :: Python :: 3.8",
            "Programming Language :: Python :: 3.9",
            "Programming Language :: Python :: 3.10",
            "Programming Language :: Python :: 3.11",
            "Programming Language :: Python :: 3.12",
            "Programming Language :: Python :: Implementation :: CPython",
        ],
        include_package_data=True,
    )


if __name__ == "__main__":
    main()