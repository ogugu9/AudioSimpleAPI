from flask import Flask
from flask_restx import Api, Resource, fields

app = Flask(__name__)
api = Api(app, version='1.0', title='Audio Simple API',
    description='Trim/Localization/Separation/Embedding API',
)
from apis.scene import scene_namespace
from apis.trim import trim_namespace
from apis.localization import localization_namespace
from apis.separation import separation_namespace
from apis.embedding import embedding_namespace
from apis.util import util_namespace
api.add_namespace(scene_namespace)
api.add_namespace(trim_namespace)
api.add_namespace(localization_namespace)
api.add_namespace(separation_namespace)
api.add_namespace(embedding_namespace)
api.add_namespace(util_namespace)


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
