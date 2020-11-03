from flask_restx import Namespace, fields, Resource
from .scene import event
from flask import request, redirect, url_for,make_response,jsonify
import subprocess
import os
import json
import numpy as np

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
    'feature': fields.String(
        description='(パラメータ)特徴量の種類',
        example='mel'
    ),
    'method': fields.String(
        description='(パラメータ)手法名',
        example='umap'
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
CONFIG_PATH="./public/config_embedding/"
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
        if "name" in request.json:
            name = request.json["name"]
        else:
            name = os.basename(request.json['audio_id'])
        ###
        #src_list = BASE_PATH+request.json['audio_id_list']
        #if 'event_list' in request.json:
        #    event_list = request.json['event_list']
        ###
        config_path=CONFIG_PATH+name+".json"
        with open(config_path, 'w') as outfile:
            json.dump(request.json,outfile)
        
        feature = request.json["feature"] if "feature" in request.json else "mel"
        method = request.json["method"] if "method" in request.json else "umap"
        result_path=RESULT_PATH
        cmd=["python","./src/embedding.py","--config",config_path,"--name",name,"--feature",feature,"--method",method]
        log_path=LOG_PATH+name+".txt"
        with open(log_path, 'w') as f:
            print(" ".join(cmd))
            p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
            #p = subprocess.Popen(cmd)
        pid=int(p.pid)
        worker[pid]={"process":p,"name":name}
        res={"worker_id":int(p.pid),"name":name}
        return res


@embedding_namespace.route('/result/<int:worker_id>')
class EmbeddingResult(Resource):
    @embedding_namespace.marshal_with(embedding_result)
    def get(self, worker_id):
        """
        結果取得:2次元座標(と元データの対応）の取得
        """
        #TODO
        if worker_id not in worker:
            return {},200
        if worker[worker_id]["name"] is not None:
            name=worker[worker_id]["name"]
            config_path=CONFIG_PATH+name+".json"
            config=json.load(open(config_path, 'r'))
            feature = config["feature"] if "feature" in config else "mel"
            method = config["method"] if "method" in config else "umap"

            result_path=RESULT_PATH
            filename_t = result_path+name+"."+feature+".t.npy"
            filename_i = result_path+name+"."+feature+".i.npy"
            filename_z = result_path+name+"."+feature+"."+method+".z.npy"
            data_t=np.load(filename_t)
            data_i=np.load(filename_i)
            data_z=np.load(filename_z)
            obj={}
            obj["point_list"]=[]
            audio_id_list=config["audio_id_list"]
            for i in range(len(data_z)):
                pt={}
                pt["x"]=data_z[i,0]
                pt["y"]=data_z[i,1]
                pt["audio_id"]=audio_id_list[data_i[i]]
                pt["begin_time"]=data_t[i]
                pt["duration"]=10#data_d[i]
                obj["point_list"].append(pt)
            return obj, 200
        return {},200
 
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


@embedding_namespace.route('/worker/<int:worker_id>')
class EmbeddingWorker(Resource):
    @embedding_namespace.marshal_with(embedding_worker)
    def get(self, worker_id):
        global worker
        """
        現在の処理状況の確認
        """
        if worker_id not in worker or  worker[worker_id]["process"] is None:
            return {'worker_id':worker_id,'status':"not found"},200
        if worker[worker_id]["process"].poll() is None:
            name=worker[worker_id]["name"]
            log_path=LOG_PATH+"/"+name+".txt"
            lines=[l for l in open(log_path,"r")]
            return {'worker_id':worker_id,'status':"running","log":lines},200
        worker[worker_id]["process"]=None
        return {'worker_id':worker_id,'status':"finished"},200


    def delete(self, worker_id):
        """
        処理の取り消し
        """
        if worker_id not in worker or  worker[worker_id]["process"] is None:
            return
        if worker[worker_id]["process"].poll() is None:
            pid= worker[worker_id]["process"].pid
            cmd=["kill", pid]
            print(cmd)
            p = subprocess.Popen(cmd)
            return
        return

