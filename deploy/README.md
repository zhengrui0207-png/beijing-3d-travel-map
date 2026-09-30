# 阿里云 Demo 部署

线上地址：https://airesumejob.xyz/beijing-map/

- 静态目录：`/var/www/beijing-3d-travel-map/current`，只同步 index.html 和 public/ 为可访问资源。
- 后端：`hosted_server.py` + `travel_api.py`，Python 3.11+，systemd `beijing-map.service`，只监听 127.0.0.1:5199。
- `/etc/beijing-map.env` 由服务器管理员维护，0600，包含 BAIDU_MAP_AK、ATLAS_PUBLIC_ORIGIN、ATLAS_PORT。不要提交该文件。
- Nginx 将 `beijing-map-limits.conf` 放在 http 上下文，将 `beijing-map-location.conf` include 在 HTTPS server 中。
- API 按 IP 和站点限流，只允许 status/search/route；检查 Host、Origin 和页面令牌；不提供公网密钥编辑入口。
- 百度控制台应白名单实际服务器公网出口 IP；本机出口白名单不等于服务器白名单。

更新：先校验模型资源并运行测试，上传到独立部署目录；保留服务器环境文件，重启 beijing-map 服务，运行 nginx -t 后 reload，再验证页面、模型和真实路线。不要覆盖同服务器上的其他站点。此服务是公开 Demo，若大规模推广，应进一步增加配额预算、认证和监控。
