from flask_restx import Namespace, fields, Resource
from flask import request, redirect, url_for,make_response,jsonify
from .scene import scene
import glob
# Namespaceの初期化
util_namespace = Namespace('util', description='utilityのエンドポイント')

# JSONモデルの定義
TF_DIR="./public/tf/"
@util_namespace.route('/transfer_function/')
class TransferFunctionList(Resource):
    def get(self):
        """
        伝達関数のリスト取得
        """
        #TODO
        l=glob.glob(TF_DIR+"*.zip")
        return l, 200


