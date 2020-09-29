from flask_restx import Namespace, fields, Resource

from .scene import scene

# Namespaceの初期化
util_namespace = Namespace('util', description='utilityのエンドポイント')

# JSONモデルの定義

@util_namespace.route('/transfer_function/')
class TransferFunctionList(Resource):
    def get(self):
        """
        伝達関数のリスト取得
        """
        #TODO
        return ["tamago_rec.zip"], 200


