from flask_restx import Namespace, fields, Resource

from .scene import scene

# Namespaceの初期化
trim_namespace = Namespace('trim', description='Trimのエンドポイント:切り出し')

# JSONモデルの定義

trim_worker = trim_namespace.model('TrimWorker', {
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
        description='切り出し処理の状況0-100(%)の値',
        example='0'
    ),
})

trim_response = trim_namespace.model('TrimResponse', {
    'name': fields.String(
        description='切り出した部分の名前',
        example='trimA'
    ),
    'worker_id': fields.Integer(
        description='ワーカーID',
        example='0'
    ),
})

trim = trim_namespace.model('Trim', {
    'original_audio_id': fields.String(
        required=True,
        description='元の音声ファイルID/ファイルパス',
        example='0'
    ),
    'begin_time': fields.Float(
        required=True,
        description='切り出しの開始(sec)、original_audio_idに対応した音声ファイルの開始を0秒とする',
        example='0'
    ),
    'end_time': fields.Float(
        required=True,
        description='切り出しの終了(sec)、original_audio_idに対応した音声ファイルの開始を0秒とする',
        example='0'
    ),
    'audio_id': fields.String(
        required=True,
        description='切り出したaudio_id/ファイルパス',
        example='1'
    ),
    'name': fields.String(
        description='切り出した部分の名前',
        example='trimA'
    ),
})

@trim_namespace.route('/')
class TrimExec(Resource):
    @trim_namespace.marshal_with(trim_response)
    @trim_namespace.expect(trim, validate=True)
    def post(self):
        """
        trimの開始
        """
        #TODO
        pass


@trim_namespace.route('/log/<int:woker_id>')
class TrimLog(Resource):
    def get(self, worker_id):
        """
        ログ取得
        """
        #TODO
        return {"log":""}, 200


@trim_namespace.route('/worker/<int:woker_id>')
class TrimWorker(Resource):
    @trim_namespace.marshal_with(trim_worker)
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
