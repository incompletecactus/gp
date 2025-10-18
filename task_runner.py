import time
import json
import requests
import hashlib

# -------------------------- 配置参数 --------------------------
# 用获取工具获取tokens，多账号用&分隔（例：token1&token2）
tokens = "7a639f7d6e528d41b821296fbeb252b1"
tokens = tokens.split("&") if tokens else []
# User-Agent配置（无需修改）
ua = "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Mobile Safari/537.36"
# 无需手动完成的任务列表（无需修改）
NOT_FINISH_TASKS = [
    "7328b1db-d001-4e6a-a9e6-6ae8d281ddbf",
    "e8f837b8-4317-4bf5-89ca-99f809bf9041",
    "65a4e35d-c8ae-4732-adb7-30f8788f2ea7",
    "73f9f146-4b9a-4d14-9d81-3a83f1204b74",
    "12e8c1e4-65d9-45f2-8cc1-16763e710036",
    "02388d14-3ab5-43fc-b709-108b371fb6d8"
]
# ----------------------------------------------------------------


def sha256_encrypt(data):
    """SHA256加密工具函数"""
    sha256 = hashlib.sha256()
    sha256.update(data.encode("utf-8"))
    return sha256.hexdigest()


def signzfb(t, url, token):
    """支付宝任务签名生成"""
    sign_str = f"appSecret=Ew+ZSuppXZoA9YzBHgHmRvzt0Bw1CpwlQQtSl49QNhY=&channel=alipay&timestamp={t}&token={token}&version=1.60.3&{url[25:]}"
    return sha256_encrypt(sign_str)


def sign(t, url, token):
    """常规任务签名生成"""
    sign_str = f"appSecret=nFU9pbG8YQoAe1kFh+E7eyrdlSLglwEJeA0wwHB1j5o=&channel=android_app&timestamp={t}&token={token}&version=1.60.3&{url[25:]}"
    return sha256_encrypt(sign_str)


def httprequests(url, token, data, mean):
    """HTTP请求工具函数（含超时重试与登录校验）"""
    t = str(int(time.time() * 1000))
    signs = sign(t, url, token)
    headers = {
        "Authorization": token,
        "Version": "1.60.3",
        "channel": "android_app",
        "phoneBrand": "Redmi",
        "timestamp": t,
        "sign": signs,
        "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        "Host": "userapi.qiekj.com",
        "Connection": "Keep-Alive",
        "Accept-Encoding": "gzip",
        "User-Agent": ua
    }

    try:
        if mean == "get":
            res = requests.get(url=url, headers=headers, timeout=15)
        else:  # post请求
            res = requests.post(url=url, headers=headers, data=data, timeout=15)

        if res.status_code == 200:
            res_json = json.loads(res.text)
            # 未登录校验
            if res_json.get("msg") == "未登录":
                print(f"❌ 账号token失效：{res_json['msg']}，退出脚本")
                exit()
            return res_json
        else:
            print(f"❌ 请求状态码异常：{res.status_code}，响应内容：{res.text[:100]}")
            return None

    except requests.exceptions.Timeout:
        print(f"⏱️ 请求超时（{url}），即将重试")
        time.sleep(3)
        return httprequests(url, token, data, mean)  # 超时自动重试
    except Exception as e:
        print(f"❌ 请求异常：{str(e)}")
        return None


def get_username(token):
    """获取账号昵称（美化日志用）"""
    url = "https://userapi.qiekj.com/user/info"
    data = {"token": token}
    res_json = httprequests(url=url, data=data, token=token, mean="post")
    
    if not res_json:
        return "未知账号"
    if res_json.get("code") == 0:
        return res_json["data"].get("userName", "未设置昵称")
    else:
        return "获取昵称失败"


def get_current_integral(token):
    """获取当前积分（用于计算今日新增）"""
    url = "https://userapi.qiekj.com/user/balance"
    data = {"token": token}
    res_json = httprequests(url=url, data=data, token=token, mean="post")
    
    if res_json and res_json.get("code") == 0:
        return res_json["data"]["integral"]
    else:
        print(f"❌ 获取积分失败，响应：{res_json}")
        return 0


def sign_in(token):
    """账号签到任务"""
    print("\n📅 开始执行【签到任务】")
    url = "https://userapi.qiekj.com/signin/doUserSignIn"
    data = {"activityId": "600001", "token": token}
    res_json = httprequests(url=url, token=token, data=data, mean="post")
    
    if not res_json:
        print("❌ 签到请求失败")
        return
    if res_json["code"] == 0:
        print(f"✅ 签到成功！当前总积分：{res_json['data']['totalIntegral']}")
    elif res_json["code"] == 33001:
        print(f"ℹ️ 今日已签到，无需重复操作")
    else:
        print(f"❌ 签到失败：{res_json.get('msg', '未知错误')}")


def home_browse(token):
    """首页浏览任务（上滑商品）"""
    print("\n📱 开始执行【首页浏览任务】")
    url = "https://userapi.qiekj.com/task/queryByType"
    data = {"taskCode": "8b475b42-df8b-4039-b4c1-f9a0174a611a", "token": token}
    res_json = httprequests(url=url, token=token, data=data, mean="post")
    
    if not res_json:
        print("❌ 首页浏览请求失败")
        return
    if res_json["code"] == 0 and res_json["data"] == True:
        print("✅ 首页浏览成功，获得1积分")
    else:
        print(f"❌ 首页浏览失败：{res_json.get('msg', '未知错误')}")


def shielding_query(token):
    """屏蔽资源查询（原solt函数，优化日志）"""
    print("\n🛡️ 执行【屏蔽资源查询】")
    url = "https://userapi.qiekj.com/shielding/query"
    data = {"shieldingResourceType": "1", "token": token}
    res_json = httprequests(url=url, data=data, token=token, mean="post")
    
    if res_json:
        print(f"ℹ️ 屏蔽查询结果：{res_json}")
    else:
        print("❌ 屏蔽资源查询失败")


def execute_task(token, task_code, task_title, task_limit):
    """执行单个常规任务（含失败交互逻辑）"""
    print(f"\n🔄 执行【{task_title}】（共{task_limit}次）")
    
    for num in range(1, task_limit + 1):
        print(f"\n第{num}/{task_limit}次尝试")
        url = "https://userapi.qiekj.com/task/completed"
        data = {"taskCode": task_code, "token": token}
        res_json = httprequests(url=url, token=token, data=data, mean="post")
        
        # 1. 请求失败（无响应）
        if not res_json:
            input("⚠️ 请点击看看广告任务过滑块验证，完成后按回车键重新运行...")
            continue
        
        # 2. 响应正常但数据为false（需手动广告）
        if res_json.get("code") == 0 and res_json.get("data") is False:
            input("⚠️ 请在APP手动做一个广告任务，完成后按回车键继续运行...")
            continue
        
        # 3. 响应正常且成功
        if res_json.get("code") == 0 and res_json.get("data") is True:
            print(f"✅ 第{num}次执行成功")
            time.sleep(10)  # 成功后等待10秒
        # 4. 其他错误（含获取异常）
        else:
            msg = res_json.get("msg", "未知错误")
            if "获取异常" in msg:
                input(f"⚠️ {msg}，请点击看看广告任务过滑块验证，完成后按回车键重新运行...")
            else:
                print(f"❌ 第{num}次执行失败：{msg}")
                time.sleep(10)  # 失败也等待10秒，避免请求过频


def app_video_task(token):
    """APP视频任务（20次上限）"""
    print("\n🎬 开始执行【APP视频任务】（最多20次）")
    
    for num in range(1, 21):
        url = "https://userapi.qiekj.com/task/completed"
        data = {"taskCode": 2, "token": token}
        res_json = httprequests(url=url, token=token, data=data, mean="post")
        
        if not res_json:
            print(f"❌ 第{num}次APP视频请求失败，停止任务")
            break
        if res_json["code"] == 0 and res_json["data"] is True:
            print(f"✅ 第{num}次APP视频任务完成")
            time.sleep(15)
        else:
            print(f"❌ 第{num}次APP视频任务失败：{res_json.get('msg', '未知错误')}，停止任务")
            break


def alipay_video_task(token):
    """支付宝视频任务（50次上限）"""
    print("\n alipay 开始执行【支付宝视频任务】（最多50次）")
    
    for num in range(1, 51):
        url = "https://userapi.qiekj.com/task/completed"
        t = str(int(time.time() * 1000))
        signs = signzfb(t, url, token)
        headers = {
            'Authorization': token,
            'Version': '1.60.3',
            'channel': 'alipay',
            'phoneBrand': 'Redmi',
            'timestamp': t,
            'sign': signs,
            'Content-Type': 'application/x-www-form-urlencoded;charset=UTF-8',
            'Host': 'userapi.qiekj.com',
            'Accept-Encoding': 'gzip',
            'User-Agent': ua
        }
        data = {"taskCode": 9, "token": token}
        
        try:
            res = requests.post(url=url, headers=headers, data=data, timeout=15)
            if res.status_code == 200:
                res_json = json.loads(res.text)
                if res_json["code"] == 0 and res_json["data"] is True:
                    print(f"✅ 第{num}次支付宝视频任务完成")
                else:
                    print(f"❌ 第{num}次支付宝视频任务失败：{res_json.get('msg', '未知错误')}")
                    break
            else:
                print(f"❌ 第{num}次支付宝视频请求异常：状态码{res.status_code}")
                break
        except Exception as e:
            print(f"❌ 第{num}次支付宝视频请求失败：{str(e)}")
            break
        
        time.sleep(15)  # 每次完成后等待15秒


# -------------------------- 主程序入口 --------------------------
if __name__ == "__main__":
    print("=" * 60)
    print("🎉 任务自动化脚本启动成功！")
    print(f"📅 执行时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    print(f"🔢 待处理账号数量：{len(tokens)}")
    print("=" * 60)

    if not tokens:
        print("❌ 未配置token，请先在脚本顶部填写tokens！")
        exit()

    # 循环处理每个账号
    for idx, token in enumerate(tokens, 1):
        print(f"\n\n" + "=" * 60)
        print(f"📌 开始处理第{idx}/{len(tokens)}个账号")
        username = get_username(token)
        print(f"👤 账号昵称：{username}")
        print("=" * 60)

        # 1. 初始化：获取初始积分
        init_integral = get_current_integral(token)
        print(f"\n💰 初始积分：{init_integral}")
        time.sleep(1)

        # 2. 执行基础任务
        sign_in(token)
        time.sleep(1)
        shielding_query(token)
        time.sleep(1)
        print("\n⌛ 3秒后开始执行其他任务...")
        time.sleep(3)
        home_browse(token)
        time.sleep(1)

        # 3. 执行任务列表（常规任务）
        print("\n" + "-" * 40)
        print("📋 开始处理【常规任务列表】")
        print("-" * 40)
        url = "https://userapi.qiekj.com/task/list"
        data = {"token": token}
        task_list_res = httprequests(url=url, token=token, data=data, mean="post")

        if not task_list_res or task_list_res.get("code") != 0:
            print(f"❌ 获取任务列表失败：{task_list_res}")
        else:
            tasks = task_list_res["data"]["items"]
            print(f"ℹ️ 共获取到{len(tasks)}个任务，过滤无需手动的任务后开始执行...")
            
            for task in tasks:
                task_code = task["taskCode"]
                task_title = task["title"]
                task_limit = task["dailyTaskLimit"]
                is_completed = task["completedStatus"] == 1

                # 跳过已完成/无需手动的任务
                if is_completed:
                    print(f"\nℹ️ 【{task_title}】已完成，跳过")
                    continue
                if task_code in NOT_FINISH_TASKS:
                    print(f"\nℹ️ 【{task_title}】无需手动执行，跳过")
                    continue

                # 执行未完成且需手动的任务
                execute_task(token, task_code, task_title, task_limit)

        # 4. 执行APP视频任务
        app_video_task(token)

        # 5. 执行支付宝视频任务
        alipay_video_task(token)

        # 6. 计算今日新增积分并总结
        final_integral = get_current_integral(token)
        today_add = final_integral - init_integral
        print("\n" + "=" * 60)
        print(f"📊 第{idx}个账号任务总结")
        print(f"👤 账号昵称：{username}")
        print(f"💰 初始积分：{init_integral}")
        print(f"💰 最终积分：{final_integral}")
        print(f"🎁 今日新增：{today_add}")
        print("✅ 所有任务执行完毕，3秒后处理下一个账号...")
        print("=" * 60)
        time.sleep(3)

    # 所有账号处理完成
    print("\n\n🎉 所有账号任务全部执行完毕！")
    print(f"📅 结束时间：{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}")
    print("=" * 60)