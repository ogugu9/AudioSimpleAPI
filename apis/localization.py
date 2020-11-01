from flask_restx import Namespace, fields, Resource
from .scene import scene
from flask import request, redirect, url_for,make_response,jsonify
import subprocess
import os

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
        example='audio_trim/test_rectf00.wav'
    ),
    'transfer_function': fields.String(
        required=True,
        description='伝達関数ファイル名',
        example='microcone_rectf.zip'
    ),
})

localization_result = localization_namespace.model('LocalizationResult', {
    'localization': fields.Nested(scene,required=True),
    'spec_img': fields.String(
        required=True,
        description='周波数-時間のパワー(スペクトログラム)の画像パス',
        example='/img.png',
    ),
    'spatial_img': fields.String(
        required=True,
        description='空間-時間のパワー(MUSICスペクトログラム)の画像パス',
        example='/img.png',
    ),
})


BASE_PATH="./public/"
TF_PATH="./public/tf/"
LOG_PATH="./public/log_localization/"
RESULT_PATH="./public/result_localization/"
worker={}
@localization_namespace.route('/')
class LocalizationExec(Resource):
    @localization_namespace.marshal_with(localization_response)
    @localization_namespace.expect(localization, validate=True)
    def post(self):
        global worker
        """
        localizationの開始
        """
        src_path=BASE_PATH+request.json['audio_id']
        tf_path=TF_PATH+request.json['transfer_function']

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
                "--out_localization", result_path+name+".loc.json",
                ">",log_path]
        print(" ".join(cmd))
        p = subprocess.Popen(cmd)
        pid=int(p.pid)
        worker[pid]={"process":p,"name":name}
        res={"worker_id":int(p.pid),"name":name}
        return res

@localization_namespace.route('/result/<int:woker_id>')
class LocalizationResult(Resource):
    @localization_namespace.marshal_with(localization_result)
    def get(self, worker_id):
        """
        結果取得:Sceneオブジェクト+ 画像等
        """
        #TODO
        pass
 
@localization_namespace.route('/log/<int:woker_id>')
class LocalizationLog(Resource):
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

       

@localization_namespace.route('/worker/<int:woker_id>')
class LocalizationWorker(Resource):
    @localization_namespace.marshal_with(localization_worker)
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

