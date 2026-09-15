"""测试包：包模式下（`python -m unittest tests.test_x`）钉住基准配置。

`unittest discover -s tests` 是以顶层模块方式导入的，不会执行本文件；
那种方式下由各测试文件顶部的 ``import _baseline`` 完成钉住。
"""

from . import _baseline  # noqa: F401  导入即执行 pin()
