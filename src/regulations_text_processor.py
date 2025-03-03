import re
from pathlib import Path
from typing import Union

# 正規表達式紀錄
# ^ 表示字串的開頭。
# \d+ 表示一個或多個數字。
# \s 表示一個空白字符（包括空格、制表符等）。

# ^\d+ : 字串以數字開頭
# ^\d+\s : 字串以數字開頭且跟著一個空白
# ^[零一二三四五六七八九十]+、 :

hierarchy_patterns = [
    [r'^\s第\s[零一二三四五六七八九十]+\s章\s'],  # 章: " 第 一 章 "標題​
    [r'^\s第\s[零一二三四五六七八九十]+\s節\s'],  # 節: " 第 二 節 "標題
    [
        r'^第\s\d+\s條',
        r'^第\s\d+-\d+\s條',
    ],  # 條: "第 54 條"​、"第 46-1 條"
    [r'^\d+\s'],  # 項: "1 "內文​
    [r'^[零一二三四五六七八九十]+、'],  # 款: "四、"內文​
    [r'^（[零一二三四五六七八九十]+）'],  # 目: "（二）"內文
]


def check_hierarchy(text: str) -> bool:
    for i, patterns in enumerate(hierarchy_patterns):
        for pattern in patterns:
            if re.match(pattern, text):
                return i + 1
    return 0


def process_regulations_txt(
    input_file: Union[str, Path], output_file: Union[str, Path]
) -> None:
    with open(input_file, 'r', encoding='utf-8') as f:
        txt_lines = f.readlines()

    new_content = ''
    current_hierarchy = 0
    current_heading = 0
    line_index = 0
    hierarchy_heading = [0] * len(hierarchy_patterns)

    for line in txt_lines:
        line_index += 1
        result = check_hierarchy(line)
        if result > 0:
            # 發現 line 是 heading，所以需要加上 # 字號了
            new_hierarchy = result
            if new_hierarchy > current_hierarchy:
                # 要升級 current_level，也就是 # 數量要增加
                current_heading += 1
                hierarchy_heading[new_hierarchy - 1] = current_heading
            if new_hierarchy < current_hierarchy:
                # 要降級 current_level，也就是 # 數量要減少
                current_heading = hierarchy_heading[new_hierarchy - 1]
            current_hierarchy = new_hierarchy
            # 在這一行加上跟 current_heading 一樣數量的 # 字號
            line = '#' * current_heading + ' ' + line
        new_content += line

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(new_content)


if __name__ == '__main__':
    regulations_dir_path = Path('data/regulations')
    output_dir_path = Path('tmp/regulations_formatted')
    output_dir_path.mkdir(parents=True, exist_ok=True)
    for txt_file in regulations_dir_path.glob('*.txt'):
        print(f'Processing {txt_file}...')
        output_file_path = output_dir_path / (txt_file.stem + '.md')
        print(f'Output file: {output_file_path}')
        process_regulations_txt(txt_file, output_file_path)
