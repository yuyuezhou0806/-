import requests

# 百度地图 API 的驾车路线查询 URL
url = "http://api.map.baidu.com/direction/v2/driving"

# 构建请求参数
params = {
    "origin": "上海市杨浦区军工路2390号",  # 替换为实际的起点坐标，格式如 "纬度,经度"
    "destination": "上海市杨浦区邯郸路500弄",  # 替换为实际的终点坐标，格式如 "纬度,经度"
    "origin_region": "上海市杨浦区军工路2390号",  # 替换为实际的起点所在地区名称
    "destination_region": "上海市杨浦区邯郸路500弄",  # 替换为实际的终点所在地区名称
    "ak": 'YXMO65MhinwIUy3DTf76PtCDzleaGPB2'  # 替换为你自己的百度地图 API Key
}

# 发起请求
response = requests.get(url, params=params)

# 处理响应
if response.status_code == 200:
    result = response.json()
    if result.get("status") == 0:
        print("驾车路线查询成功")
        print(result)
    else:
        print(f"查询失败，错误码: {result.get('status')}，错误信息: {result.get('message')}")
else:
    print(f"请求失败，状态码: {response.status_code}")

