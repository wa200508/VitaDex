"""Keep p4a's pinned recipe, using FreeType's official SourceForge mirror."""

from pythonforandroid.recipes.freetype import FreetypeRecipe


class MirroredFreetypeRecipe(FreetypeRecipe):
    url = (
        'https://downloads.sourceforge.net/project/freetype/'
        'freetype2/{version}/freetype-{version}.tar.xz'
    )
    # Published in Buildroot 2020.02.1 package/freetype/freetype.hash.
    sha256sum = '16dbfa488a21fe827dc27eaf708f42f7aa3bb997d745d31a19781628c36ba26f'


recipe = MirroredFreetypeRecipe()
