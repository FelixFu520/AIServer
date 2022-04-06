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
import zipfile
import subprocess
import json
from loguru import logger

__all__ = ['dataServer']


class dataServer(socketio.Namespace):
    def on_connect(self, sid, environ):
        logger.info("dataServer----sid:{} connected".format(sid))
        # logger.info("{} environ:".format(environ))

    def on_disconnect(self, sid):
        logger.info("dataServer----sid:{} disconnect".format(sid))
        # self.emit("message_disconnect", {'status': 0, 'data': None})

    def on_allDatasetsByTaskTypeSN(self, sid, data):
        """
        返回 /ai/data/AIDatasets/taskType/SN下的所有数据集列表
        """
        logger.info("dataServer----sid:{} getDatasets".format(sid))
        dataset_path = os.path.join("/ai/data/AIDatasets", data['taskType'], data['SN'])
        all_datasets = [folder for folder in os.listdir(dataset_path) if os.path.isdir(os.path.join(dataset_path, folder))]
        return all_datasets

    def on_unzipFile(self, sid, data):
        """
        解压文件
        :param sid:
        :param data:
        :return:
        """
        logger.info("dataServer----sid:{} unzipFile".format(sid))
        try:
            fileName = data['fileName']  # 文件名
            remotePath = data['remotePath']  # 服务器位置
            removeOri = data['removeOri']   # 是否删除原zip文件

            zipPath = os.path.join(remotePath, fileName)
            if zipfile.is_zipfile(zipPath):
                with zipfile.ZipFile(zipPath, 'r') as zipf:
                    zipf.extractall(remotePath)
            #
            # cmd = "unzip -O CP936 -q -o {} -d {}".format(os.path.join(remotePath, fileName), remotePath)
            # os.system(cmd)
            # if removeOri:
            #     cmd_ = "rm -r {}".format(os.path.join(remotePath, fileName.split(".")[0]))
            #     os.system(cmd_)
            return True, "unzip success"
        except Exception as e:
            logger.error("unzip error " + str(e))
            return False, str(e)


    def on_deleteDatasetServer(self, sid, data):
        """
        删除dataset
        :param sid:
        :param data:
        :return:
        """
        logger.info("dataServer----sid:{} deleteDatasetServer".format(sid))
        try:
            removePath = data['removePath']
            logger.info("rm -r {}".format(removePath))
            os.system("rm -r {}".format(removePath))
            return "successfully delete"
        except Exception as e:
            logger.error(str(e))
            return "delete failed"



