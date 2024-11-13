import os
import sys
import time
import json
import pickle
import re
import requests
import base64
from bs4 import BeautifulSoup
import tkinter as tk
from tkinter import filedialog
from colorama import init, Fore
import tempfile
import urllib.parse
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes
init()  # 初始化colorama
header = {
    'Accept-Encoding' : 'gzip, deflate',
    'Accept-Language' : 'zh-CN,zh;q=0.9',
    'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'}

ua={
   'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Safari/537.36'
}

coursedata = []
coursedatas = []
activates = []

def is_running_from_temp_directory():
    # 获取可执行文件的绝对路径
    exe_path = os.path.abspath(sys.executable)
    # 获取系统的临时目录路径
    temp_directory = tempfile.gettempdir()

    # 检查可执行文件的路径是否以系统临时目录开头
    if exe_path.startswith(temp_directory):
        return True
    return False

# 保存用户凭证到本地文件
def save_credentials(username, password, filename='账号信息'):
    with open(filename, 'wb') as f:
        # 将用户名和密码保存为pickle格式
        pickle.dump({'username': username, 'password': password}, f)

# 从本地文件加载用户凭证
def load_credentials(filename='账号信息'):
    if os.path.exists(filename):
        try:
            with open(filename, 'rb') as f:
                credentials = pickle.load(f)
                return credentials['username'], credentials['password']
        except (EOFError, KeyError):
            print("凭证文件为空或格式不正确。")
    else:
        print("凭证文件不存在。")
    return None, None
def load_coursedata(filename='coursedata.json'):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                coursedata = json.load(f)
                return coursedata
        except (json.JSONDecodeError, KeyError) as e:
            print(f"课程文件读取错误：{e}")
    else:
        print("课程文件不存在。")
    return None
# 弹出文件选择对话框，让用户选择文件
def select_file():
    # 创建 Tkinter 根窗口
    root = tk.Tk()
    # 隐藏根窗口
    root.withdraw()
    # 确保主窗口不会被关闭
    root.update()
    # 定义图片文件的扩展名
    file_types = [
        ('Image files', '*.jpg *.jpeg *.png *.gif'),
        ('All files', '*.*')
    ]
    # 弹出文件选择对话框，只显示图片文件类型
    file_path = filedialog.askopenfilename(filetypes=file_types)
    # 完成后关闭根窗口
    root.destroy()
    return file_path

# 登录函数，使用用户名和密码进行登录
def login(username, password):
    
    # 创建会话对象
    session = requests.Session()
    # 登录API URL
    url = 'https://passport2-api.chaoxing.com/v11/loginregister'
    # 构造登录请求数据
    data = {
        "cx_xxt_passport": "json",
        "roleSelect": "true",
        "uname": username,
        "code": password,
        "loginType": "1",
    }
    password=urllib.parse.quote(password)
    # 发送登录请求
    response = session.get(url, params=data,headers=header,verify=True,allow_redirects=False)
    # 解析响应结果
    account = response.json()
    mes = account.get('mes')
    return mes

# 登录函数，提交POST请求进行登录
def login_post(username, password, schoolid=None):
    # 创建会话对象
    session = requests.Session()
    password=urllib.parse.quote(password)
    # 发送登录请求
    r = session.post('http://passport2.chaoxing.com/api/login?name={}&pwd={}&schoolid={}&verify=0'.format(username, password, schoolid),headers=header,verify=True, allow_redirects=False)
    # 解析响应结果
    name = json.loads(r.text)['realname']
    uid = json.loads(r.text)['uid']
    schoolid = json.loads(r.text)['schoolid']
    return session, name, schoolid, uid

# 获取用户PUID
def get_puid():
    # 请求PUID API URL
    url = 'https://sso.chaoxing.com/apis/login/userLogin4Uname.do'
    # 发送请求并解析响应
    response = session.get(url, headers=header,verify=True, allow_redirects=False)
    data = response.json()
    try:
        puid = data["msg"]["puid"]
        return puid
    except KeyError:
        print("未能获取到puid，响应数据可能不包含'msg'键，或者'msg'键的值不包含'puid'。")
        # 打印出响应的JSON数据来帮助调试
        print(data)
        return None

# 获取Token
def Token():
    # Token API URL
    url = 'https://pan-yz.chaoxing.com/api/token/uservalid'
    # 发送请求并解析响应
    response = session.get(url, headers=header,verify=True, allow_redirects=False)
    data = response.json()
    return data["_token"]

# 上传文件对象
def obj(token, puid, file):
    # 构造文件对象
    files = {
        "file": ("file.png", open(file, "rb"))  # 打开文件用于读取二进制数据
    }
    # 构造请求数据
    data = {
        "puid": puid
    }
    # 发送文件上传请求
    u = session.post('https://pan-yz.chaoxing.com/upload?_token={}'.format(token), data=data, files=files, headers=header,verify=True, allow_redirects=False)
    # 解析响应
    r = json.loads(u.text)
    if r['result']:
        object_id = r['objectId']  # 提取objectId
        print(f'图片上传成功，objectId: {object_id}')
        return object_id
    else:
        print(f'图片上传失败，页面提示: {r["msg"]}')
        return None

# 获取课程列表
def get_data():
    url1='https://mooc1-api.chaoxing.com/mycourse/backclazzdata?view=json&rss=1'
    response1 = session.get(url1, headers=header, verify=True, allow_redirects=False)
    data = response1.json()
    course_details = []

# 遍历每个课程条目
    if 'channelList' in data:
            for item in data['channelList']:
                group_id = item['key']  # 获取 group ID
                course_data = item['content'].get('course', {}).get('data', [])
                if course_data:  # 确保课程数据存在
                    for course in course_data:
                        course_id = course.get('id', '未提供课程ID')  # 获取 courseId
                        course_name = course.get('name', '未提供课程名称')  # 获取课程名称
                        course_details.append({
                            'name': course_name,  # 课程组名称
                            'classid': group_id,      # 课程组 ID
                            'courseid': course_id       # 课程 ID
                        })
    with open('coursedata.json', 'w', encoding='utf-8') as file:
        json.dump(course_details, file, indent=4, ensure_ascii=False)

def selected_course(coursedata):
    for index, course in enumerate(coursedata):
            print(f"{index + 1}: {course['name']}")

        # 用户选择课程
    course_index = int(input("请输入课程的序号来获取详细信息: ")) - 1
    if 0 <= course_index < len(coursedata):
        selected_course = coursedata[course_index]
        return selected_course
    else:
        print("输入的序号无效！")
# 获取签到码
def signCode(aid, session, header):
    # 签到码API URL
    url = 'https://mobilelearn.chaoxing.com/widget/sign/pcTeaSignController/showSignInfo'
    params = {
        'activeId': aid
    }
    # 发送请求并解析响应
    r = session.get(url, params=params, headers=header,verify=True, allow_redirects=False)
    html_data = r.text
    # 使用正则表达式查找签到码
    match = re.search(r'<input type="hidden" id="signCode" value="(\d+)"\s*/?>', html_data)
    if match:
        return match.group(1)  # 提取签到码
    else:
        return None

# 执行预签到
def YQD(aid, courseId, classId, uid):
    # 预签到API URL
    url = 'https://mobilelearn.chaoxing.com/newsign/preSign'
    # 构造请求数据
    data = {
        'activePrimaryId': aid,
        'courseId': courseId,
        'classId': classId,
        'uid': uid,
        'appType': '15',
        'general': '1',
        'sys': '1',
        'ls': '1',
        'tid': '',
        'ut': 's',
    }
    # 发送请求并解析响应
    r = session.get(url, params=data, headers=header,verify=True, allow_redirects=False)
    # 使用BeautifulSoup解析HTML
    soup = BeautifulSoup(r.text, 'html.parser')
    # 查找id为'statuscontent'的<h1>标签
    status_content = soup.find('h1', id='statuscontent')
    # 如果找到标签，提取标签的文本内容；如果没有找到，返回空字符串
    is_ok = status_content.get_text(strip=True) if status_content else None
    return is_ok
def aes_encrypt(mode='CBC'):
    plaintext = os.urandom(16).hex()
    key = os.urandom(32).hex()
    key = key.encode('utf-8')[:32]
    iv = get_random_bytes(16)
    cipher = AES.new(key, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext.encode(), AES.block_size))
    ciphertext_b64 = base64.b64encode(ciphertext).decode('utf-8')
    return ciphertext_b64
# 执行签到
def QD(aid, uid, name, schoolid, validate=None,sign_code=None, latitude=None, longitude=None, address=None, objectId=None, enc=None):
    # 签到API URL
    url = 'https://mobilelearn.chaoxing.com/pptSign/stuSignajax'
    # 构造请求数据
    data = {
        "activeId": aid,
        "uid": uid,
        "fid": schoolid,
        "name": name,
        "signCode": sign_code,
        "enc": enc,
        "ifTiJiao": "1",
        "latitude": latitude,
        "longitude": longitude,
        'address': address,
        'objectId': objectId,
        "ifTiJiao" : "1",
        "vpProbability":0,
        "vpStrategy" : "",
        "deviceCode": aes_encrypt(),
        'validate':validate
    }
    # 使用POST请求发送数据并打印响应
    r = session.post(url, data=data, headers=header,verify=True, allow_redirects=False)
    print(r.text)

# 获取活动列表

def active_get(fid, courseId, classId):
    url = f'https://mobilelearn.chaoxing.com/v2/apis/active/student/activelist?fid={fid}&courseId={courseId}&classId={classId}'
    response = session.get(url, headers=header, verify=True, allow_redirects=False)
    if response.status_code == 200:
        data = response.json()  # 解析响应为JSON
        active_list = data.get('data', {}).get('activeList', [])
        # 正则表达式匹配 "YYYY-MM-DD HH:MM:SS" 或 "MM-DD HH:MM" 格式
        time_pattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}|\d{2}-\d{2} \d{2}:\d{2}')
        # 提取需要的信息，仅当 otherId 不为空且 nameFour 不匹配日期时间格式时
        extracted_data = []
        for activity in active_list:
            if activity.get('otherId') and not time_pattern.match(activity.get('nameFour', '')):
                extracted_info = {
                    'otherId': activity['otherId'],
                    'id': activity['id'],
                    'nameFour': activity['nameFour'],
                    'nameOne': activity['nameOne']
                }
                extracted_data.append(extracted_info)
        
        return extracted_data
    else:
        # 处理错误的情况
        print(f"Error: HTTP {response.status_code}")
        return None

def display_activities(fid, courseId, classId):
    activities = active_get(fid, courseId, classId)
    if activities is not None:
        os.system('cls' if os.name == 'nt' else 'clear')
        print("\n可用的活动列表：")
        for index, activity in enumerate(activities):
            print(f"{index + 1}. {activity['nameFour']} ({activity['nameOne']})")
        print("0. 返回到课程选择")
        # 获取用户输入
        try:
            choice = int(input("\n请输入你需要签到的活动序号：")) - 1
            if choice == -1:
                return None  # 用户选择返回
            elif 0 <= choice < len(activities):
                return activities[choice]
            else:
                print("选择无效，请重试。")
        except ValueError:
            print("输入错误，请输入数字。")
    else:
        print("没有可用的活动或发生了错误。")
    return None


# 执行刷新操作
def SX(aid):
    # 刷新API URL
    url = f'https://mobilelearn.chaoxing.com/v2/apis/active/getPPTActiveInfo?activeId={aid}&duid=&denc='
    # 发送请求并解析响应
    r = session.get(url, headers=header,verify=True, allow_redirects=False)
    if r.status_code == 200:
        data = r.json()
        if data.get("result") == 1 and "data" in data and "otherId" in data["data"]:
            otherId = data["data"]["otherId"]
            if otherId == 0:
                return otherId, data["data"]["ifphoto"]
            else:
                return otherId, None
    return None, None


# 手动输入经纬度坐标
def input_coordinates(prompt):
    while True:
        try:
            coordinates_input = input(prompt)
            latitude, longitude = [float(coord.strip()) for coord in coordinates_input.split(',')]
            return latitude, longitude
        except ValueError:
            print(Fore.RED + "输入格式不正确或不是有效的数字，请按照 '纬度,经度' 的格式重新输入，例如 '116.403514,39.921714'。" + Fore.RESET)





if __name__ == "__main__":
    if is_running_from_temp_directory():
        print(Fore.RED + "检测到程序可能正在从压缩包中运行，请解压后再使用。"+ Fore.RESET)
        input()
        sys.exit()
    else:
        print("程序正常启动。")
    # 格式化当前时间
    formatted_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    attempts = 0
    max_attempts=3
    # 尝试加载保存的凭证
    while True:
        # 尝试加载保存的凭证
        user, pwd = load_credentials()
        
        if user and pwd:
            # 使用保存的凭证尝试登录
            mes= login(user, pwd)
            if mes != "验证通过":  # 假设mes为"验证通过"表示登录成功
                print(f'登录失败，返回信息：{mes}')
                attempts += 1
                if attempts >= max_attempts:
                    input('密码错误3次，按任回车退出。')
                    sys.exit()
                continue
            else:
                session, name, schoolid, uid = login_post(user, pwd)
                print("登录成功！")
                time.sleep(1)
                os.system('cls' if os.name == 'nt' else 'clear')
                break  # 登录成功，退出循环
        else:
            # 如果没有保存的凭证或者登录失败，提示用户输入新的凭证
            user = input('请输入账号：')
            pwd = input('请输入密码：')
            mes = login(user, pwd)
            if mes != "验证通过":  # 假设mes为"验证通过"表示登录成功
                print(f'登录失败，返回信息：{mes}')
                continue  # 登录失败，继续循环
            else:
                save_credentials(user, pwd)
                session, name, schoolid, uid = login_post(user, pwd)
                print("登录成功！")
                time.sleep(1)
                os.system('cls' if os.name == 'nt' else 'clear')
                break  # 登录成功，退出循环
    print('等待课程数据加载完成...')
    get_data()
    while True:
        os.system('cls' if os.name == 'nt' else 'clear')
        coursedata = load_coursedata()
        if coursedata is None:
            print("加载课程数据失败。")
            continue  # 如果数据加载失败，重新开始循环

        course_selection = selected_course(coursedata)  # 假设选择课程的函数名为 select_course
        if course_selection is None:
            print("未选择有效课程。")
            continue  # 如果没有有效的课程，重新开始循环
        
        selected_activity = display_activities(schoolid, course_selection['courseid'], course_selection['classid'])
        if selected_activity is None:
            continue  # 如果用户选择返回，重新开始循环

        # 从这点开始，selected_activity 已经被确认不为 None
        other_id = selected_activity['otherId']
        if selected_activity['id'] is not None:
            pas = YQD(selected_activity['id'], course_selection['courseid'], course_selection['classid'], uid)
            if pas != "签到成功":  # 假设"已签到"是成功签到的标志
                other_id, ifp_id = SX(selected_activity['id'])  # 调用SX函数获取otherId和ifp_id

                # 根据other_id的值执行不同的签到流程
                if other_id in [3, 5]:
                    print('当前为手势或验证码签到')
                    print('签到码&手势为:',None)
                    QD(selected_activity['id'], uid, name, schoolid,None,None)
                elif other_id == 4:
                    print('当前为位置签到')
                    print(Fore.RED + "未能成功获取到位置信息，请手动输入。" + Fore.RESET)
                    address = input('位置名：')
                    longitude, latitude = input_coordinates('可以前往https://api.map.baidu.com/lbsapi/getpoint/获取,\n请输入纬度和经度，用逗号分隔(例如 106.672333,30.467109):')
                    QD(selected_activity['id'], uid, name, schoolid, None, None, latitude, longitude, address)
                elif other_id == 0:
                    if ifp_id == 1:
                        print('当前为拍照签到')
                        file = select_file()
                        jpg_a = obj(Token(), get_puid(), file=file)
                        QD(selected_activity['id'], uid, name, schoolid, None, objectId=jpg_a)
                    else:
                        print('当前为普通签到')
                        QD(selected_activity['id'], uid, name, schoolid, None)
                elif other_id == 2:
                    print(Fore.RED + "暂不支持的签到类型。" + Fore.RESET)
                else:
                    print(Fore.RED + "未知类型活动。" + Fore.RESET)
            else:
                print("返回类型:", pas)
            input("按回车键返回课程列表。")
