import configparser
import os, shutil
import time
import zipfile
from ftplib import FTP


def getFileAll(fileDir):
    allFileList = []
    for root, dirs, files in os.walk(fileDir):
        for file in files:
            allFileList.append(os.path.join(root, file))
    return allFileList


def zip_ya(startdir, file_news):
    z = zipfile.ZipFile(file_news, 'w', zipfile.ZIP_DEFLATED)  # 参数一：文件夹名
    for dirpath, dirnames, filenames in os.walk(startdir):
        fpath = dirpath.replace(startdir, '')  # 这一句很重要，不replace的话，就从根目录开始复制
        fpath = fpath and fpath + os.sep or ''  # 这句话理解我也点郁闷，实现当前文件夹以及包含的所有文件的压缩
        for filename in filenames:
            z.write(os.path.join(dirpath, filename), fpath + filename)
    z.close()


def copyFile2BasePath(allFileList, basePath, log):
    path = basePath + "\\dbupdate"
    isExists = os.path.exists(path)

    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)

    num = 0

    for x in allFileList:
        log.write(getTime() + "开始生成" + x)
        log.write('\n')
        num = num + 1
        # 只判断以sql结尾的，其他直接复制
        if x.endswith(".sql") == False:
            log.write(getTime() + "不是sql文件，直接复制" + x)
            log.write('\n')
            fileName = x.split('\\')[-1]
            shutil.copyfile(x, basePath + "\\dbupdate\\" + fileName)
            continue
        try:
            idx = str(num)
            if num < 10:
                idx = "0" + str(num)

            fileName = idx + "_" + x.split('\\')[-2] + "_" + x.split('\\')[-1]

            old = open(x, "r", encoding='UTF-8')
            fileName = fileName.replace('.sql', '_ora.sh')
            f = open(basePath + "\\dbupdate\\" + fileName, "w", encoding='gbk')
            f.write("#!/bin/bash")
            f.write('\n')
            f.write("source ~/.bash_profile")
            f.write('\n')
            f.write("DB_USERID=$DBUSER/$DBPASSWD")
            f.write('\n')
            f.write("export NLS_LANG='SIMPLIFIED CHINESE_CHINA.ZHS16GBK'")
            f.write('\n')
            f.write("sqlplus ${DB_USERID} <<!")
            f.write('\n')
            text_lines = old.readlines()
            for line in text_lines:
                f.write(line)

            f.write('\n')
            f.write("!")
            f.close()
            old.close()
            log.write(getTime() + "生成成功" + x)
            log.write('\n')
        except Exception as e:
            log.write("生成异常" + x + e)
            log.write('\n')


def turn(file):
    with open(file, 'rb') as f:
        data = f.read()
        encoding = 'gbk'
        # chardet.detect(data)['encoding']
        data_str = data.decode(encoding)
        tp = 'LF'
        if '\r\n' in data_str:
            tp = 'CRLF'
            data_str = data_str.replace('\r\n', '\n')
        if encoding not in ['UTF-8', 'ascii'] or tp == 'CRLF':
            with open(file, 'w', newline='\n') as f:
                f.write(data_str)
            print(f"{file}: ({tp},{encoding}) trun to (LF,utf-8) success!")


def sftp(basePath, log):
    config = configparser.ConfigParser()
    # -read读取ini文件
    file = basePath + '\\config.ini'
    if os.path.exists(file) == False:
        return
    config.read(file, encoding='GB18030')

    tranflag = config.get('ftp', 'tranflag')
    if tranflag == '0':
        log.write("不上传到FTP")
        log.write('\n')
        return

    host = config.get('ftp', 'host')
    port = config.get('ftp', 'port')
    username = config.get('ftp', 'username')
    password = config.get('ftp', 'password')
    remotepath = config.get('ftp', 'remotepath')

    localfile = basePath + '\\dbupdate.zip'

    log.write("开始上传到FTP服务器" + host)
    log.write('\n')
    ftp = FTP()
    ftp.connect(host, int(port))
    ftp.login(username, password)
    ftp.rmd(remotepath)  # 删除远程目录
    ftp.mkd(remotepath)  # 新建远程目录
    ftp.cwd(remotepath)
    fd = open(localfile, 'rb')
    ftp.storbinary('STOR %s' % os.path.basename(localfile), fd)
    fd.close()
    log.write("上传到FTP服务器完成" + host)
    log.write('\n')
    ftp.quit()


def genSqlCmd(basePath):
    f = open(basePath + "\\genHis.log", "a")
    f.write(
        "==================================================" + getTime() + "开始==================================================")
    f.write('\n')
    f.write("basePath:" + basePath)
    f.write('\n')

    file = basePath + "\\dbupdate.zip"
    if os.path.exists(file):
        os.remove(file)

    file = basePath + "\\dbupdate"
    if os.path.exists(file):
        shutil.rmtree(file)
    f.write("删除已经生成的压缩包")
    f.write('\n')
    # 获得origin文件列表
    allFileList = getFileAll(basePath + "\\origin")
    f.write("获得origin文件列表")
    f.write('\n')
    # 创建dbupdate目录，并将origin文件夹下的文件全部复制到当前目录下
    copyFile2BasePath(allFileList, basePath, f)
    f.write("创建dbupdate目录，并将origin文件夹下的文件全部复制到当前目录下")
    f.write('\n')
    # 修改data下面文件编码格式
    dataFileList = getFileAll(basePath + "\\dbupdate")
    for x in dataFileList:
        if x.endswith(".sh") == False:
            f.write("不是sh文件，跳过" + x)
            f.write('\n')
            continue
        turn(x)
        f.write("编码格式转化" + x + "完成")
        f.write('\n')
    # 压缩data文件夹
    startdir = basePath + "\\dbupdate"  # 要压缩的文件夹路径
    file_news = startdir + '.zip'  # 压缩后文件夹的名字
    zip_ya(startdir, file_news)
    f.write("压缩dbupdate文件夹")
    f.write('\n')

    # 删除dbupdate文件夹
    file = basePath + "\\dbupdate"
    shutil.rmtree(file)
    sftp(basePath, f)
    # 提示成功消息
    f.write(getTime() + "数据库更新包生成成功")
    print(getTime() + "数据库更新包生成成功")
    f.write('\n')
    f.write(
        "--------------------------------------------------" + getTime() + "结束--------------------------------------------------")
    f.write('\n')
    f.close


def getTime():
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())) + " "


basePath = os.getcwd()
# basePath = "D:\\2021\\202101\\14"
genSqlCmd(basePath)
