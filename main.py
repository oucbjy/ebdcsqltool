import os,shutil
import zipfile

from pip._vendor import chardet

def getFileAll(fileDir):
    allFileList = []
    for root, dirs, files in os.walk(fileDir):
        for file in files:
            allFileList.append(os.path.join(root, file))
    return allFileList

def zip_ya(startdir,file_news):
    # startdir = ".\\123"  #要压缩的文件夹路径
    # file_news = startdir +'data.zip' # 压缩后文件夹的名字
    z = zipfile.ZipFile(file_news,'w',zipfile.ZIP_DEFLATED) #参数一：文件夹名
    for dirpath, dirnames, filenames in os.walk(startdir):
        fpath = dirpath.replace(startdir,'') #这一句很重要，不replace的话，就从根目录开始复制
        fpath = fpath and fpath + os.sep or ''#这句话理解我也点郁闷，实现当前文件夹以及包含的所有文件的压缩
        for filename in filenames:
            z.write(os.path.join(dirpath, filename),fpath+filename)
        print('压缩成功')
    z.close()

def copyFile2BasePath(allFileList, basePath):
    path = basePath + "\\data"
    isExists = os.path.exists(path)

    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)

        print(path + ' 创建成功')
    path = basePath + "\\data\\data"
    isExists = os.path.exists(path)

    # 判断结果
    if not isExists:
        # 如果不存在则创建目录
        # 创建目录操作函数
        os.makedirs(path)

        print(path + ' 创建成功')
    num = 0
    for x in allFileList:
        num = num + 1
        fileName = str(num) + "_" + x.split('\\')[-1]
        shutil.copyfile(x, basePath + "\\data\\data\\" + fileName)
        # print(x)

def turn(file):
    with open(file, 'rb') as f:
        data = f.read()
        encoding = chardet.detect(data)['encoding']
        data_str = data.decode(encoding)
        tp = 'LF'
        if '\r\n' in data_str:
            tp = 'CRLF'
            data_str = data_str.replace('\r\n', '\n')
        if encoding not in ['utf-8', 'ascii'] or tp == 'CRLF':
            with open(file, 'w', newline='\n', encoding='utf-8') as f:
                f.write(data_str)
            print(f"{file}: ({tp},{encoding}) trun to (LF,utf-8) success!")

def genSqlCmdTxt(dataFileList, basePath):
    # 打开一个文件
    f = open(basePath + "\\sqlcmd.sh", "a")

    f.write("#!/bin/sh")
    f.write('\n')
    f.write("path=$1")
    f.write('\n')
    f.write("user=$2")
    f.write('\n')
    f.write("password=$3")
    f.write('\n')
    f.write('\n\n')

    f.write("unzip ${path}/data.zip")
    f.write('\n')
    f.write("path=${path}/data")
    f.write('\n\n')

    for x in dataFileList:
        tmp = x.split('\\')[-1]
        f.write('echo "==============================' + tmp + ' start]=============================="')
        f.write('\n')
        print(x.split('\\')[-1])
        f.write("sqlplus ${user}/${password} <<EOF")
        f.write('\n')
        f.write("@${path}/" + tmp)
        f.write('\n')
        f.write("commit")
        f.write('\n')
        f.write("/")
        f.write('\n')
        f.write("exit")
        f.write('\n')
        f.write("EOF")
        f.write('\n')
        f.write('echo "------------------------------' + tmp + ' end ]------------------------------"')
        f.write('\n\n')
    f.close

def genSqlCmd(basePath):
    f = open(basePath + "\\genSqlCmd.log", "w")
    f.write("basePath:" + basePath)
    f.write('\n')
    #删除已经生成的sh和压缩包
    file = basePath + "\\sqlcmd.sh"
    if os.path.exists(file):
        os.remove(file)

    file = basePath + "\\data.zip"
    if os.path.exists(file):
        os.remove(file)

    file = basePath + "\\data"
    if os.path.exists(file):
        shutil.rmtree(file)
    f.write("删除已经生成的sh和压缩包")
    f.write('\n')
    #获得origin文件列表
    allFileList = getFileAll(basePath + "\\origin")
    f.write("获得origin文件列表")
    f.write('\n')
    #创建data目录，并将origin文件夹下的文件全部复制到当前目录下
    copyFile2BasePath(allFileList, basePath)
    f.write("创建data目录，并将origin文件夹下的文件全部复制到当前目录下")
    f.write('\n')
    #修改data下面文件编码格式
    dataFileList = getFileAll(basePath + "\\data\\data")
    for x in dataFileList:
        turn(x)
        print("编码格式转化" + x + "完成")
        f.write("编码格式转化" + x + "完成")
        f.write('\n')
    #压缩data文件夹
    startdir = basePath + "\\data"  # 要压缩的文件夹路径
    file_news = startdir + '.zip'  # 压缩后文件夹的名字
    zip_ya(startdir, file_news)
    f.write("压缩data文件夹")
    f.write('\n')
    #生成sqlcmd.sh文件内容
    dataFileList = getFileAll(basePath + "\\data")
    genSqlCmdTxt(dataFileList, basePath)
    f.write("生成sqlcmd.sh文件内容")
    f.write('\n')
    # 删除data文件夹
    file = basePath + "\\data"
    shutil.rmtree(file)
    f.write("删除data文件夹")
    f.write('\n')
    #设置sqlcmd文件编码格式
    turn(basePath + "\\sqlcmd.sh")
    # 将sh和data.zip压缩到dbupdate.zip
    # 创建文件夹dbupdate
    path = basePath + "\\dbupdate"
    isExists = os.path.exists(path)
    if not isExists:
        os.makedirs(path)

    # 复制文件到文件夹zip压缩到dbupdate下面去
    shutil.copyfile(basePath + "\\data.zip", basePath + "\\dbupdate\\data.zip")
    shutil.copyfile(basePath + "\\sqlcmd.sh", basePath + "\\dbupdate\\sqlcmd.sh")

    startdir = basePath + "\\dbupdate"  # 要压缩的文件夹路径
    file_news = startdir + '.zip'  # 压缩后文件夹的名字
    zip_ya(startdir, file_news)

    # 删除dbupdate文件夹
    file = basePath + "\\dbupdate"
    shutil.rmtree(file)

    f.write("将sh和data.zip压缩到dbupdate.zip")
    f.write('\n')
    #删除临时文件
    file = basePath + "\\sqlcmd.sh"
    if os.path.exists(file):
        os.remove(file)

    file = basePath + "\\data.zip"
    if os.path.exists(file):
        os.remove(file)
    f.write("删除sh和data.zip文件夹")
    f.write('\n')
    #提示成功消息
    print("生成成功")
    f.write("生成成功")
    f.write('\n')
    f.close

basePath = os.getcwd()
# basePath = "D:\\202101\\14"
genSqlCmd(basePath)