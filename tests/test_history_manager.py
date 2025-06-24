import os
import tempfile
from jcontext.history_manager import HistoryManager


def test_add_and_retrieve_prompt():
    with tempfile.TemporaryDirectory() as tmpdir:
        hist_file = os.path.join(tmpdir, 'hist.json')
        hm = HistoryManager(hist_file)
        pid = hm.add_prompt('hello world', project_path='/tmp', title='greet')
        assert hm.get_prompt(pid)['text'] == 'hello world'
        assert hm.get_prompt(pid)['title'] == 'greet'
        assert hm.get_all_prompts()[0]['id'] == pid


def test_search_and_delete():
    with tempfile.TemporaryDirectory() as tmpdir:
        hist_file = os.path.join(tmpdir, 'hist.json')
        hm = HistoryManager(hist_file)
        id1 = hm.add_prompt('first entry')
        id2 = hm.add_prompt('second entry')
        results = hm.search_prompts('second')
        assert len(results) == 1 and results[0]['id'] == id2
        assert hm.delete_prompt(id1)
        assert hm.get_prompt(id1) is None
        hm.clear_history()
        assert hm.get_all_prompts() == []
