from flask_restx import Namespace, fields, Resource

from .scene import scene

# Namespaceの初期化
separation_namespace = Namespace('separation', description='Separationのエンドポイント')

# JSONモデルの定義

separation_worker = separation_namespace.model('SeparationWorker', {
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

separation_response = separation_namespace.model('SeparationResponse', {
    'name': fields.String(
        description='定位の設定に対する名前',
        example='separationA'
    ),
    'worker_id': fields.Integer(
        description='ワーカーID',
        example='0'
    ),
})

separation = separation_namespace.model('Separation', {
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
    'localization': fields.Nested(scene,required=True),
    'transfer_function': fields.String(
        required=True,
        description='伝達関数ファイル名',
        example='0'
    ),
   'lowest_freq': fields.Float(
        required=True,
        description='（分離パラメータ）最小周波数',
        example='2200'
    ),
})
separation_audio = separation_namespace.model('SepAudio', {
    'spec_img': fields.String(
        required=True,
        description='分離音の周波数-時間のパワー(スペクトログラム)の画像パス',
        example='spec.png',
    ),
})


@separation_namespace.route('/')
class SeparationExec(Resource):
    @separation_namespace.marshal_with(separation_response)
    @separation_namespace.expect(separation, validate=True)
    def post(self):
        """
        separationの開始
        """
        #TODO
        pass


@separation_namespace.route('/sep/<int:woker_id>/<int:sep_audio_id>')
class SeparationAudio(Resource):
    @separation_namespace.marshal_with(separation_audio)
    def get(self, worker_id,sep_audio_id):
        """
        分離音情報の取得
        """
        #TODO
        pass


@separation_namespace.route('/log/<int:woker_id>')
class SeparationLog(Resource):
    def get(self, worker_id):
        """
        ログ取得
        """
        #TODO
        return {"log":""}, 200

@separation_namespace.route('/result/<int:woker_id>')
class SeparationResult(Resource):
    @separation_namespace.marshal_with(scene)
    def get(self, worker_id):
        """
        結果取得:Sceneオブジェクト
        """
        #TODO
        pass
        

@separation_namespace.route('/worker/<int:woker_id>')
class SeparationWorker(Resource):
    @separation_namespace.marshal_with(separation_worker)
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

