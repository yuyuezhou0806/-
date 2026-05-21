# 车辆档案管理系统

基于 FastAPI + Vue3 + Element Plus 的车辆档案管理系统，支持车牌颜色自动识别、Excel导入导出、保险提醒、用车申请审批等功能。

## 功能特性

- **车辆档案管理**: 增删改查车辆基本信息、证件信息、保险信息
- **车牌颜色识别**: 自动识别蓝牌、黄牌、绿牌、白牌等车牌颜色
- **Excel导入导出**: 支持批量导入车辆数据，导出Excel报表
- **保险到期提醒**: 自动检测30天内即将到期的保险
- **维修记录管理**: 记录车辆维修保养历史
- **用车申请审批**: 完整的用车申请、审批、归还流程
- **数据备份**: 一键备份数据库到本地文件

## 系统要求

- Python 3.8+
- 支持 Windows / Linux / macOS

## 安装部署

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务

**Windows:**
```bash
start.bat
```

**Linux/macOS:**
```bash
./start.sh
```

或手动启动:
```bash
python main.py
```

### 3. 访问系统

打开浏览器访问: http://localhost:8000/index.html

## 项目结构

```
vehicle_api/
├── main.py              # 后端主程序 (FastAPI)
├── index.html           # 前端页面 (Vue3)
├── test.html            # 测试页面
├── start.bat            # Windows启动脚本
├── start.sh             # Linux/macOS启动脚本
├── requirements.txt     # Python依赖列表
├── README.md            # 本说明文档
├── vehicle_management.db # SQLite数据库文件 (自动生成)
└── static/              # 静态资源文件
    ├── js/
    │   ├── vue.global.js        # Vue3
    │   ├── element-plus.js      # Element Plus
    │   ├── element-plus-icons.js # Element Plus图标
    │   └── axios.min.js         # Axios HTTP库
    └── css/
        └── element-plus.css     # Element Plus样式
```

## 使用说明

### 添加车辆
1. 点击"新增"按钮
2. 填写车辆信息（车牌号、品牌、型号等）
3. 选择车辆状态（闲置/使用中/维修中/已报废）
4. 保存即可

### 导入Excel
1. 点击"导入"下拉菜单
2. 选择"下载模板"获取导入模板
3. 按模板格式填写数据
4. 选择"导入Excel"上传文件

### 用车申请
1. 点击"用车申请"按钮
2. 切换到"申请用车"标签
3. 选择闲置车辆，填写申请信息
4. 提交申请等待审批

### 数据备份
1. 点击"备份"按钮
2. 系统会自动备份数据库
3. 备份文件保存在项目目录下

## 数据库说明

- **数据库类型**: SQLite
- **数据库文件**: `vehicle_management.db`
- **自动创建**: 首次启动时自动创建表结构

## 注意事项

1. **端口占用**: 默认使用 8000 端口，如被占用请修改 main.py 中的端口
2. **数据安全**: 建议定期使用"备份"功能备份数据
3. **浏览器兼容性**: 推荐使用 Chrome、Edge、Firefox 等现代浏览器

## 技术支持

如有问题，请检查:
1. Python版本是否 >= 3.8
2. 所有依赖是否已正确安装
3. 8000端口是否被其他程序占用
