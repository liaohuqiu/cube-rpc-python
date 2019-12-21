#!/usr/bin/env python

from cpbox.tool import functocli
from cpbox.tool import dockerutil
from cpbox.tool import template
from cpbox.app.devops import DevOpsApp

APP_NAME = 'cubi-rpc'
version = '1.0'
image_name = 'docker.vhash.io/liaohuqiu/cubi-rpc-dev:' + version
image_name_push = 'docker-publish.vhash.io/liaohuqiu/cubi-rpc-dev:' + version


class App(DevOpsApp):

    def __init__(self):
        DevOpsApp.__init__(self, APP_NAME)

    def sdist(self):
        cmd = 'rm -rf dist'
        self.shell_run(cmd)
        cmd = 'python src/setup.py sdist'
        self.shell_run(cmd)

    def develop(self):
        cmd = 'python src/setup.py develop --user'
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

    def __init__(self, **kwargs):
        DevOpsApp.__init__(self, APP_NAME, **kwargs)
        self.cli_container_name = 'cube-rpc-cli'

    def start(self):
        cmd = 'tail -f /dev/null'
        self._run_container(self.cli_container_name, cmd, '-d')

    def _run_container(self, container_name, cmd, mod):
        volumes = {
            self.root_dir: '/opt'
        }
        args = dockerutil.base_docker_args(
            container_name=container_name,
            volumes=volumes,
            working_dir='/opt'
        )
        cmd_data = {}
        cmd_data['image'] = image_name
        cmd_data['args'] = args
        cmd_data['cmd'] = cmd
        cmd_data['run_mod'] = mod
        cmd = template.render_str(
            'docker run {{ run_mod }} --net=host --restart always {{ args }} {{ image }} bash -c "{{ cmd }}"', cmd_data)
        self.shell_run(cmd)

    def restart(self):
        self.stop()
        self.start()

    def stop(self):
        self.remove_container(self.cli_container_name, force=True)

    def attach(self):
        cmd = 'docker exec -it %s bash' % (self.cli_container_name)
        self.shell_run(cmd)

    def build_image(self):
        cmd = 'docker build -t %s %s/docker' % (image_name, self.root_dir)
        self.shell_run(cmd)

    def push_image(self):
        cmd = 'docker tag %s %s' % (image_name, image_name_push)
        self.shell_run(cmd)

        cmd = 'docker push %s' % (image_name_push)
        self.shell_run(cmd)

    def test(self):
        self.logger.info('test')

    def run_echo_server(self):
        cmd = 'python src/cubi-echo-server.py roles/cubi-rpc/config/cubi-echo-server.yml'
        self.shell_run(cmd)


if __name__ == '__main__':
    functocli.run_app(App)
