# AudioSimpleAPI
# Using Docker
## build
```
cd AudioSimpleAPI
docker build . -t audioapi
```
## Run with port 5000
- Port 5000
- Original audio files in the following host directory: <sample_audio>
```
docker run -it --rm  -v  <sample_audio>:/AudioSimpleAPI/public/audio  -p 5000:5000 audioapi:latest
```
If necessary, you can mount the directories in `public/` using the `-v` option.


## Installation without docker
```
pip install -r requirements.txt
```
### Required commands
```
sudo apt-get install sox

```
### Usage
```
python app.py
```
