import os
import tempfile
from jcontext.file_indexer import FileIndexer
from jcontext.content_processor import ContentProcessor


def setup_indexer():
    tmpdir = tempfile.TemporaryDirectory()
    with open(os.path.join(tmpdir.name, 'file.py'), 'w') as f:
        f.write('print("hi")')
    indexer = FileIndexer(tmpdir.name)
    return tmpdir, indexer


def test_extract_and_process():
    tmp, idx = setup_indexer()
    proc = ContentProcessor(idx)
    text = 'See file.py for code.'
    refs = proc.extract_file_references(text)
    assert refs == ['file.py']
    processed = proc.process_content_for_copy(text)
    assert '```python' in processed
    assert '# file.py' in processed
    assert 'print("hi")' in processed
    tmp.cleanup()


def test_validate_and_stats():
    tmp, idx = setup_indexer()
    proc = ContentProcessor(idx)
    text = 'Use file.py here.'
    validation = proc.validate_file_paths(text)
    assert validation == [('file.py', True)]
    stats = proc.get_text_statistics(text)
    assert stats['lines'] == 1
    assert stats['file_references'] == 1
    tmp.cleanup()
