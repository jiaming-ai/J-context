import os
import tempfile
from jcontext.file_indexer import FileIndexer

def create_sample_dir():
    tmpdir = tempfile.TemporaryDirectory()
    base = tmpdir.name
    os.makedirs(os.path.join(base, 'sub'), exist_ok=True)
    with open(os.path.join(base, 'foo.py'), 'w') as f:
        f.write('print("foo")')
    with open(os.path.join(base, 'bar.js'), 'w') as f:
        f.write('console.log("bar")')
    with open(os.path.join(base, 'sub', 'test.txt'), 'w') as f:
        f.write('hello')
    return tmpdir

def test_index_and_search():
    tmp = create_sample_dir()
    idx = FileIndexer()
    assert idx.set_root_path(tmp.name)
    # Should index 3 files
    assert idx.get_indexed_files_count() == 3
    # Exact match
    assert idx.search_files('foo.py', limit=1) == ['foo.py']
    # Prefix match
    results = idx.search_files('ba')
    assert 'bar.js' in results
    # Contains match
    results = idx.search_files('test')
    assert 'sub/test.txt' in results
    tmp.cleanup()

def test_file_content_and_language():
    tmp = create_sample_dir()
    idx = FileIndexer(tmp.name)
    assert idx.get_file_content('foo.py').strip() == 'print("foo")'
    assert idx.get_file_language('foo.py') == 'python'
    tmp.cleanup()
