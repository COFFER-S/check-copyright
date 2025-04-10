# 1. 项目：
提交时自动检查 License 格式并自动修改。

# 2. 功能目标：
<font style="color:rgb(23, 43, 77);">1. 检查代码文件中是否缺失 License head（可自动补全）

</font><font style="color:rgb(23, 43, 77);">2. 检查 copyright 年份是否正确

</font><font style="color:rgb(23, 43, 77);">3. 实现 pre-commit hook

</font><font style="color:rgb(23, 43, 77);">4. 支持 replace 参数

</font><font style="color:rgb(23, 43, 77);">5. 支持 ignore 忽略文件

</font><font style="color:rgb(23, 43, 77);">6. 不同目录下的文件可使用不同的 License（a: 符合就近原则; b: config.yaml 文件中的 config 覆盖上方的 config）

</font><font style="color:rgb(23, 43, 77);">7. 检查 LICENSE 文件

</font><font style="color:rgb(23, 43, 77);">8. 非开源代码使用特定的 License</font>

# 3. License 格式
```plain
/*
 * Espressif Modified MIT License
 *
 * Copyright (c) 2025 Espressif Systems (Shanghai) CO., LTD
 *
 * Permission is hereby granted for use EXCLUSIVELY with Espressif Systems products.
 * This includes the right to use, copy, modify, merge, publish, distribute, and sublicense
 * the Software, subject to the following conditions:
 *
 * 1. This Software MUST BE USED IN CONJUNCTION WITH ESPRESSIF SYSTEMS PRODUCTS.
 * 2. The above copyright notice and this permission notice shall be included in all copies
 *    or substantial portions of the Software.
 * 3. Redistribution of the Software in source or binary form FOR USE WITH NON-ESPRESSIF PRODUCTS
 *    is strictly prohibited.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
 * INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
 * PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
 * FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
 * OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
 * DEALINGS IN THE SOFTWARE.
 *
 * SPDX-License-Identifier: LicenseRef-Espressif-Modified-MIT
 */
```

<font style="color:rgb(23, 43, 77);">如果仓库有一个正式的许可文件，比如在代码库的根目录添加完整的 LICENSE 文件，使用时可在代码文件中添加如下简要说明：</font>

```plain
/*
 * SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO., LTD
 * SPDX-License-Identifier: LicenseRef-Espressif-Modified-MIT
 *
 * See LICENSE file for details.
 */
```

<font style="color:rgb(23, 43, 77);">对于 examples 与 test_apps 中的*</font><font style="color:#FF0000;">开源代码</font><font style="color:rgb(23, 43, 77);">*使用如下License：</font>

```plain
/*
 * SPDX-FileCopyrightText: 2025 Espressif Systems (Shanghai) CO., LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */
```

<font style="color:rgb(23, 43, 77);">LICENSE 文件参考格式如下：</font>

```plain
Espressif Modified MIT License

Copyright (c) 2025 Espressif Systems (Shanghai) CO., LTD

Permission is hereby granted for use EXCLUSIVELY with Espressif Systems products.
This includes the right to use, copy, modify, merge, publish, distribute, and sublicense
the Software, subject to the following conditions:

1. This Software MUST BE USED IN CONJUNCTION WITH ESPRESSIF SYSTEMS PRODUCTS.
2. The above copyright notice and this permission notice shall be included in all copies
or substantial portions of the Software.
3. Redistribution of the Software in source or binary form FOR USE WITH NON-ESPRESSIF PRODUCTS
is strictly prohibited.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.

SPDX-License-Identifier: LicenseRef-Espressif-Modified-MIT
```

# 4. 项目结构
```bash
check-copyright
├── check_copyright_config.yaml  # 配置文件
├── check_copyright.py           # 工具脚本
├── LICENSE                      # 许可证
├── README.md                    # 说明
└── setup.py                     # 程序入口
```

# 5. 参数设计
```bash
usage: check_copyright.py [-h] [--config CONFIG] [--replace] files [files ...]

Check the copyright declaration of newly added files in the current commit.

positional arguments:
  files            Input file list

options:
  -h, --help       show this help message and exit
  --config CONFIG  Configuration file path
  --replace        Enable replacement functionality
```

位置参数：

+ files <文件路径>
    - 直接在`python check_copyright.py`后添加文件或文件夹路径即可。

可选参数：

+ --config <配置文件路径>
    - 需要在 `python check_copyright.py --config`后添加 config.yaml(配置文件路径)
+ --replace，表示直接帮助用户修改
    - `python check_copyright.py --replace`

# 6. check_copyright_config.yaml 规则
1. 默认使用 DEFAULT config
2. 下方追加的 config 可根据 include 路径覆盖 DEFAULT config
3. 缺省的关键字默认使用 DEFAULT config
4. ignore 中配置跳过许可证检查路径

```yaml
DEFAULT:  # 默认 license 配置
  allowed_licenses:
    - Espressif Modified MIT
    - Espressif-Modified-MIT
  license_for_new_files: Espressif Modified MIT  # 新增文件使用的许可证
  espressif_copyright_full: |
     /*
      * {license} License
      *
      * Copyright (c) {year} Espressif Systems (Shanghai) CO., LTD
      *
      * Permission is hereby granted for use EXCLUSIVELY with Espressif Systems products.
      * This includes the right to use, copy, modify, merge, publish, distribute, and sublicense
      * the Software, subject to the following conditions:
      *
      * 1. This Software MUST BE USED IN CONJUNCTION WITH ESPRESSIF SYSTEMS PRODUCTS.
      * 2. The above copyright notice and this permission notice shall be included in all copies
      *    or substantial portions of the Software.
      * 3. Redistribution of the Software in source or binary form FOR USE WITH NON-ESPRESSIF PRODUCTS
      *    is strictly prohibited.
      *
      * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
      * INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR
      * PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE
      * FOR ANY CLAIM, DAMAGES, OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
      * OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
      * DEALINGS IN THE SOFTWARE.
      *
      * SPDX-License-Identifier: LicenseRef-Espressif-Modified-MIT
      */
  espressif_copyright_short: |
    /*
     * SPDX-FileCopyrightText: {year} Espressif Systems (Shanghai) CO., LTD
     * SPDX-License-Identifier: LicenseRef-Espressif-Modified-MIT
     *
     * See LICENSE file for details.
     */


examples_and_test_apps:  # example 与 test_apps 使用不同于 DEFAULT 的 Apache-2.0 许可，覆盖上方键值对
  include:  # 作用的路径
   - '**/examples/basic_examples/**'
   - '**/test_apps/**'
  allowed_licenses:
    - Apache-2.0
  license_for_new_files: Apache-2.0
  espressif_copyright_full: |
    /*
     * SPDX-FileCopyrightText: {year} Espressif Systems (Shanghai) CO., LTD
     *
     * SPDX-License-Identifier: {license}
     */
  espressif_copyright_short: ''

ignore:  # 跳过许可证检查的配置
  include:
    - '**/esp_gmf_queue.h'
    - '**/managed_components/**'
    - '**/build/**'
    - '**/examples/esp_audio_simple_player/test_apps/main/aud_simp_player_test.c'
    - '**/examples/esp_audio_simple_player/test_apps/main/test_main.c'
    - '**/gmf_core/test_apps/main/cases/gmf_uri_test.c'
    - '**/gmf_core/test_apps/main/test_gmf_core_main.c'
    - '**/gmf_elements/test_apps/main/test_gmf_core_main.c'
    - '**/memory_checks.h'
    - '**/test_utils.h'
    - '**/memory_checks.c'
    - '**/leak_test.c'
    - '**/test_runner.c'
    - '**/test_utils.c'

```

# 7. 使用方法
## 7.1. 脚本命令
```bash
python check_copyright.py <file_path/dir_path> --replace
```

## 7.2. 结合 pre-commit 使用
### 7.2.1. 前提条件
1. 安装 pre-commit 工具

```bash
pip install pre-commit
```

2. 确保`.pre-commit-config.yaml` 配置文件中追加下方内容

```bash
# See https://pre-commit.com for more information
# See https://pre-commit.com/hooks.html for more hooks

repos:
  - repo: https://github.com/COFFER-S/check-copyright.git
    rev: v1.0
    hooks:
      - id: check-copyright
        types_or: [c, c++]
        # args: ['--replace'] # 默认不进行格式化，只打印不符合 License 规范的文件

```

### 7.2.2. 使用
正常使用`git commit`提交代码即可

