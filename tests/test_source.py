# Copyright 2014, 2015 Christoph Reiter
#                 2020 Nick Boultbee
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.

import os
import re
from typing import List, Iterable, Pattern

import pytest
from gi.repository import Gtk
from pytest import fixture

from quodlibet.util import get_module_dir
from tests.test_po import QL_BASE_DIR


def iter_py_paths():
    """Iterates over all Python source files that are part of Quod Libet"""

    import quodlibet
    root = os.path.dirname(get_module_dir(quodlibet))

    skip = [
        os.path.join(root, "build"),
        os.path.join(root, "dist"),
        os.path.join(root, "docs"),
        os.path.join(root, "dev-utils"),
        os.path.join(root, "quodlibet", "packages"),
    ]
    for dirpath, dirnames, filenames in os.walk(root):
        for dirname in dirnames:
            if dirname.startswith("."):
                dirnames.remove(dirname)
        if any((dirpath.startswith(s + os.sep) or s == dirpath)
               for s in skip):
            continue

        for filename in filenames:
            if filename.endswith('.py'):
                yield os.path.join(dirpath, filename)


def prettify_path(s: str) -> str:
    return os.path.splitext(os.path.relpath(s, QL_BASE_DIR))[0]


@pytest.fixture(params=list(iter_py_paths()), ids=prettify_path)
def py_path(request):
    return request.param


class TestLicense:
    ALLOWED_RAW = ["""
This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.
""", """
Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the
"Software"), to deal in the Software without restriction, including
without limitation the rights to use, copy, modify, merge, publish,
distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to
the following conditions:

The above copyright notice and this permission notice shall be included
in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""]
    ALLOWED = ["".join(license.split()) for license in ALLOWED_RAW]

    def test_license_is_compliant(self, py_path):
        header = b""
        with open(py_path, "rb") as h:
            for line in h:
                line = line.strip()
                if not line.startswith(b"#"):
                    break
                header += line.lstrip(b"# ") + b"\n"

        norm = b"".join(header.split())
        norm = norm.decode("utf-8")
        assert any([l in norm for l in self.ALLOWED])


class TestStockIcons:
    @fixture
    def res(self) -> Iterable[Pattern]:
        return [re.compile(r)
                for r in ("(Gtk\\.STOCK_[_A-Z]*)",
                          "[\"\'](gtk-[\\-a-z]*)")]

    @fixture
    def white(self) -> List[str]:
        # gtk setting keys start like stock icons, so white list them
        white = [x.replace("_", "-") for x in
                 dir(Gtk.Settings.get_default().props)
                 if x.startswith("gtk_")]
        # older gtk doesn't have those, but we still have them in the source
        white += ["gtk-dialogs-use-header",
                  "gtk-primary-button-warps-slider"]
        # some more..
        white += ["gtk-tooltip", "gtk-", "gtk-update-icon-cache-"]
        return white

    def test_icons_used(self, py_path, res, white):
        if py_path.endswith(("icons.py", "test_source.py")):
            return
        with open(py_path, "rb") as h:
            data = h.read().decode("utf-8")
            for r in res:
                match = r.search(data)
                if match:
                    group = match.group(1)
                    assert group in white