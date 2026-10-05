"""Use ReportLab 4's pure Python PDF engine instead of p4a's legacy C recipe."""
from pathlib import Path

from pythonforandroid.recipe import PythonRecipe


class ReportLabRecipe(PythonRecipe):
    version = '4.4.9'
    url = ('https://files.pythonhosted.org/packages/1a/39/'
           '42cf24aee570a80e1903221ae3a92a2e34c324794a392eb036cbb6dc3839/'
           'reportlab-{version}.tar.gz')
    sha256sum = '7cf487764294ee791a4781f5a157bebce262a666ae4bbb87786760a9676c9378'
    depends = ['setuptools', 'pillow']
    python_depends = ['charset-normalizer']
    call_hostpython_via_targetpython = False

    def prebuild_arch(self, arch):
        super().prebuild_arch(arch)
        root = Path(self.get_build_dir(arch.arch))
        # The app embeds DejaVu fonts; no optional font downloads or GPL font needed.
        for path in (root / 'src' / 'reportlab' / 'fonts').glob('DarkGarden*'):
            path.unlink()
        setup = root / 'setup.py'
        source = setup.read_text()
        source = source.replace("dlt1 = not specialOption('--no-download-t1-files')", 'dlt1 = False')
        setup.write_text(source)


recipe = ReportLabRecipe()
