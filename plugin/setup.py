from setuptools import setup

setup(
      name    = "renpy_editra",    # Plugin Name
      version = "6.14",   # Plugin Version
      description = "Ren'Py Support for Editra",   # Short plugin description
      author = "Tom Rothamel",     # Your Name
      author_email = "pytom@bishoujo.us",  # Your contact
      license = "MIT",       # Plugins licensing info
      packages = [ 'renpy_editra', 'json' ],
      zip_safe = False,
      entry_points = '''
      [Editra.plugins]
      renpy_editra = renpy_editra:RenpyPlugin
      '''
     )
