# emoji-parser

从 Unicode 官方数据文件中提取所有 emoji，输出为标准 CSV，方便 Java 等语言读取到 `HashSet` 中做匹配。

## 性能效果

> [!IMPORTANT]
>
> 正式测试前，会跑一轮**测试短剧🂡**进行预热，**减小启动JVM时间**

### 考虑JVM耗时

```
--rerun-tasks --info | grep "耗时"
    [耗时] 输入=测试短剧😀 -> **147 ms (147526209 ns)** 
    [耗时] 输入=测试短剧👩‍🚀，👨‍👩‍👧‍👦 -> 2 ms (2699791 ns)
    [耗时] 输入=测试短剧👋🏽 -> 2 ms (2383125 ns)
    [耗时] 输入=测试短剧🂡 -> 1 ms (1499166 ns)
    [耗时] 输入=测试短剧 -> **60 ms (60474667 ns)**
    [耗时] 输入=测试短剧∑ -> 0 ms (330792 ns)
    [耗时] 输入=测试短剧🌹 -> 2 ms (2091250 ns)
    [耗时] 输入=𪚥 -> 1 ms (1877291 ns)
    [耗时] 输入=💯 -> 1 ms (1942209 ns)
    [耗时] 输入=测试短剧❤ -> **1 ms (1476333 ns)**
```

### 原始版本

```
--rerun-tasks --info | grep "耗时"
    [耗时] 输入=测试短剧😀 -> 2 ms (2841375 ns)
    [耗时] 输入=测试短剧👩‍🚀，👨‍👩‍👧‍👦 -> 2 ms (2515875 ns)
    [耗时] 输入=测试短剧👋🏽 -> 1 ms (1440000 ns)
    [耗时] 输入=测试短剧🂡 -> 3 ms (3551125 ns)
    [耗时] 输入=测试短剧 -> **59 ms (59456250 ns)**
    [耗时] 输入=测试短剧∑ -> 0 ms (343167 ns)
    [耗时] 输入=测试短剧🌹 -> 1 ms (1306542 ns)
    [耗时] 输入=𪚥 -> 1 ms (1946334 ns)
    [耗时] 输入=💯 -> 2 ms (2390916 ns)
    [耗时] 输入=测试短剧❤ -> **1 ms (1074791 ns)**
```

### emojis.csv

```
--rerun-tasks --info | grep "耗时"
    [耗时] 输入=测试短剧😀 -> 1 ms (1519417 ns)
    [耗时] 输入=测试短剧👩‍🚀，👨‍👩‍👧‍👦 -> 2 ms (2276541 ns)
    [耗时] 输入=测试短剧👋🏽 -> 3 ms (3949333 ns)
    [耗时] 输入=测试短剧🂡 -> 1 ms (1921375 ns)
    [耗时] 输入=测试短剧 -> **13 ms (13389291 ns)**
    [耗时] 输入=测试短剧∑ -> 0 ms (693166 ns)
    [耗时] 输入=测试短剧🌹 -> 6 ms (6074000 ns)
    [耗时] 输入=𪚥 -> 6 ms (6044459 ns)
    [耗时] 输入=💯 -> 3 ms (3031875 ns)
    [耗时] 输入=测试短剧❤ -> **1 ms (1670208 ns)**
```

### emoji-mask.csv

```
--rerun-tasks --info | grep "耗时"
    [耗时] 输入=测试短剧😀 -> 1 ms (1597708 ns)
    [耗时] 输入=测试短剧👩‍🚀，👨‍👩‍👧‍👦 -> 1 ms (1289333 ns)
    [耗时] 输入=测试短剧👋🏽 -> 2 ms (2470459 ns)
    [耗时] 输入=测试短剧🂡 -> 2 ms (2214791 ns)
    [耗时] 输入=测试短剧 -> **21 ms (21863667 ns)**
    [耗时] 输入=测试短剧∑ -> 0 ms (388083 ns)
    [耗时] 输入=测试短剧🌹 -> 1 ms (1838500 ns)
    [耗时] 输入=𪚥 -> 3 ms (3857416 ns)
    [耗时] 输入=💯 -> 2 ms (2449625 ns)
    [耗时] 输入=测试短剧❤ -> **2 ms (2981291 ns)**
```

## 数据来源

`res/` 目录下为 Unicode 官方 emoji 数据文件（**Version 17.0**）：

| 文件 | 说明 |
| --- | --- |
| `emoji-test.txt` | Emoji 键盘/显示测试数据，包含 RGI emoji 全集 |
| `emoji-sequences.txt` | 基础 emoji、keycap、旗帜、tag 等序列（含 `..` 码点范围） |
| `emoji-zwj-sequences.txt` | ZWJ 连接序列（如家庭、职业等组合 emoji） |

> 后两个文件中的 emoji 均为 `emoji-test.txt` 的子集，合并去重后总数与其一致。

## 使用方法

需要 Python 3。在项目根目录运行：

```bash
python3 extract_emojis.py
```

脚本会解析 `res/` 下的三个文件，把十六进制码点（含范围与 ZWJ 多码点序列）转换为实际 emoji 字符，合并去重后写入 `emojis.csv`。

### 命令行参数

| 参数 | 说明 |
| --- | --- |
| `--mask-surrogate` | 筛除在 Java（UTF-16）中含代理项 char 的 emoji，结果写入 `emojis-mask.csv` |

`--mask-surrogate` 用于只保留所有码点都在 BMP（≤ U+FFFF）内的 emoji。在 Java 字符串（UTF-16）中，码点 ≥ U+10000 的补充字符会被表示为一对代理项，此时 `Character.isSurrogate(ch)` 为 `true`；该参数筛除任一码点 ≥ U+10000 的 emoji，确保结果中每个 `char` 都不是代理项。

```bash
python3 extract_emojis.py --mask-surrogate
```

筛除后剩余 **312 个**全 BMP 码点的 emoji（多为 keycap、变体选择符等组合形式）。

## 输出格式

`emojis.csv` 为标准 CSV，UTF-8 编码：

- 第一行为标题 `emoji`
- 之后每行一个 emoji 字符
- 使用 Python `csv` 模块写出，遵循标准转义规则
- 行尾统一为 LF（`\n`）。`csv` 模块默认按 RFC 4180 使用 CRLF（`\r\n`），脚本已显式指定 `lineterminator='\n'` 改为 LF，避免下游用 `split("\n")` 手动拆分时行尾残留 `\r` 导致 `HashSet` 匹配失败（`BufferedReader.readLine()` 不受影响，两种行尾都能正确处理）

```csv
emoji
#⃣
😀
👨‍👩‍👧‍👦
```

当前共提取 **5225 个唯一 emoji**（`emojis.csv`）；使用 `--mask-surrogate` 时为 **312 个**（`emojis-mask.csv`）。两个文件的格式完全一致。

注意：单个 emoji 可能由多个 Unicode 码点组成（如 ZWJ 序列），因此应按整行作为一个 emoji 处理，不要按字符拆分。

## Java 读取示例

跳过首行标题，将每行加入 `HashSet<String>`：

```java
import java.io.BufferedReader;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.HashSet;
import java.util.Set;

public class EmojiLoader {
    public static Set<String> loadEmojis(String csvPath) throws IOException {
        Set<String> emojis = new HashSet<>();
        try (BufferedReader reader = Files.newBufferedReader(
                Paths.get(csvPath), StandardCharsets.UTF_8)) {
            String line = reader.readLine(); // 跳过标题行
            while ((line = reader.readLine()) != null) {
                if (!line.isEmpty()) {
                    emojis.add(line);
                }
            }
        }
        return emojis;
    }
}
```

## 项目结构

```
emoji-parser/
├── README.md
├── extract_emojis.py   # 提取脚本
├── emojis.csv          # 输出结果（全部 emoji）
├── emojis-mask.csv     # 输出结果（--mask-surrogate，仅 BMP 码点）
└── res/                # Unicode 官方数据文件
    ├── emoji-test.txt
    ├── emoji-sequences.txt
    └── emoji-zwj-sequences.txt
```
