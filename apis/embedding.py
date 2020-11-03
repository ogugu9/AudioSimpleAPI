from flask_restx import Namespace, fields, Resource
from .scene import event
from flask import request, redirect, url_for,make_response,jsonify
import subprocess
import os

# Namespaceの初期化
embedding_namespace = Namespace('embedding', description='Embeddingのエンドポイント')

# JSONモデルの定義
embedding_point = embedding_namespace.model('EmbeddingPoint', {
    'x': fields.Float(
        required=True,
        description='低次化した際の次元:1',
        example=0.0
    ),
    'y': fields.Float(
        required=True,
        description='低次化した際の次元:2',
        example=0.0
    ),
    'audio_id': fields.String(
        required=True,
        description='対象のaudio_id',
        example='audio_trim/test_rectf00.wav'
    ),
    'begin_time': fields.Float(
        required=True,
        description='対象のaudio_id中のどの時刻からの特徴量か？',
        example=0
    ),
    'duration': fields.Float(
        required=True,
        description='対象のaudio_id中のどれだけの区間か？(msec)',
        example=1
    ),
    'original_vector': fields.List(fields.Float(),
        description='2次元にする前の特徴量',
        example=[]
    ),
})

embedding_result = embedding_namespace.model('EmbeddingResult', {
    'point_list': fields.List(fields.Nested(embedding_point,required=True),
        required=True,
        description='低次元化した点のリスト',
        example=[]
    ),
})

embedding = embedding_namespace.model('Embedding', {
    'name': fields.String(
        required=True,
        description='圧縮の設定に対する名前',
        example='default'
    ),
    'audio_id_list': fields.List(fields.String(),
        required=True,
        description='対象のaudio_id',
        example=['audio_trim/test_rectf00.wav']
    ),
    'event_list': fields.List(fields.Nested(event,required=True),
        description='audio_id_listと対応したイベント情報を付与する（基本は不要だが圧縮の際にシーン情報まで利用する場合には必要、audio_id_list と同じ順番で指定する）',
        example=[]
    ),
})

embedding_worker = embedding_namespace.model('EmbeddingWorker', {
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

embedding_response = embedding_namespace.model('EmbeddingResponse', {
    'name': fields.String(
        description='定位の設定に対する名前',
        example='embeddingA'
    ),
    'worker_id': fields.Integer(
        description='ワーカーID',
        example='0'
    ),
})

BASE_PATH="./public/"
LOG_PATH="./public/log_embedding/"
RESULT_PATH="./public/result_embedding/"
worker={}
@embedding_namespace.route('/')
class EmbeddingExec(Resource):
    @embedding_namespace.marshal_with(embedding_response)
    @embedding_namespace.expect(embedding, validate=True)
    def post(self):
        global worker
        """
        embeddingの開始
        """
        src_path=BASE_PATH+request.json['audio_id']
        tf_path =TF_PATH+request.json['transfer_function']

        if "name" in request.json:
            name= request.json["name"]
        else:
            name=os.basename(request.json['audio_id'])
        log_path=LOG_PATH+name+".txt"
        result_path=RESULT_PATH

        src_num          = request.json['src_num']
        threshold        = request.json['threshold']
        lowest_freq      = request.json['lowest_freq']
        pause_length     = request.json['pause_length']
        min_interval_src = request.json['min_interval_src']
     
        cmd=["micarrayx-localize", tf_path, src_path,
                #"--stft_win_size", S,
                #"--stft_step", S,
                "--min_freq", str(lowest_freq),
                #"--max_freq", F,
                #"--music_win_size", S,
                #"--music_step", S,
                "--music_src_num", str(src_num),
                "--out_npy", result_path+name+".npy",
                "--out_full_npy", result_path+name+".full.npy",
                "--out_fig", result_path+name+".music.png",
                "--out_spectrogram",result_path+name+".spec.png",
                "--out_setting",result_path+name+".config.json",
                "--thresh", str(threshold),
                "--event_min_size", str(min_interval_src),
                "--out_embedding", result_path+name+".loc.json",
                ">",log_path]
        print(" ".join(cmd))
        p = subprocess.Popen(cmd)
        pid=int(p.pid)
        worker[pid]={"process":p,"name":name}
        res={"worker_id":int(p.pid),"name":name}
        return res


@embedding_namespace.route('/result/<int:worker_id>')
class EmbeddingResult(Resource):
    @embedding_namespace.marshal_with(embedding_result)
    def get(self, worker_id):
        """
        結果取得:Sceneオブジェクト+ 画像等
        """
        #TODO
        if worker_id not in worker:
            return {},200
        if worker[worker_id]["name"] is not None:
            name=worker[worker_id]["name"]
            result_path=RESULT_PATH
            out_npy      = result_path+name+".npy"
            out_full_npy = result_path+name+".full.npy"
            out_fig      = result_path+name+".music.png"
            out_spectrogram  = result_path+name+".spec.png"
            out_setting      = result_path+name+".config.json"
            out_embedding = result_path+name+".loc.json"
            
            obj={}
            obj["embedding"]={}
            obj["embedding"]["audio_id"]=""
            obj["embedding"]["name"]=name
            obj["embedding"]["event_list"]=[]
            if os.path.exists(out_embedding):
                print("[LOAD]",out_embedding)
                loc_obj=json.load(open(out_embedding))
                interval=loc_obj["interval"]
                tl=loc_obj["tl"]
                obj["embedding"]["event_list"]=convert_tl2events(tl,interval)
            obj["spec_img"]= out_spectrogram
            obj["spatial_img"]= out_fig
            return obj, 200
 
@embedding_namespace.route('/log/<int:worker_id>')
class EmbeddingLog(Resource):
    def get(self, worker_id):
        """
        ログ取得
        """
        if worker_id not in worker:
            return {'log':""},200
        if worker[worker_id]["name"] is not None:
            name=worker[worker_id]["name"]
            log_path=LOG_PATH+"/"+name+".txt"
            lines=[l for l in open(log_path,"r")]
            return {"log":lines},200
        return {"log":""}, 200

