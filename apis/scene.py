from flask_restx import Namespace, fields, Resource


# Namespaceの初期化
scene_namespace = Namespace('scene', description='sceneのエンドポイント: 切り出した音声ファイルにイベント（定位された結果もしくはアノテーションされた結果）のセット')

# JSONモデルの定義
event_point = scene_namespace.model('EventPoint', {
    'begin_time': fields.Float(
        required=True,
        description='定位の開始(sec) 、eventの開始を0秒とする',
        example=0
    ),
    'duration': fields.Float(
        required=True,
        description='定位時間(sec) 、デフォルトの定位設定だと500msecごとに定位を行う',
        example=0.5
    ),
    'direction': fields.Float(
        required=True,
        description='定位方向(degree) 、0度を中心+180から-180で指定',
        example=0
    ),

})

event = scene_namespace.model('Event', {
    'begin_time': fields.Float(
        required=True,
        description='イベントの開始(sec) 、audio_idの開始を0秒とする',
        example=0
    ),
    'end_time': fields.Float(
        required=True,
        description='イベントの終了(sec)、audio_idの開始を0秒とする',
        example=0
    ),
    'sep_audio_id': fields.String(
        description='分離音の音声ファイルのID',
        example=""
    ),
    'point_list': fields.List(fields.Nested(event_point),required=True),
    'label': fields.String(
        description='イベントの名前',
        example='Event A'
    ),
    'localization_id': fields.String(
        description='イベントの名前',
        example='0'
    ),
})


scene = scene_namespace.model('Scene', {
    'audio_id': fields.String(
        required=True,
        description='切り出したaudio_id',
        example='1'
    ),
    'event_list': fields.List(fields.Nested(event),required=True),
    'name': fields.String(
        required=True,
        description='切り出し部分の名前',
        example='trim A'
    ),
})


@scene_namespace.route('/dummy/')
class SceneDummy(Resource):
    """
    ダミーscene
    """
    @scene_namespace.marshal_with(scene)
    def get(self):
        """
        ダミー取得
        """
        obj={
                "audio_id":"dummy_audio",
                "name":"dummy",
                "event_list":[
                    {
                        "begin_time":0.0,
                        "end_time":1.0,
                        "point_list":[{
                            "begin_time":0.0,
                            "duration":1.0,
                            "direction":45.0,
                            }]
                        }
                    ]
                }
        return obj



