cd /PyTaskManager-master/master
python TaskMaster.py &

cd ../client
sleep 10

python FileService.py &

sleep 5

python runScript.py