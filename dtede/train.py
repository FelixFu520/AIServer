# -*- coding: utf-8 -*-
# @Author:FelixFu
# @Date: 2021.4.14
# @GitHub:https://github.com/felixfu520
# @Copy From:
import random
import socketio
import eventlet
from cryptography.fernet import Fernet
import os
import glob
import pickle
import shutil
import nvgpu
import subprocess
import json
from loguru import logger

__all__ = ['trainServer']
SEPARATOR = "<SEPARATOR>"


class trainServer(socketio.Namespace):
    def on_connect(self, sid, environ):
        logger.info("trainServer----sid:{} connected".format(sid))
        # logger.info("{} environ:".format(environ))

    def on_disconnect(self, sid):
        logger.info("trainServer----sid:{} disconnect".format(sid))
        # self.emit("message_disconnect", {'status': 0, 'data': None})

    def on_allDataset(self, sid, data):
        """
        返回 /ai/data/AIDatasets/taskType/SN下的所有数据集列表
        """
        logger.info("trainServer----sid:{} getDatasets".format(sid))
        dataset_path = os.path.join("/ai/data/AIDatasets", data['taskType'], data['SN'])
        all_datasets = [folder for folder in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, folder))]
        return all_datasets

    def on_allCkpt(self, sid, data):
        """
        返回/ai/data/AILogs/sn/taskType/modelName/projectName/configName下的所有日志（日期）
        """
        logger.info("trainServer----sid:{} allCkpt".format(sid))
        SN = data['SN']
        taskType = data['taskType']
        modelName = data['modelName']
        projectName = data['projectName']
        configName = data['configName']
        ckptPath = os.path.join("/ai/data/AILogs", SN, taskType, modelName, projectName, configName)
        allCkptPath = [folder for folder in os.listdir(ckptPath) if os.path.isdir(os.path.join(ckptPath, folder))]
        return allCkptPath

    def on_uploadFile(self, sid, data):
        #  {'filename': f"{filenameBase}{SEPARATOR}{counter}.part", 'data_bytes': bytes_read}
        SN = data['SN']
        taskType = data['taskType']
        modelName = data['modelName']
        projectName = data['projectName']
        ckptPath = os.path.join("/ai/data/AILogs", SN, taskType, modelName, projectName, "temp")
        os.makedirs(ckptPath, exist_ok=True)

        fileName = data['fileName']
        filename_to_return = fileName.split(SEPARATOR)[0]
        print(f"Receiving file {fileName}")
        with open(os.path.join(ckptPath, fileName), "wb") as f:
            # write to the file the bytes we just received
            f.write(data['data_bytes'])
        return filename_to_return

    def on_mergePart(self, sid, data):
        #  {'filename': f"{filenameBase}{SEPARATOR}{counter}.part", 'data_bytes': bytes_read}
        SN = data['SN']
        taskType = data['taskType']
        modelName = data['modelName']
        projectName = data['projectName']
        ckptPath = os.path.join("/ai/data/AILogs", SN, taskType, modelName, projectName, "temp")
        ckptPathDst = os.path.join("/ai/data/AILogs", SN, taskType, modelName, projectName, "weights")
        os.makedirs(ckptPathDst, exist_ok=True)

        fileName = data['fileName']
        print(os.path.join(ckptPath, fileName))
        if os.path.exists(os.path.join(ckptPath, fileName)):
            print(f"Merging {data['fileName']}")
        else:
            print(f"File {data['fileName']} not exists")
            return

        fileprefix = fileName.split(SEPARATOR)[0]
        numberFiles = fileName.split(SEPARATOR)[1].split(".")[0]
        filetowrite = fileName.split(SEPARATOR)[0]
        if os.path.exists(os.path.join(ckptPathDst,filetowrite)):
            os.remove(filetowrite)
        with open(os.path.join(ckptPathDst,filetowrite), "ab") as fileobjtowrite:
            for i in range(int(numberFiles)+1):
                splitFile = fileprefix+SEPARATOR+str(i)+".part"
                splitFilePath = os.path.join(ckptPath, splitFile)
                with open(splitFilePath, 'rb') as fileobjtoread:
                    fileobjtowrite.write(fileobjtoread.read())
                os.remove(splitFilePath)

    def on_train(self, sid, data):
        logger.info("trainServer----sid:{} train".format(sid))
        sn = data['sn']
        taskType = data['taskType']
        modelName = data['modelName']
        projectName = data['projectName']
        configName = data['configName']
        configDict = data['config']

        json_str = json.dumps(configDict, indent=4)
        logPath = os.path.join("/ai/data/AILogs", sn, taskType, modelName, projectName, configName).replace('\\','/')
        jsonPath = os.path.join(logPath, 'config.json')
        with open(jsonPath, 'w') as json_file:
            json_file.write(json_str)
        res = subprocess.Popen(f"nohup python /ai/DAO/main.py -c {os.path.join(jsonPath)} &", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return res