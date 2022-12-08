from distutils.core import setup

setup(name="Spotdj",
      version="0.1.0",
      packages=["spotdj"],
      install_requires=[
            "spotdl",
            "ffmpeg-python",
            "colorama",
            "rymscraper @ git+ssh://git@github.com/dbeley/rymscraper.git"
      ],
      )
