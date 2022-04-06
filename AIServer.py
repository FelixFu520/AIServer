import os
import sys
import hashlib
from loguru import logger
import eventlet
import socketio

sys.path.append(os.path.dirname(os.path.abspath(__file__)))  # 添加当前目录
from system import *
from dtede import *


__all__ = ['AIServer']


def checkLicense():
    # get mac & SN
    macAddr_SN = []
    licensePath = os.path.join("/ai/AIServer/LICENSE")
    if not os.path.exists(licensePath):  # 不存在LICENSE 文件
        logger.error("No LICENSE in {}".format(licensePath))
        return

    with open(licensePath, 'r') as licenseFile:
        for line in licenseFile.readlines():
            macAddr_SN.append(line.strip())

        logger.info("The MAC Address is {}".format(macAddr_SN[0]))
        logger.info("The SN is {}".format(macAddr_SN[1]))

    # check license
    m = hashlib.md5()
    m.update((macAddr_SN[0] + "AIServer_made_by_FelixFu").encode('utf-8'))
    if macAddr_SN[1] == m.hexdigest():
        logger.info("The SN is right, starting AIServer now .....")
        return True
    else:
        logger.error("The SN is error, can't start AIServer !!!!")
        return False


def AIServer(port=4444):
    log_path = os.path.join(os.path.dirname(__file__), 'logs', "log.txt")
    logger.add(log_path, format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {message}")
    if not checkLicense():  # 检查服务器证书，如果证书错误，返回
        return
    logger.info("............Started AIServer now............")
    sio = socketio.Server()
    # 1. 监听linuxServer
    sio.register_namespace(linuxServer('/linuxServer'))
    # 2. 监听Dataset
    sio.register_namespace(dataServer('/dataServer'))
    # 3. 监听train
    sio.register_namespace(trainServer('/trainServer'))
    # # 4. 监听eval
    # sio.register_namespace(evalServer('/eval'))
    # # 5. 监听demo
    # sio.register_namespace(demoServer('/demo'))
    # # 6. 监听onnx
    # sio.register_namespace(onnxServer('/onnx'))
    # # 7. 监听exportc
    # sio.register_namespace(exportcServer('/exportc'))

    app = socketio.WSGIApp(sio, static_files={
        '/': {'content_type': 'text/html', 'filename': 'index.html'}
    })
    eventlet.wsgi.server(eventlet.listen(('', port)), app)

