# Cookie 获取教程

当 agent-reach/OpenCLI、bb-browser 或 agent-browser 无法复用用户登录态时，引导用户手动获取小红书 cookie。

## 引导话术

```text
别担心，很简单！跟着做就行：

第一步：打开浏览器，访问 www.xiaohongshu.com，确保你已经登录了

第二步：打开开发者工具
  - 如果你用的是 Chrome 或 Edge：按键盘上的 F12
  - 如果你用的是 Safari：按 Option + Cmd + I
    （如果按了没反应，先去 Safari → 设置 → 高级 → 勾选"显示开发菜单"）
  - 如果你用的是 Firefox：按 F12

第三步：在弹出的面板里，点击顶部的「Application」（应用）标签
  → 左侧找到「Cookies」展开
  → 点击 xiaohongshu.com

第四步：在右侧表格里找到名为 web_session 的那一行，
  双击它的 Value 列，全选复制

第五步：把复制的内容发给我就行了！

找不到也没关系，你可以选择跳过，我用基础模式帮你分析。
```

## Cookie 存储规则

- 保存位置：`scripts/.env`（格式：`XHS_COOKIE=web_session=xxx`）
- `.env` 必须在 `.gitignore` 中
- Memory 中只记录配置状态（`reference_xhs_cookie.md`），写"cookie 已配置于 YYYY-MM-DD"，**不存储 cookie 值本身**
- 绝不在对话中回显用户发送的 cookie 值
