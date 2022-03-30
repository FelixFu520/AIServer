# -*- coding: utf-8 -*-
# @Author:FelixFu
# @Date: 2021.4.14
# @GitHub:https://github.com/felixfu520
# @Copy From:
import os
import pickle
import nvgpu
import subprocess
from loguru import logger

import eventlet
import socketio

__all__ = ['linuxServer']


class linuxServer(socketio.Namespace):
    def on_connect(self, sid, environ):
        logger.info("sid:{} connected".format(sid))
        # logger.info("{} environ:".format(environ))

    def on_disconnect(self, sid):
        logger.info("sid:{} disconnect".format(sid))
        self.emit("message_disconnect", {'status': 0, 'data': None})

    def on_addServer(self, sid):
        logger.info("sid:{} addServer".format(sid))
        self.emit("message_addServer", {'status': 0, 'data': None})

    def on_smi(self, sid):
        logger.info("sid:{} exec command(nvidia-smi)".format(sid))
        # 获取nvidia-smi命令的结果，并存储到result中，返回给message_smi方法
        res = subprocess.Popen("nvidia-smi", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = []
        for line in res.stdout.readlines():
            line = bytes.decode(line)
            result.append(line.strip())
        self.emit('message_smi', {'status': 0, 'data': pickle.dumps(result)})

    def on_top(self, sid):
        logger.info("sid:{} exec command(top)".format(sid))
        # 获取nvidia-smi命令的结果，并存储到result中，返回给message_smi方法
        res = subprocess.Popen("top -b -n 1", shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        result = []
        for line in res.stdout.readlines():
            line = bytes.decode(line)
            result.append(line.strip())
        self.emit('message_top', {'status': 0, 'data': pickle.dumps(result)})

    def on_availableGpu(self, sid):
        logger.info("linuxServer----sid:{} exec command(nvgpu.available_gpus())".format(sid))
        gpus = nvgpu.available_gpus()  # 获取可用GPUs
        return gpus

    def on_makeDirs(self, sid, data):
        logger.info("linuxServer----sid:{} exec command(os.makedirs())".format(sid))
        path = data['path']
        try:
            os.makedirs(path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(e)
            return False


if __name__ == "__main__":
    port = 8888
    sio = socketio.Server()
    sio.register_namespace(linuxServer('/linuxServer'))
    app = socketio.WSGIApp(sio, static_files={
        '/': {'content_type': 'text/html', 'filename': 'index.html'}
    })
    eventlet.wsgi.server(eventlet.listen(('', port)), app)
