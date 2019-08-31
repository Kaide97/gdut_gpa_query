import json
from io import BytesIO
import base64
from Crypto.Cipher import AES
from PIL import Image
import requests


class Encrypt(object):
    @staticmethod
    def _pkcs7padding(text):
        """
        明文使用PKCS7填充
        最终调用AES加密方法时，传入的是一个byte数组，要求是16的整数倍，因此需要对明文进行处理
        :param text: 待加密内容(明文)
        :return:
        """
        bs = AES.block_size  # 16
        length = len(text)
        bytes_length = len(bytes(text, encoding='utf-8'))
        # tips：utf-8编码时，英文占1个byte，而中文占3个byte
        padding_size = length if (bytes_length == length) else bytes_length
        padding = bs - padding_size % bs
        # tips：chr(padding)看与其它语言的约定，有的会使用'\0'
        padding_text = chr(padding) * padding
        return text + padding_text

    @staticmethod
    def encrypt(key, content, mode=AES.MODE_ECB, result_encode="hex"):
        """
        AES加密
        key,iv使用同一个
        模式cbc
        填充pkcs7
        :param result_encode:
        :param mode: 加密类型
        :param key: 密钥
        :param content: 加密内容
        :return:
        """
        key_bytes = bytes(key, encoding='utf-8')
        if mode == AES.MODE_ECB:
            cipher = AES.new(key_bytes, mode)
        else:
            iv = key_bytes
            cipher = AES.new(key_bytes, mode, iv)
        # 处理明文
        content_padding = Encrypt._pkcs7padding(content)
        # 加密
        encrypt_bytes = cipher.encrypt(bytes(content_padding, encoding='utf-8'))
        if result_encode == "hex":
            result = encrypt_bytes.hex()
        else:
            # 重新编码 base64
            result = str(base64.b64encode(encrypt_bytes), encoding='utf-8')
        return result


class GDUT_Class(object):
    def __init__(self):
        self._account = None
        self._password = None
        self._v_code = None
        self._gpa_data = None
        self._term_list = None
        self._session = requests.session()

    def login(self):
        self._account = input("学号: ")
        self._password = input("密码: ")
        self._get_v_code()
        key = str()
        for i in range(4):
            key += self._v_code
        encrypt_pwd = Encrypt.encrypt(key, self._password)
        print("account={}&pwd={}&verifycode={}".format(self._account, encrypt_pwd, self._v_code))
        header = {
            "Host": "222.200.98.147",
            "Connection": "keep-alive",
            "Content-Length": "70",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "Origin": "http://222.200.98.147",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.3704.400 QQBrowser/10.4.3587.400",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Referer": "http://222.200.98.147/",
            "Accept-Encoding": "gzip, deflate",
            "Accept-Language": "zh-CN,zh;q=0.9"
        }
        login_ret = self._session.post("http://222.200.98.147/new/login",
                                       data="account={}&pwd={}&verifycode={}".format(self._account, encrypt_pwd,
                                                                                     self._v_code), headers=header)
        print(login_ret.content.decode("utf-8"))

    def _get_v_code(self):
        v_code = self._session.get("http://222.200.98.147/yzm")
        b = BytesIO()
        b.write(v_code.content)
        Image.open(b).show()
        self._v_code = input("输入验证码: ")

    def _request_gpa_data(self):
        cj_ret = self._session.post("http://222.200.98.147/xskccjxx!getDataList.action?xnxqdm=&jhlxdm=&page=1&rows=100&sort=xnxqdm&order=asc")
        self._gpa_data = json.loads(cj_ret.content, encoding="utf-8")
        self._term_list = set()
        for r in self._gpa_data["rows"]:
            self._term_list.add(r["xnxqmc"])
        self._term_list = list(self._term_list)
        self._term_list.sort()

    def is_init(self):
        return self._gpa_data is not None

    def show_terms(self):
        print("以下为可以查询的学期: ")
        for i in range(1, len(self._term_list)+1):
            print("{} : {}".format(i, self._term_list[i - 1]))
        term = input("输入需要计算的学期(如:1 2,查询第一第二学期): ").split(" ")
        ret = []
        for r in term:
            ret.append(self._term_list[int(r) - 1])
        return ret

    def cal_gpa(self):
        if self._gpa_data is None:
            self._request_gpa_data()
        request_term = self.show_terms()
        ret = 0
        xf_total = 0
        for r in self._gpa_data["rows"]:
            if r["xnxqmc"] in request_term:
                xf_total += float(r["xf"])
                ret += float(r["xf"]) * float(r["cjjd"])
                #  cjjd 绩点 kcmc 课程名 xf 学分 xdfsmc 类型
                print("[课程名: {}-{} 学分: {}] 绩点: {}".format(r["kcmc"], r["xdfsmc"], r["xf"], r["cjjd"]))

        print("======== 您在选择的学期的绩点为: 【 {} 】 ========".format(round(ret / xf_total, 2)))


gdut = GDUT_Class()
gdut.login()
while True:
    if gdut.is_init() and "q" == input("回车继续查询,输入q退出"):
        break
    gdut.cal_gpa()
