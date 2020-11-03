import os
import glob
import pickle
import pandas as pd
import librosa
import numpy as np
import time
from multiprocessing import Pool
import argparse
import json
from sklearn.manifold import TSNE
from sklearn.preprocessing import normalize
from sklearn.decomposition import PCA
import umap
import trimap

from sklearn.neighbors import KNeighborsClassifier
from sklearn.model_selection import cross_val_predict
import sklearn
import sklearn.metrics


from PIL import Image
with_loc_feature=False
def get_feature(filename,feature):
    try:
        print(filename)
        name,_ = os.path.splitext(filename)
        npy_path=name+".npy"
        feat=None
        if with_loc_feature and os.path.exists(npy_path):
            ## 10msec 16k
            feat=np.load(npy_path)
            feat=feat.transpose()
            #print("feat",feat.shape)
        y, sr = librosa.load(filename,sr=None)
        #print("y:",y.shape)
        #print("sr:",sr)
        n_sample=y.shape[-1]
        n_fft=2048
        hop_length=512
        duration=float(hop_length)*1000.0/sr
        if feature=="mfcc":
            mfcc_feature = librosa.feature.mfcc(y=y,sr=sr,n_mfcc=13)
            mfcc_delta = librosa.feature.delta(mfcc_feature)
            mfcc_deltadelta = librosa.feature.delta(mfcc_delta)
            f=np.vstack([mfcc_feature, mfcc_delta,mfcc_deltadelta])
            if feat is not None:
                im = Image.fromarray(feat)
                z=im.resize((f.shape[1],feat.shape[0]))
                feat=np.asarray(z)
                f=np.concatenate([feat,f],axis=0)
                return f,duration
            return f,duration
        elif feature=="mel":

            S = librosa.feature.melspectrogram(y, sr=sr, n_mels=128, )
            logS = librosa.amplitude_to_db(S, ref=np.max)
            if feat is not None:
                im = Image.fromarray(feat)
                z=im.resize((f.shape[1],feat.shape[0]))
                feat=np.asarray(z)
                f=np.concatenate([feat,f],axis=0)
                return f,duration
            return logS,duration
        elif feature=="mel2":
            S = librosa.feature.melspectrogram(y, sr=sr, n_mels=128)
            logS = librosa.amplitude_to_db(S, ref=np.max)
            logS_delta = librosa.feature.delta(logS)
            logS_deltadelta = librosa.feature.delta(logS)
            f=np.vstack([logS, logS_delta, logS_deltadelta])
            if feat is not None:
                #print("feat",feat.shape)
                im = Image.fromarray(feat)
                z=im.resize((f.shape[1],feat.shape[0]))
                feat=np.asarray(z)
                #print("feat",feat.shape)
                f=np.concatenate([feat,f],axis=0)
                #print("mel",f.shape)
                return f,duration
            #print("mel",f.shape)
            return f,duration
        elif feature=="spec":
            # win_length =n_fft
            # hop_length=win_length / 4
            D = librosa.stft(y,n_fft=1024,hop_length=None, win_length=None)
            log_power = librosa.amplitude_to_db(np.abs(D), ref=np.max)
            if feat is not None:
                im = Image.fromarray(feat)
                z=im.resize((f.shape[1],feat.shape[0]))
                feat=np.asarray(z)
                f=np.concatenate([feat,f],axis=0)
                return f,duration
            return log_power,duration
    except:
        print("[ERROR]",filename)
        return None,None

def make_sliding_window(X,window,limit_length):
    out_x=[]
    for i in range(len(X)):
        s=len(X[i])
        if limit_length is not None and limit_length<s:
            s=limit_length
        x=X[i][:s,:]
        dest=[]
        for j in range(s-window):
            dest.append(np.reshape(x[j:j+window,:],(-1,)))
        if len(dest)>0:
            out_x.append(np.array(dest))
    return out_x


def process(args):
    filename,evt,f=args
    if f=="":
        x,duration=get_feature(filename,"mel")
    else:
        x,duration=get_feature(filename,f)
    return (x,evt,duration)
    

def embedding(X,args):
    print("... preprocess: normalization and PCA")
    method=args.method
    preprocess_start_time = time.time()
    X=normalize(X)
    if X.shape[1]>20:
        prep_model=PCA(n_components=20)
        X=prep_model.fit_transform(X)
    preprocess_interval = time.time() - preprocess_start_time

    ##
    """
    print("... saving prepprocessed data")
    filename_x=output_path+"/"+feature+"_x.npy"
    filename_y=output_path+"/"+feature+"_y.npy"
    np.save(filename_x,X)
    np.save(filename_y,Y)
    """
    ##
    print("... embedding")
    embedding_start_time = time.time()
    if method=="song":
        import song
        model = song.song_.SONG(n_max_epoch=n_max_epoch,b=b)
        model.fit(X, Y)
        embedding=model.raw_embeddings[:,:]
    else:
        if method=="tsne":
            model = TSNE(n_components=2, random_state=42)
        elif method=="trimap":
            model = trimap.TRIMAP(n_iters=500)
        else:
            model = umap.UMAP()
        embedding = model.fit_transform(X)
    embedding_interval = time.time() - embedding_start_time
    print("Preprocess time\t{}\n".format(preprocess_interval))
    print("Embedding time\t{}\n".format(embedding_interval))
    return embedding


def main():
    #### argv check
    parser = argparse.ArgumentParser(
        description="applying the MUSIC method to am-ch wave file"
    )
    #### option for the MUSIC method
    parser.add_argument(
        "--config",
        metavar="C",
        type=str,
        default="config.json",
        help="config json",
    )
    parser.add_argument(
        "--feature",
        metavar="F",
        type=str,
        default="mel",
        help="feature: mel/mfcc",
    )
    parser.add_argument(
        "--name",
        metavar="F",
        type=str,
        default="default",
        help="output: save name",
    )
    parser.add_argument(
        "--resample",
        metavar="F",
        type=int,
        default=None,
        help="resample",
    )
    parser.add_argument(
        "--method",
        metavar="F",
        type=str,
        default="umap",
        help="method:umap/tsne/trimap",
    )
    args = parser.parse_args()
    if not args:
        quit()
    ###
    config=json.load(open(args.config))
    audio_id_list=config["audio_id_list"]
    event_list=None
    if "event_list" not in config:
        event_list=config["event_list"]
        if len(event_list)==0:
            event_list=None
    ###
    all_data=[]
    if event_list is None:
        for audio_id in audio_id_list:
            filename="public/"+audio_id
            all_data.append((filename,None,args.feature))
    else:
        for audio_id, evt in zip(audio_id_list,event_list):
            filename="public/"+audio_id
            all_data.append((filename,evt,args.feature))
    ###
    p = Pool(16)
    results=p.map(process, all_data)
    p.close()
    ###
    all_data_x=[]
    all_data_e=[]
    all_data_d=[]
    all_data_i=[]
    for i,r in enumerate(results):
        x,evt,d = r
        if x is not None:
            all_data_x.append(x)
            all_data_e.append(evt)
            all_data_d.append(d)
            all_data_i.append(i)

    all_data_x=make_sliding_window(all_data_x,window=1,limit_length=None)
    idx=[]
    begin_time=[]
    for (x,e,d,i) in zip(all_data_x,all_data_e,all_data_d,all_data_i):
        begin_time.append(np.arange(x.shape[1])*d)
        idx.append([i]*x.shape[1])
    out_x=np.concatenate(all_data_x,axis=1)
    out_x=np.transpose(out_x)
    out_i=np.concatenate(idx)
    out_t=np.concatenate(begin_time)
    result_path="public/result_embedding"
    np.save(result_path+"/"+args.name+"."+args.feature+".x.npy",out_x)
    np.save(result_path+"/"+args.name+"."+args.feature+".t.npy",out_t)
    np.save(result_path+"/"+args.name+"."+args.feature+".i.npy",out_i)
    ###########
    resample=args.resample
    if resample is not None:
        print("... resampling")
        idx=list(range(out_x.shape[0]))
        np.random.shuffle(idx)
        idx=idx[:resample]
        X=out_x[idx,:]
        T=out_t[idx,:]
        I=out_i[idx,:]
    else:
        X=out_x
        T=out_t
        I=out_i
    
    Z=embedding(X,args)
    
    np.save(result_path+"/"+args.name+"."+args.feature+"."+args.method+".z.npy",Z)
    print("Z",Z.shape)
    print("x",out_x.shape)


if __name__ == '__main__':
    main()

