# -*- coding: utf-8 -*-
import json
import logging
import os
from random import sample
from string import ascii_letters, digits
import time
import uuid

from flask import Flask, jsonify, request

from wechatpayv3 import WeChatPay, WeChatPayType

# 微信支付商户号（直连模式）或服务商商户号（服务商模式，即sp_mchid)
MCHID = '167examlebyself586'

# 商户证书私钥
with open('/youpath/apiclient_key.pem') as f:
    PRIVATE_KEY = f.read()

# 商户证书序列号
CERT_SERIAL_NO = '19511you num'

# API v3密钥， https://pay.weixin.qq.com/wiki/doc/apiv3/wechatpay/wechatpay3_2.shtml
APIV3_KEY = 'NANyour serect'

# APPID，应用ID或服务商模式下的sp_appid
APPID = 'wx75youid'

# 回调地址，也可以在调用接口的时候覆盖
NOTIFY_URL = 'https://youurl'

# 微信支付平台证书缓存目录，减少证书下载调用次数，首次使用确保此目录为空目录。
# 初始调试时可不设置，调试通过后再设置，示例值:'./cert'。
# 新申请的微信支付商户号如果使用平台公钥模式，可以不用设置此参数。
CERT_DIR = None

# 日志记录器，记录web请求和回调细节
logging.basicConfig(filename=os.path.join(os.getcwd(), 'demo.log'), level=logging.DEBUG, filemode='a', format='%(asctime)s - %(process)s - %(levelname)s: %(message)s')
LOGGER = logging.getLogger("demo")

# 接入模式:False=直连商户模式，True=服务商模式
PARTNER_MODE = False

# 代理设置，None或者{"https": "http://10.10.1.10:1080"}，详细格式参见https://requests.readthedocs.io/en/latest/user/advanced/#proxies
PROXY = None

# 请求超时时间配置
TIMEOUT = (10, 30) # 建立连接最大超时时间是10s，读取响应的最大超时时间是30s

# 微信支付平台公钥
# 注：如果使用公钥模式初始化，需配置此参数。
#with open('path_to_wechat_pay_public_key/pub_key.pem') as f:
#    PUBLIC_KEY = f.read()

# 微信支付平台公钥ID
# 注：如果使用公钥模式初始化，需配置此参数。
#PUBLIC_KEY_ID = 'PUB_KEY_ID_444F4864EA9B34415...'

# 使用微信支付平台证书模式初始化。
wxpay = WeChatPay(
    wechatpay_type=WeChatPayType.NATIVE,
    mchid=MCHID,
    private_key=PRIVATE_KEY,
    cert_serial_no=CERT_SERIAL_NO,
    apiv3_key=APIV3_KEY,
    appid=APPID,
    notify_url=NOTIFY_URL,
    cert_dir=CERT_DIR,
    logger=LOGGER,
    partner_mode=PARTNER_MODE,
    proxy=PROXY,
    timeout=TIMEOUT)

# 2025年2月开通的 微信企业支付账号需要用公钥
# 平台证书模式向公钥模式切换期间也请使用此方式初始化。
# wxpay = WeChatPay(
#     wechatpay_type=WeChatPayType.NATIVE,
#     mchid=MCHID,
#     private_key=PRIVATE_KEY,
#     cert_serial_no=CERT_SERIAL_NO,
#     apiv3_key=APIV3_KEY,
#     appid=APPID,
#     notify_url=NOTIFY_URL,
#     logger=LOGGER,
#     partner_mode=PARTNER_MODE,
#     proxy=PROXY,
#     timeout=TIMEOUT,
#     public_key=PUBLIC_KEY,
#     public_key_id=PUBLIC_KEY_ID)

app = Flask(__name__)


@app.route('/pay')
def pay():
    # 以native下单为例，下单成功后即可获取到'code_url'，将'code_url'转换为二维码，并用微信扫码即可进行支付测试。
    out_trade_no = ''.join(sample(ascii_letters + digits, 8))
    description = 'demo-description'
    amount = 100
    code, message = wxpay.pay(
        description=description,
        out_trade_no=out_trade_no,
        amount={'total': amount},
        pay_type=WeChatPayType.NATIVE
    )
    return jsonify({'code': code, 'message': message})


@app.route('/transfer')
def transfer():
    # 以native下单为例，下单成功后即可获取到'code_url'，将'code_url'转换为二维码，并用微信扫码即可进行支付测试。
    out_bill_no = ''.join(sample(ascii_letters + digits, 8))
    transfer_scene_id='1005'
    openid='真实个人微信ID'
    
    user_name = '真实姓名'
    transfer_amount = 30
    transfer_remark='个体fun '
    user_recv_perception='劳务报酬'
    transfer_scene_report_infos =  [
      {
        "info_type" : "岗位类型",
        "info_content" : "专家顾问"
      },
      {
        "info_type" : "报酬说明",
        "info_content" : "带货提成"
      },
    ]
    print('get request')
    try:
        code, message = wxpay.mch_transfer_bills(out_bill_no=out_bill_no,transfer_scene_id=transfer_scene_id, \
            openid=openid,transfer_amount=transfer_amount,transfer_remark=transfer_remark,user_name=user_name,  \
         user_recv_perception=user_recv_perception, transfer_scene_report_infos=transfer_scene_report_infos   )
        print('get code',code, message)
    except Exception as e:
    # 捕获其他所有类型的异常
        print("发生了其他错误：", e)

    return jsonify({'code': code, 'message': message})
  @app.route('/notify', methods=['POST'])
def notify():
    result = wxpay.callback(request.headers, request.data)
    if result and result.get('event_type') == 'TRANSACTION.SUCCESS':
        resp = result.get('resource')
        appid = resp.get('appid')
        mchid = resp.get('mchid')
        out_trade_no = resp.get('out_trade_no')
        transaction_id = resp.get('transaction_id')
        trade_type = resp.get('trade_type')
        trade_state = resp.get('trade_state')
        trade_state_desc = resp.get('trade_state_desc')
        bank_type = resp.get('bank_type')
        attach = resp.get('attach')
        success_time = resp.get('success_time')
        payer = resp.get('payer')
        amount = resp.get('amount').get('total')
        # TODO: 根据返回参数进行必要的业务处理，处理完后返回200或204
        return jsonify({'code': 'SUCCESS', 'message': '成功'})
    else:
        return jsonify({'code': 'FAILED', 'message': '失败'}), 500


if __name__ == '__main__':
    app.run()
