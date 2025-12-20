# WeChat Linux 版本监控

这个项目自动监控微信 Linux 版的官方页面，检测新版本发布，并保存版本信息。

## 功能

- 每天自动检查 https://linux.weixin.qq.com 的版本更新
- 提取版本号（如 4.1.0）
- 下载所有架构的安装包并计算哈希值
- 自动创建 GitHub Release
- 保存历史版本数据

## 文件命名规范

检测到新版本时，文件会按照以下规范重命名：
wechat_linux_架构_版本号_包类型.扩展名

示例：
- `wechat_linux_x86_4.1.0.deb`
- `wechat_linux_arm64_4.1.0.AppImage`
- `wechat_linux_loongarch_4.1.0.deb`

## 数据格式

版本数据保存在 `data/versions.json` 中，包含：
- 版本号
- 检测时间
- 各架构文件的哈希值和元数据

## 使用方法

1. Fork 这个仓库
2. 确保 Actions 已启用
3. 每天会自动运行，检测新版本
4. 新版本会自动创建 Release

## 手动触发


在 GitHub 仓库页面，点击 Actions → "Check WeChat Linux Version" → Run workflow
