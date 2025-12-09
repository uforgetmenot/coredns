# 浏览器缓存问题修复说明

## 问题描述

登录 dashboard 页面后出现以下错误:
```
加载备份失败
加载记录失败
Corefile 预览失败

TypeError: Cannot set properties of null (setting 'innerHTML')
TypeError: Cannot set properties of null (setting 'textContent')
```

## 根本原因

浏览器缓存了旧版本的 `dashboard.js` 文件。在页面重构过程中,我们将部分功能从 dashboard 迁移到了独立页面:
- DNS 记录管理 → `/records` 页面
- Corefile 管理 → `/corefile` 页面

旧版本的 `dashboard.js` 仍然包含这些功能的代码,但 dashboard 页面的 HTML 中已经没有对应的 DOM 元素,导致 JavaScript 尝试设置不存在元素的属性时出错。

## 解决方案

为所有 JavaScript 文件添加版本参数来强制浏览器刷新缓存:

### 修改的文件

1. **dashboard.html**
   ```html
   <script src="/static/js/dashboard.js?v=2.0"></script>
   ```

2. **records.html**
   ```html
   <script src="/static/js/records.js?v=1.0"></script>
   ```

3. **corefile.html**
   ```html
   <script src="/static/js/corefile.js?v=1.0"></script>
   ```

## 如何验证修复

1. **清除浏览器缓存**
   - Chrome: Ctrl+Shift+Delete → 清除缓存和 Cookie
   - Firefox: Ctrl+Shift+Delete → 清除缓存
   - 或者使用隐私/无痕模式测试

2. **硬刷新页面**
   - Windows: Ctrl+F5 或 Ctrl+Shift+R
   - Mac: Cmd+Shift+R

3. **检查开发者工具**
   - 打开 Chrome DevTools (F12)
   - 切换到 Network 标签
   - 刷新页面
   - 确认 dashboard.js 请求 URL 包含 `?v=2.0`

4. **验证功能**
   - Dashboard 页面应正常显示统计数据和 CoreDNS 状态
   - 不应出现任何 JavaScript 错误
   - `/records` 页面应正常显示 DNS 记录管理功能
   - `/corefile` 页面应正常显示 Corefile 管理和备份功能

## 技术细节

### 当前 dashboard.js 应该包含的功能

```javascript
// ✓ 保留的功能
- loadStats()           // 加载统计数据
- loadCoreDNSStatus()   // 加载 CoreDNS 状态
- reloadCoreDNS()       // 重载 CoreDNS

// ✗ 已移除的功能(迁移到其他页面)
- loadRecords()         // → records.js
- loadBackups()         // → corefile.js
- refreshCorefilePreview() // → corefile.js
- createBackup()        // → corefile.js
- handleBackupAction()  // → corefile.js
```

### 版本控制策略

以后更新 JavaScript 文件时,记得更新版本号:

```html
<!-- 小改动:增加小版本号 -->
<script src="/static/js/dashboard.js?v=2.1"></script>

<!-- 大改动:增加主版本号 -->
<script src="/static/js/dashboard.js?v=3.0"></script>
```

## 预防措施

### 开发环境

在开发时禁用缓存:
1. 打开 Chrome DevTools (F12)
2. 切换到 Network 标签
3. 勾选 "Disable cache" 选项

### 生产环境

考虑使用以下策略之一:

1. **文件名哈希** (推荐)
   ```html
   <script src="/static/js/dashboard.a1b2c3d4.js"></script>
   ```

2. **自动版本号**
   ```python
   # 使用文件修改时间或 Git commit hash
   import os
   from datetime import datetime

   js_version = os.path.getmtime('app/static/js/dashboard.js')
   # 或
   js_version = git_commit_hash
   ```

3. **Cache-Control 头**
   ```python
   # 在 FastAPI 中设置
   @app.get("/static/js/{file_name}")
   async def serve_js(file_name: str):
       return FileResponse(
           f"static/js/{file_name}",
           headers={"Cache-Control": "no-cache"}
       )
   ```

## 相关文件

- `app/templates/dashboard.html` - Dashboard 页面模板
- `app/templates/records.html` - DNS 记录页面模板
- `app/templates/corefile.html` - Corefile 页面模板
- `app/static/js/dashboard.js` - Dashboard 页面脚本
- `app/static/js/records.js` - DNS 记录页面脚本
- `app/static/js/corefile.js` - Corefile 页面脚本

## 总结

问题已通过添加版本参数修复。用户需要:
1. 清除浏览器缓存或硬刷新页面
2. 确认 JavaScript 文件请求包含版本参数
3. 验证所有页面功能正常工作

如果问题仍然存在,请检查:
- 浏览器控制台是否有其他错误
- 网络请求是否成功加载新版本文件
- 是否有代理或 CDN 缓存问题
