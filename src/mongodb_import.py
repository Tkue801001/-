import re
from pathlib import Path

from utils.mongodb import get_database, get_regulation_id

hierarchy_patterns = [
    [r'^第\s[零一二三四五六七八九十]+\s章\s'],  # 章: "第 一 章 "標題​
    [r'^第\s[零一二三四五六七八九十]+\s節\s'],  # 節: "第 二 節 "標題
    [
        r'^第\s\d+\s條',
        r'^第\s\d+-\d+\s條',
    ],  # 條: "第 54 條"​、"第 46-1 條"
    [r'^\d+\s'],  # 項: "1 "內文​
    [r'^[零一二三四五六七八九十]+、'],  # 款: "四、"內文​
    [r'^（[零一二三四五六七八九十]+）'],  # 目: "（二）"內文
]


def get_hierarchy_unit_number(text: str) -> bool:
    for i, patterns in enumerate(hierarchy_patterns):
        for pattern in patterns:
            if re.match(pattern, text):
                return re.match(pattern, text).group()


def get_all_regulation_title(db):
    collection = db['regulations']
    documents = collection.find({}, {'_id': 0, 'title': 1})
    return [doc['title'] for doc in documents]


def import_regulations(regulations_folder_path: Path):
    db = get_database()
    print('Database connected successfully')
    collection = db['regulations']
    print('Collection: ' + collection.name + ' connected successfully')

    regulation_title_list = get_all_regulation_title(db)

    file_paths = regulations_folder_path.iterdir()
    for i, file_path in enumerate(file_paths):
        if file_path.stem in regulation_title_list:
            print('Regulations: regulation of ' + file_path.stem + ' already exists')
            continue
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
            lines = content.split('\n')
            index = -1
            for j, line in enumerate(lines):
                if '第 一 章' in line:
                    index = j
                    break

            if index != -1:
                pre_chapter_content = '\n'.join(lines[:index])
                post_chapter_content = '\n'.join(lines[index:])
            else:
                pre_chapter_content = content
                post_chapter_content = ''

            document = {
                'title': file_path.stem,
                'meta_data': pre_chapter_content,
                'full_text': content,
            }

            # 插入文檔到集合中
            collection.insert_one(document)


def import_entry(markdown_dir_path: Path, regulations_folder_path: Path):
    # Connect to collection
    db = get_database()
    print('Database connected successfully')
    collection = db['entries']
    print('Collection: ' + collection.name + ' connected successfully')

    regulation_title_list = get_all_regulation_title(db)

    # Get all markdown files
    file_paths = markdown_dir_path.iterdir()
    for file_path in file_paths:
        file_name = file_path.stem
        # if file_name in regulation_title_list:
        #     print('Entries: regulation of ' + file_name + ' already exists')
        #     continue
        reference_id = get_regulation_id(db, file_name)

        regulations_txt_path = (
            regulations_folder_path / file_path.with_suffix('.txt').name
        )
        with open(regulations_txt_path, 'r', encoding='utf-8') as file:
            regulation_txt = file.read()

        # Read markdown file 1-by-1
        with open(file_path, 'r', encoding='utf-8') as file:
            regulation = file.read()

            # Extract sections
            pattern = r'(#+.*?)(?=\n#+|\Z)'
            sections = re.findall(pattern, regulation, re.DOTALL)

            entries = []
            parent_stack = []

            for section in sections:
                lines = section.splitlines()
                current_data = ''
                current_rank = 0

                # Combine rank 0 content
                for line in lines:
                    if line.startswith('#'):
                        current_rank = line.count('#')
                        current_data = line
                    else:
                        current_data += '\n' + line
                current_data = current_data.replace('#', '').strip()
                start_index = regulation_txt.find(current_data)
                end_index = start_index + len(current_data)

                # Find parent
                if current_data:
                    while parent_stack and parent_stack[-1]['rank'] >= current_rank:
                        parent_stack.pop()
                    parent_id = parent_stack[-1]['id'] if parent_stack else 'root'

                    entry = {
                        'ref_regulation': reference_id,
                        'unit_number': get_hierarchy_unit_number(current_data),
                        'full_text_index': [start_index, end_index],
                        'content': current_data,
                        'label': '',
                        'edge_to_parent': 'root' if parent_id == 'root' else parent_id,
                    }
                    entry_id = collection.insert_one(entry).inserted_id
                    parent_stack.append({'id': entry_id, 'rank': current_rank})

        print('Entries of ' + file_name + ' imported successfully')


if __name__ == '__main__':
    # Import regulations
    regulations_folder_path = Path('data/regulations')
    import_regulations(regulations_folder_path)

    # Import entries
    formatted_regulations_dir_path = Path('tmp/regulations_formatted')
    import_entry(formatted_regulations_dir_path, regulations_folder_path)
