from flask_restx import Namespace, fields, Resource
from .scene import scene
from flask import request, redirect, url_for,make_response,jsonify
import subprocess
import os
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
        example='audio/test_rectf00.wav'
    ),
    'begin_time': fields.Float(
        required=True,
        description='切り出しの開始(sec)、original_audio_idに対応した音声ファイルの開始を0秒とする',
        example=0
    ),
    'end_time': fields.Float(
        required=True,
        description='切り出しの終了(sec)、original_audio_idに対応した音声ファイルの開始を0秒とする',
        example=2
    ),
    'audio_id': fields.String(
        required=True,
        description='切り出したaudio_id/ファイルパス',
        example='audio_trim/test_rectf00.wav'
    ),
    'name': fields.String(
        description='切り出した部分の名前',
        example='trimA'
    ),
})
BASE_PATH="./public/"
LOG_PATH="./public/log_trim/"
worker={}
@trim_namespace.route('/')
class TrimExec(Resource):
    @trim_namespace.marshal_with(trim_response)
    @trim_namespace.expect(trim, validate=True)
    def post(self):
        global worker
        """
        trimの開始
        """
        src_path =BASE_PATH+request.json['original_audio_id']
        dest_path=BASE_PATH+request.json['audio_id']
        t1=request.json['begin_time']
        t2=request.json['end_time']
        if "name" in request.json:
            name= request.json["name"]
        else:
            name=os.path.basename(request.json['audio_id'])
        log_path=LOG_PATH+"/"+name+".txt"
        cmd=["sox", src_path,"-t","wavpcm", dest_path, "trim", str(t1),str(t2)]
        with open(log_path, 'w') as f:
            print(" ".join(cmd))
            p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
            #p = subprocess.Popen(cmd)
        pid=int(p.pid)
        worker[pid]={"process":p,"name":name}
        res={"worker_id":int(p.pid),"name":name}
        return res


@trim_namespace.route('/log/<int:worker_id>')
class TrimLog(Resource):
    def get(self, worker_id):
        """
        ログ取得
        """
        if worker_id not in worker or  worker[worker_id]["process"] is None:
            return {'log':""},200
        if worker[worker_id]["name"] is not None:
            name=worker[worker_id]["name"]
            log_path=LOG_PATH+"/"+name+".txt"
            lines=[l for l in open(log_path,"r")]
            return {"log":lines},200


        return {"log":""}, 200


@trim_namespace.route('/worker/<int:worker_id>')
class TrimWorker(Resource):
    @trim_namespace.marshal_with(trim_worker)
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


