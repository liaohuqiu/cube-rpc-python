#!/usr/bin/env python

from cpbox.app.devops import DevOpsApp
from cpbox.tool import functocli

APP_NAME = 'cpbox'


class App(DevOpsApp):

    def __init__(self):
        DevOpsApp.__init__(self, APP_NAME)

    def sdist(self):
        cmd = 'rm -rf dist'
        self.shell_run(cmd)
        cmd = 'python setup.py sdist'
        self.shell_run(cmd)

    def develop(self):
        cmd = 'python setup.py develop --user'
        self.shell_run(cmd)

    def upload(self):
        self.sdist()
        cmd = 'twine upload --config-file %s/.pypirc %s/dist/*' % (self.root_dir, self.root_dir)
        self.shell_run(cmd, exit_on_error=False)

    def upload_to_official(self):
        self.sdist()
        cmd = 'twine upload --config-file %s/.pypirc-official %s/dist/*' % (self.root_dir, self.root_dir)
        self.shell_run(cmd, exit_on_error=False)

    def upload_to_all(self):
        self.upload()
        self.upload_to_official()


if __name__ == '__main__':
    functocli.run_app(App)
