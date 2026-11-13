# PDF 字体与授权

使用本机 Noto Sans CJK SC 字体，来源为 https://github.com/notofonts/noto-cjk ，许可为 SIL Open Font License 1.1。

构建时仅转换书籍实际使用的字形，派生字体重命名为 Andy Career Guide SC，并以可搜索、可选中的 Unicode TrueType 子集嵌入 PDF。源字体不随仓库分发；完整许可副本写入本地 tmp/pdf-fonts/Noto-CJK-license.txt。

英文 SQL 示例使用本机 DejaVu Sans Mono，其自由字体许可见 https://dejavu-fonts.github.io/License.html 。

生成器仅使用系统已安装的字体与库，不在构建中联网下载字体。
