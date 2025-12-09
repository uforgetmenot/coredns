# 上级 DNS 配置 - 快速开始

## 通过 Web 界面配置（推荐）

1. 启动应用并登录
2. 访问 Dashboard: `http://localhost:8000/dashboard`
3. 找到"上级 DNS 配置"卡片
4. 填写配置：
   - **主 DNS 服务器**: 必填，例如 `1.1.1.1`
   - **备用 DNS 服务器**: 可选，例如 `1.0.0.1`
5. 点击"保存配置"
6. 重新生成 Corefile 并重载 CoreDNS

## 通过 API 配置

```bash
# 更新上级 DNS 配置
curl -X PUT http://localhost:8000/api/settings/upstream-dns \
  -H "Content-Type: application/json" \
  -d '{
    "primary_dns": "1.1.1.1",
    "secondary_dns": "1.0.0.1"
  }'

# 获取当前配置
curl http://localhost:8000/api/settings/upstream-dns
```

## 常用 DNS 服务器参考

### Google Public DNS
- 主: `8.8.8.8`
- 备: `8.8.4.4`

### Cloudflare DNS
- 主: `1.1.1.1`
- 备: `1.0.0.1`

### 阿里云 DNS
- 主: `223.5.5.5`
- 备: `223.6.6.6`

### 腾讯 DNS
- 主: `119.29.29.29`
- 备: `182.254.116.116`

### 114 DNS
- 主: `114.114.114.114`
- 备: `114.114.115.115`

## 验证配置

配置保存后，生成的 Corefile 将包含类似以下内容：

```
. {
    forward . 1.1.1.1 1.0.0.1
    log
    errors
    cache 30
}
```

## 故障排查

### 配置未生效
1. 确认配置已保存（查看提示消息）
2. 重新生成 Corefile（访问 `/corefile` 页面点击"生成 Corefile"）
3. 重载 CoreDNS（Dashboard 点击"重载 CoreDNS"）

### API 调用失败
- 检查请求 Content-Type 是否为 `application/json`
- 确认 primary_dns 字段不为空
- 查看服务器日志获取详细错误信息
