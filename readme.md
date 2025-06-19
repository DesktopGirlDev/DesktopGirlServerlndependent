### 这是DesktopGirlServer的独立直接ai后端服务器
本服务器使用独立的python环境进行构建，最后使用pyinstaller打包成exe文件。
### 服务器功能
- 读取服务器配置文件./serverConfig.yaml（只读）
- 通过文件./Britney-v1/contact/ 内的文件实现与客户端沟通
- 编译后的文件应该放在根目录(./Britney-v1)下
- 编译时应选择与客户端相同的图标，应该不存在ui界面以及控制台输出，唯一的图标是任务栏右下角的小图标
