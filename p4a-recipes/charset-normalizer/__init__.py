"""Force portable Python; pip's host Linux wheels cannot run on Android."""
from pythonforandroid.recipe import PythonRecipe


class CharsetNormalizerRecipe(PythonRecipe):
    version = '3.4.4'
    url = ('https://files.pythonhosted.org/packages/13/69/'
           '33ddede1939fdd074bce5434295f38fae7136463422fe4fd3e0e89b98062/'
           'charset_normalizer-{version}.tar.gz')
    sha256sum = '94537985111c35f28720e43603b8e7b43a6ecfb2ce1d3058bbe955b73404e21a'
    depends = ['setuptools']
    site_packages_name = 'charset_normalizer'
    call_hostpython_via_targetpython = False

    def get_recipe_env(self, arch=None, **kwargs):
        env = super().get_recipe_env(arch, **kwargs)
        env['CHARSET_NORMALIZER_USE_MYPYC'] = '0'
        return env


recipe = CharsetNormalizerRecipe()
