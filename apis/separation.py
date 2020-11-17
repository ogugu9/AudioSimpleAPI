from flask_restx import Namespace, fields, Resource
from flask import request, redirect, url_for,make_response,jsonify
import subprocess
import os
import math
import json
import numpy as np

from .scene import scene

# Namespaceの初期化
separation_namespace = Namespace('separation', description='Separationのエンドポイント')

# JSONモデルの定義

separation_worker = separation_namespace.model('SeparationWorker', {
    'worker_id': fields.Integer(
        required=True,
        description='実行しているワーカーのID',
        example=0
    ),
    'status': fields.String(
        required=True,
        description='処理の状況:"none","pending", "running", "finished"',
        example='running'
    ),
    'progress': fields.Float(
        description='定位処理の状況0-100(%)の値',
        example=0
    ),
})

separation_response = separation_namespace.model('SeparationResponse', {
    'name': fields.String(
        description='定位の設定に対する名前',
        example='separationA'
    ),
    'worker_id': fields.Integer(
        description='ワーカーID',
        example=0
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
        example='audio_trim/test_rectf00.wav'
    ),
    'localization': fields.Nested(scene,required=True),
    'transfer_function': fields.String(
        required=True,
        description='伝達関数ファイル名',
        example='microcone_rectf.zip'
    ),
   'interval': fields.Float(
        required=True,
        description='（分離パラメータ）定位間隔(msec)',
        example=400
    ),
   'lowest_freq': fields.Float(
        required=True,
        description='（分離パラメータ）最小周波数',
        example=2200
    ),
})
separation_audio = separation_namespace.model('SepAudio', {
    'sep_audio_id': fields.String(
        required=True,
        description='分離音ID',
        example='spec.wav',
    ),
    'spec_img': fields.String(
        required=True,
        description='分離音の周波数-時間のパワー(スペクトログラム)の画像パス',
        example='spec.png',
    ),
    'spec_csv': fields.String(
        required=True,
        description='分離音の周波数-時間のパワー(スペクトログラム)のcsvパス',
        example='spec.csv',
    ),
})
separation_audio_list = separation_namespace.model('SepAudioList', {
    'sep_audio_list': fields.List(fields.Nested(separation_audio ,required=True)
    ),
})

def convert_events2tl(event_list,interval):
    #[{"id": 0, "x": [0.0, 0.958, 0.287], "power": 1}],
    timeline=[]
    for evt in event_list:
        loc_id=evt["localization_id"]
        begin_t=evt["begin_time"]
        begin_idx=int(math.floor(begin_t/interval))
        end_t=evt["end_time"]
        end_idx=int(end_t/interval)
        while len(timeline)<=end_idx:
            timeline.append([])
        pt_index=0
        pt_list=evt["point_list"]
        if len(pt_list)>0:
            current_pt=evt["point_list"][0]
            for i in range(end_idx-begin_idx):
                tl_idx=begin_idx+i
                current_time=begin_t+interval*i
                while pt_index+1 < len(pt_list) and pt_list[pt_index+1]["begin_time"]<=current_time:
                    pt_index+=1
                    current_pt = pt_list[pt_index]
                theta=current_pt["direction"]*math.pi/180
                obj={}
                obj["x"]=[np.cos(theta),np.sin(theta),0]
                obj["direction"]=current_pt["direction"]
                if "power" in current_pt:
                    obj["power"]=current_pt["power"]
                else:
                    obj["power"]=1
                obj["id"]=loc_id
                timeline[tl_idx].append(obj)
    return timeline


BASE_PATH="./public/"
TF_PATH="./public/tf/"
LOG_PATH="./public/log_separation/"
RESULT_PATH="./public/result_separation/"


worker={}
@separation_namespace.route('/')
class SeparationExec(Resource):
    @separation_namespace.marshal_with(separation_response)
    @separation_namespace.expect(separation, validate=True)
    def post(self):
        """
        separationの開始
        """
        global worker
        src_path=BASE_PATH+request.json['audio_id']
        tf_path=TF_PATH+request.json['transfer_function']

        if "name" in request.json:
            name= request.json["name"]
        else:
            name=os.basename(request.json['audio_id'])
        log_path=LOG_PATH+name+".txt"
        result_path=RESULT_PATH

        lowest_freq   = request.json['lowest_freq'] if 'lowest_freq' in request.json else 1000
        interval      = request.json['interval'] if 'interval' in request.json else 400
        localization=request.json['localization']
        event_list=localization["event_list"]
        tl=convert_events2tl(event_list,interval)
        loc_filename=RESULT_PATH+name+".loc.json"
        tl_filename=RESULT_PATH+name+".tl.json"
        with open(loc_filename, 'w') as fp:
            json.dump(localization, fp)
        with open(tl_filename, 'w') as fp:
            json.dump({"interval": interval, "tl": tl}, fp)
        
        os.makedirs(RESULT_PATH+name+"_sep/",exist_ok=True)
        cmd=[
            "micarrayx-separate",
            tf_path,
            src_path,
            "--timeline", tl_filename,
            #"--min_freq", str(lowest_freq),
            "--out", RESULT_PATH+name+"_sep/sep",
            "--out_sep_spectrogram_fig",
            "--out_sep_spectrogram_csv",
            ]
        with open(log_path, 'w') as f:
            print(" ".join(cmd))
            p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT)
            #print(cmd)
            #p = subprocess.Popen(cmd)
        pid=int(p.pid)
        worker[pid]={"process":p,"name":name}
        res={"worker_id":int(p.pid),"name":name}
        return res


@separation_namespace.route('/sep_audio_list/<int:worker_id>')
class SeparationAudio(Resource):
    @separation_namespace.marshal_with(separation_audio_list)
    def get(self, worker_id):
        """
        [Utility API] 分離音情報の取得
        """
        if worker_id not in worker:
            return {},200
        if worker[worker_id]["name"] is not None:
            name=worker[worker_id]["name"]
            sep_id_base="result_separation/"+name+"_sep/sep"
            loc_filename=RESULT_PATH+name+".loc.json"
            with open(loc_filename, 'r') as fp:
                loc=json.load(fp)
            data=[]
            for el in loc["event_list"]:
                sep_audio_id=sep_id_base+"."+str(el["localization_id"])+".wav"
                obj={}
                obj["sep_audio_id"]=sep_audio_id
                base_name, _ = os.path.splitext(sep_audio_id)
                obj["spec_img"]=BASE_PATH+base_name+".spec.png"
                obj["spec_csv"]=BASE_PATH+base_name+".spec.csv"
                data.append(obj)
            print(worker_id,sep_audio_id)
            return {"sep_audio_list":data}
        return {},200


@separation_namespace.route('/result/<int:worker_id>')
class SeparationResult(Resource):
    @separation_namespace.marshal_with(scene)
    def get(self, worker_id):
        """
        結果取得:Sceneオブジェクト
        """
        if worker_id not in worker:
            return {},200
        if worker[worker_id]["name"] is not None:
            name=worker[worker_id]["name"]
            loc_filename=RESULT_PATH+name+".loc.json"
            with open(loc_filename, 'r') as fp:
                loc=json.load(fp)
            for el in loc["event_list"]:
                sep_audio_id=SEP_ID_BASE+name+"."+str(el["localization_id"])+".wav"
                el["sep_audio_id"]=sep_audio_id
            return loc
        return {},200

@separation_namespace.route('/log/<int:worker_id>')
class SeparationLog(Resource):
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


@separation_namespace.route('/worker/<int:worker_id>')
class SeparationWorker(Resource):
    @separation_namespace.marshal_with(separation_worker)
    def get(self, worker_id):
        """
        現在の処理状況の確認
        """
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

