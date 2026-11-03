"""Mobile entry point and desktop development launcher."""
import os
os.environ['KIVY_INSPECTOR'] = '0'

from application import VitaDexApp

__all__ = ['VitaDexApp']

if __name__ == '__main__':
    VitaDexApp().run()
