from distutils.core import setup

setup(name="Spotdj",
      version="0.1.0",
      packages=["spotdj"],
      install_requires=[
            "spotdl",
            "ffmpeg-python",
            "colorama",
            "rymscraper @ git+https://github.com/dbeley/rymscraper.git@14708474abcea8ce91c83a0debf934bd37d19a8e"
      ],
      )
