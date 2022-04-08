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


class trainServer(socketio.Namespace):
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
        if not os.path.exists(ckptPath):
            return []
        allCkptPath = [file_ for file_ in os.listdir(ckptPath) if file_ == "best_ckpt.pth"]
        return allCkptPath

    def on_uploadFile(self, sid, data):
        """
        已废弃
        :param sid:
        :param data:
        :return:
        """
        SEPARATOR = "<SEPARATOR>"
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
        """
        已废弃
        :param sid:
        :param data:
        :return:
        """
        SEPARATOR = "<SEPARATOR>"
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
        gpu_str = data['gpu_str']
        devices_num = data['devices_num']

        json_str = json.dumps(configDict, indent=4)
        logPath = os.path.join("/ai/data/AILogs", sn, taskType, modelName, projectName, configName).replace('\\','/')
        os.makedirs(logPath, exist_ok=True)
        jsonPath = os.path.join(logPath, 'config.json')
        with open(jsonPath, 'w') as json_file:
            json_file.write(json_str)

        # print(f"TWO:{gpu_str} nohup /usr/bin/python /ai/AICore/main.py --num_machines 1 --machine_rank 0 --devices {devices_num} -c {jsonPath} &")
        # res = subprocess.Popen(
        #     f"{gpu_str} nohup /usr/bin/python /ai/AICore/main.py --num_machines 1 --machine_rank 0 --devices {devices_num} -c {jsonPath} &",
        #     shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        logger.info(f"ONE:{gpu_str} /usr/bin/python /ai/AICore/main.py --num_machines 1 --machine_rank 0 --devices {devices_num} -c {jsonPath}")
        res = subprocess.Popen(
            f"{gpu_str} NCCL_DEBUG=INFO /usr/bin/python /ai/AICore/main.py --num_machines 1 --machine_rank 0 --devices {devices_num} -c {jsonPath}",
            shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        # train_log = os.path.join(logPath, "train_log.txt")
        # print(f"{gpu_str} NCCL_DEBUG=INFO nohup python /ai/AICore/main.py --num_machines 1 --machine_rank 0 --devices {devices_num} -c {jsonPath} {train_log} 2>&1 &")
        # res = subprocess.Popen(
        #     f"{gpu_str} NCCL_DEBUG=INFO nohup python /ai/AICore/main.py --num_machines 1 --machine_rank 0 --devices {devices_num} -c {jsonPath} {train_log} 2>&1 &",
        #     shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return res.pid

    def on_getLog(self, sid, data):
        logger.info("trainServer----sid:{} getLog".format(sid))
        SN = data['sn']
        taskType = data['taskType']
        modelName = data['modelName']
        projectName = data['projectName']
        configName = data['configName']
        allLog = data['allLog']
        logPath = os.path.join("/ai/data/AILogs", SN, taskType, modelName, projectName, configName)
        if not os.path.exists(logPath):
            return []
        if allLog:
            alllogPath = [file_ for file_ in os.listdir(logPath)]
        else:
            alllogPath = [file_ for file_ in os.listdir(logPath) if not file_.endswith("pth")]
        return alllogPath
