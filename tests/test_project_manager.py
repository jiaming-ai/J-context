import os
import tempfile
from jcontext.project_manager import ProjectManager
from jcontext.global_settings import GlobalSettings


def test_create_and_load_project():
    with tempfile.TemporaryDirectory() as home:
        orig_home = os.environ.get('HOME')
        os.environ['HOME'] = home
        try:
            gs = GlobalSettings(root_dir=home)
            pm = ProjectManager(gs)
            proj_dir = tempfile.mkdtemp(dir=home)
            pid = pm.create_or_update_project(proj_dir)
            assert pid in pm.projects
            assert pm.set_current_project(pid)
            cur = pm.get_current_project()
            assert cur and cur['path'] == proj_dir
        finally:
            if orig_home is not None:
                os.environ['HOME'] = orig_home
            else:
                del os.environ['HOME']
