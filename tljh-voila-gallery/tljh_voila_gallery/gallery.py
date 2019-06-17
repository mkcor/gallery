import os
from tornado import ioloop, web
from pkg_resources import resource_stream, resource_filename
from ruamel.yaml import YAML
from jinja2 import PackageLoader, Environment
import json
from binderhub.launcher import Launcher
from urllib.parse import urljoin, urlencode

yaml = YAML()

# Read gallery.yaml on each spawn. If this gets too expensive, cache it here
def get_gallery():
    with resource_stream(__name__, 'gallery.yaml') as f:
        return yaml.load(f)

templates = Environment(loader=PackageLoader('tljh_voila_gallery', 'templates'))

class GalleryHandler(web.RequestHandler):
    def get(self):
        gallery_template = templates.get_template('gallery-examples.html')
        gallery = get_gallery()

        self.write(gallery_template.render(
            url=self.request.full_url(),
            examples=gallery.get('examples', [])
        ))

    async def post(self):
        gallery = get_gallery()

        example_name = self.get_body_argument('example')

        example = gallery['examples'][example_name]


        launcher = Launcher(
            hub_api_token=os.environ['JUPYTERHUB_API_TOKEN'],
            hub_url=os.environ['JUPYTERHUB_BASE_URL']
        )
        response = await launcher.launch(
            f'{example_name}:latest',
            launcher.unique_name_from_repo(example['repo_url'])
        )
        redirect_url = urljoin(
            response['url'],
            example['url']
        ) +  '?' + urlencode({'token': response['token']})
        self.redirect(redirect_url)
        

def make_app():
    return web.Application([
        (os.environ['JUPYTERHUB_SERVICE_PREFIX'] + '/?', GalleryHandler),
    ])

if __name__ == "__main__":
    if not os.environ['JUPYTERHUB_API_URL'].endswith('/'):
        os.environ['JUPYTERHUB_API_URL'] = os.environ['JUPYTERHUB_API_URL'] + '/'
    app = make_app()
    app.listen(9888)
    ioloop.IOLoop.current().start()