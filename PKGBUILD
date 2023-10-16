pkgname=python-venv-gui
pkgver=1.1
pkgrel=1
pkgdesc="Crear Entornos Virtuales(venv) De Python."
arch=('any')
url="https://github.com/krafairus/python-venv-gui"
license=('MIT')
depends=('python' 'python-pyqt5' 'xdg-utils')

source=("python-venv-gui.py"
        "python-venv-gui.desktop"
        "python-venv-gui.svg"
        "icons.tar.gz")

sha256sums=('9f559442dd8f3b20994059c5d17815c6826f6372eb598973fcf3e1a3a8662dcd'
            '2143055516c7b557b69ee19895451e48a5c6504c270643074c1f8fda65c45779'
            '85baebeaee8557e8c7b7037eab68df6da2e0f8c3d4531fdc4a61fa4184ff5200'
            'e67b90d7f4db35545456c5c4fc8baa2e9588b04e9e2c0ed6a895c88b5a262aef')

package() {
  cd "$srcdir"
  install -d "$pkgdir/usr/bin/python-venv-gui"
  install -d "$pkgdir/usr/bin/python-venv-gui/icons"
  cp -r "$srcdir/icons/"* "$pkgdir/usr/bin/python-venv-gui/icons/"
  install -Dm644 python-venv-gui.desktop "$pkgdir/usr/share/applications/python-venv-gui.desktop"
  install -Dm644 python-venv-gui.svg "$pkgdir/usr/share/icons/hicolor/scalable/apps/python-venv-gui.svg"
  install -Dm644 python-venv-gui.py "$pkgdir/usr/bin/python-venv-gui/python-venv-gui.py"

}
