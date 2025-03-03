from pathlib import Path

from utils.mongodb import get_database, get_regulation_id


def test_full_text_index(entry_id: str):
    """
    Tests if the full text index of an entry matches the content of the corresponding regulation.

    Args:
        entry_id (str): The ID of the entry to be tested. E.g., 'entry_5'.

    Returns:
        None
    """
    db = get_database()
    # print('Database connected successfully')
    collection_entries = db['entries']
    # print('Collection: ' + collection_entries.name + ' connected successfully')

    collection_regulations = db['regulations']
    # print('Collection: ' + collection_regulations.name + ' connected successfully')

    entry = collection_entries.find_one({'_id': entry_id})
    entry_content = entry['content']
    start_index, end_index = entry['full_text_index']

    regulation = collection_regulations.find_one({'_id': entry['ref_regulation']})
    full_text = regulation['full_text']
    if full_text[start_index:end_index] == entry_content:
        print('Test type(result): successfully')
    else:
        print('Test result: failed')


def full_text_search(search_text: str):
    # search_text = '建築物'

    db = get_database()
    collection_entries = db['entries']

    query = {'content': {'$regex': search_text}}
    results = collection_entries.find(query)

    # # 印出搜尋結果
    # results = list(results)
    # print(len(results))
    # for result in results:
    #     print(result)
    return list(results)


def context_entries_search(entry_id: str):
    db = get_database()
    collection_name = 'entries'
    collection_entries = db[collection_name]
    collection_entries['edge_to_parent']

    query_result = collection_entries.aggregate(
        [
            # 1. 找到指定的節點，這裡假設為 _id: "A"
            {'$match': {'_id': entry_id}},
            # 2. 找出所有的祖先節點
            {
                '$graphLookup': {
                    'from': collection_name,
                    'startWith': '$edge_to_parent',  # 開始尋找父層
                    'connectFromField': 'edge_to_parent',  # 一直向上查找 edge_to_parent
                    'connectToField': '_id',
                    'as': 'ancestors',  # 查找結果存儲在 ancestors
                    'depthField': 'ancestorLevel',  # 可選，記錄層級深度
                }
            },
            # 3. 找出所有的子孫節點
            {
                '$graphLookup': {
                    'from': collection_name,
                    'startWith': '$_id',  # 開始尋找子層
                    'connectFromField': '_id',  # 當前文件的 _id
                    'connectToField': 'edge_to_parent',  # 連接到子文件的 edge_to_parent
                    'as': 'descendants',  # 查找結果儲存在 descendants
                    'depthField': 'descendantLevel',  # 可選，保存層級深度
                }
            },
        ]
    )

    query_result = list(query_result)
    if len(query_result) != 1:
        raise ValueError(
            f'Expected exactly one result to match the query, but found {len(query_result)}'
        )

    return query_result[0]


def concate_ancestor_entries_content(entry_id: str):
    context_entries = context_entries_search(entry_id)
    this_entry_content = context_entries['content']
    ancestor_entries = context_entries_search(entry_id)['ancestors']

    result_content = ''
    ancestor_entries.sort(key=lambda x: x['ancestorLevel'], reverse=True)
    for ancestor in ancestor_entries:
        result_content += ancestor['content'] + '\n'
    result_content += this_entry_content
    # print(result_content)
    return result_content


def concate_ancestor_entries_unit_number(entry_id: str):
    context_entries = context_entries_search(entry_id)
    this_entry_unit_number = context_entries['unit_number']
    ancestor_entries = context_entries_search(entry_id)['ancestors']

    result_unit_number = ''
    ancestor_entries.sort(key=lambda x: x['ancestorLevel'], reverse=True)
    for ancestor in ancestor_entries:
        result_unit_number += ancestor['unit_number'] + ', '
    result_unit_number += this_entry_unit_number
    # print(result_content)
    return result_unit_number


def deduplicate_content_list(content_list: list):
    """Deduplicates a list of content"""
    content_list.sort(key=lambda x: len(x))
    for i, content in enumerate(content_list):
        for j in range(i + 1, len(content_list)):
            if content in content_list[j]:
                content_list[j] = ''
    # remove empty strings and return it
    return [content for content in content_list if content]


def save_regulation_entries(regulation_title, save_dir):
    db = get_database()

    save_dir_path: Path = Path(save_dir) / regulation_title
    if not save_dir_path.exists():
        save_dir_path.mkdir(parents=True, exist_ok=True)

    collection = db['entries']

    regulation_id = get_regulation_id(db, regulation_title)
    # get all entries that are associated with the regulation title
    query = {'ref_regulation': regulation_id}
    documents = collection.find(query)

    # save each document to txt file with the firsrt line of document content as filename
    for document in documents:
        filename = document['content'].split('\n')[0].strip()
        save_file_path = save_dir_path / filename
        with open(save_file_path, 'w', encoding='utf-8') as f:
            f.write(document['content'])


if __name__ == '__main__':
    # matched_enries_results = []
    # for matched_entry in full_text_search('梯子'):
    #     entry_id = matched_entry['_id']
    #     result = concate_ancestor_entries(entry_id)
    #     matched_enries_results.append(result)
    # deduplicate_result = deduplicate_content_list(matched_enries_results)
    # for result in deduplicate_result:
    #     print(result)
    #     print('------')
    save_regulation_entries('職業安全衛生設施規則', 'tmp/entrys_txt_files')
