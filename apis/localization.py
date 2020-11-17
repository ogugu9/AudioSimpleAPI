from flask_restx import Namespace, fields, Resource
from .scene import scene
from flask import request, redirect, url_for,make_response,jsonify
import subprocess
import os
import math
import json

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
    'src_num': fields.Integer(
        required=False,
        description='(パラメータ)',
        example=3
    ),
    'threshold': fields.Float(
        required=False,
        description='(パラメータ)',
        example=12.5
    ),
    'lowest_freq': fields.Float(
        required=False,
        description='(パラメータ)',
        example=1000
    ),
    'pause_length': fields.Float(
        required=False,
        description='(パラメータ)',
        example=10
    ),
    'min_interval_src': fields.Float(
        required=False,
        description='(パラメータ)',
        example=10
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

        src_num          = request.json['src_num'] if 'src_num' in request.json else 3
        threshold        = request.json['threshold'] if 'threshold' in request.json else 10
        lowest_freq      = request.json['lowest_freq'] if 'lowest_freq' in request.json else 1000
        pause_length     = request.json['pause_length'] if 'pause_length' in request.json else 100
        min_interval_src = request.json['min_interval_src'] if 'min_interval_src' in request.json else 10
     
        #"--stft_win_size", S,
        #"--stft_step", S,
        #"--max_freq", F,
        #"--music_win_size", S,
        #"--music_step", S,
        cmd=["micarrayx-localize",
                "--min_freq",         str(lowest_freq),
                "--music_src_num",    str(src_num),
                "--thresh",           str(threshold),
                "--event_min_size",   str(min_interval_src),
                "--out_npy",          result_path+name+".npy",
                "--out_full_npy",     result_path+name+".full.npy",
                "--out_fig",          result_path+name+".music.png",
                "--out_spectrogram",  result_path+name+".spec.png",
                "--out_setting",      result_path+name+".config.json",
                "--out_localization", result_path+name+".loc.json",
                tf_path, src_path,
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

def convert_tl2events(tl,interval):
    #[{"id": 0, "x": [0.0, 0.958, 0.287], "power": 1}],
    events={}
    current_time=0
    duration=interval
    prev_evt=set()
    for time_pt in tl:
        current_evt=set()
        for e in time_pt:
            current_evt.add(e["id"])
            if e["id"] not in events:
                events[e["id"]]={}
                events[e["id"]]["begin_time"]=current_time
                events[e["id"]]["point_list"]=[]
                events[e["id"]]["sep_audio_id"]= "0"
                events[e["id"]]["label"]= "None"
            pt={}
            pt["begin_time"]=current_time
            pt["direction"]=math.atan2(float(e["x"][1]),float(e["x"][0]))/math.pi*180
            pt["duration"]=duration
            pt["power"]=e["power"]
            events[e["id"]]["point_list"].append(pt)
        for removed_id in prev_evt-current_evt:
            events[removed_id]["end_time"]=current_time
        current_time+=interval
    for removed_id in current_evt:
        events[removed_id]["end_time"]=current_time
    event_list=[]
    for k,v in events.items():
        v["localization_id"]=k 
        event_list.append(v)
    return event_list

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
                obj["power"]=current_pt["power"]
                obj["id"]=loc_id
                timeline[tl_idx].append(obj)
    return timeline


@localization_namespace.route('/result/<int:worker_id>')
class LocalizationResult(Resource):
    @localization_namespace.marshal_with(localization_result)
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
            out_localization = result_path+name+".loc.json"
            
            obj={}
            obj["localization"]={}
            obj["localization"]["audio_id"]=""
            obj["localization"]["name"]=name
            obj["localization"]["event_list"]=[]
            if os.path.exists(out_localization):
                print("[LOAD]",out_localization)
                loc_obj=json.load(open(out_localization))
                interval=loc_obj["interval"]
                tl=loc_obj["tl"]
                obj["localization"]["event_list"]=convert_tl2events(tl,interval)
            obj["spec_img"]= out_spectrogram
            obj["spatial_img"]= out_fig
            return obj, 200
 
@localization_namespace.route('/log/<int:worker_id>')
class LocalizationLog(Resource):
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

       

@localization_namespace.route('/worker/<int:worker_id>')
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

