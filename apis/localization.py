from flask_restx import Namespace, fields, Resource

from .scene import scene

# Namespaceの初期化
localization_namespace = Namespace('localization', description='Localizationのエンドポイント')

# JSONモデルの定義

localization_worker = localization_namespace.model('LocalizationWorker', {
    'worker_id': fields.Integer(
        required=True,
        description='実行しているワーカーのID',
        example='0'
    ),
    'status': fields.String(
        required=True,
        description='処理の状況:"none","pending", "running", "finished"',
        example='running'
    ),
    'progress': fields.Float(
        description='定位処理の状況0-100(%)の値',
        example='0'
    ),
})

localization_response = localization_namespace.model('LocalizationResponse', {
    'name': fields.String(
        description='定位の設定に対する名前',
        example='localizationA'
    ),
    'worker_id': fields.Integer(
        description='ワーカーID',
        example='0'
    ),
})

localization = localization_namespace.model('Localization', {
    'name': fields.String(
        required=True,
        description='定位の設定に対する名前',
        example='default'
    ),
    'audio_id': fields.String(
        required=True,
        description='対象のaudio_id',
        example='0'
    ),
    'transfer_function': fields.String(
        required=True,
        description='伝達関数ファイル名',
        example='0'
    ),
    'src_num': fields.Integer(
        required=True,
        description='（定位パラメータ）音源数',
        example='3'
    ),
    'threshold': fields.Float(
        required=True,
        description='（定位パラメータ）スレッショルド',
        example='28.5'
    ),
    'lowest_freq': fields.Float(
        required=True,
        description='（定位パラメータ）最小周波数',
        example='2200'
    ),
    'pause_length': fields.Float(
        required=True,
        description='（定位パラメータ）空白期間',
        example='1200'
    ),
    'min_interval_src': fields.Float(
        required=True,
        description='（定位パラメータ）音源間の最小間隔',
        example='15'
    ),
})

@localization_namespace.route('/')
class LocalizationExec(Resource):
    @localization_namespace.marshal_with(localization_response)
    @localization_namespace.expect(localization, validate=True)
    def post(self):
        """
        localizationの開始
        """
        #TODO
        pass

@localization_namespace.route('/spec_img/<int:woker_id>')
class LocalizationSpec(Resource):
    def get(self, worker_id):
        """
        周波数-時間のパワー(スペクトログラム)の画像パス取得
        """
        #TODO
        return {"img":""}, 200


@localization_namespace.route('/spatial_img/<int:woker_id>')
class LocalizationSpatialPower(Resource):
    def get(self, worker_id):
        """
        空間-時間のパワーの画像パス取得
        """
        #TODO
        return {"img":""}, 200



@localization_namespace.route('/log/<int:woker_id>')
class LocalizationLog(Resource):
    def get(self, worker_id):
        """
        ログ取得
        """
        #TODO
        return {"log":""}, 200

@localization_namespace.route('/result/<int:woker_id>')
class LocalizationResult(Resource):
    @localization_namespace.marshal_with(scene)
    def get(self, worker_id):
        """
        結果取得:Sceneオブジェクト
        """
        #TODO
        pass
        

@localization_namespace.route('/worker/<int:woker_id>')
class LocalizationWorker(Resource):
    @localization_namespace.marshal_with(localization_worker)
    def get(self, worker_id):
        """
        現在の処理状況の確認
        """
        #TODO
        pass

    def delete(self, worker_id):
        """
        処理の取り消し
        """
        #TODO
        return {'message': 'Success'}, 200

