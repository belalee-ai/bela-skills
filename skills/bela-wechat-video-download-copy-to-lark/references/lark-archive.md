# 飞书 Wiki 按名称归档：可移植操作参考

本参考依据当前已安装 `lark-cli` 的帮助与 lark-wiki/lark-drive/lark-doc/lark-shared 技能，并用 user 身份只读验证过名称解析及分页。示例中的 token/ID 全部为运行时变量，不携带原账户的域名、用户 ID、空间 ID 或节点 token。

## 0. 严格依赖前置门禁

完整技能的核心依赖为 6 个 Skill：`wechat-video-downloader`、`hypit`、`lark-shared`、`lark-wiki`、`lark-drive`、`lark-doc`。本参考的飞书段必须有后 4 个 Skill 与可执行 `lark-cli`。

在任何下载、分析或云端写入前，主技能应逐项检查所有必需 SKILL.md、所引用的必需 reference/脚本与 CLI，读取版本和所需子命令帮助，并按主技能执行最新版本核验及范围明确的技能升级；缺失或无法运行即停止，列明安装项，由使用者安装后重新运行完整前置检查。不得静默安装、切换浏览器/其他 API、用别的工具替代缺失依赖，也不能跳过缺失能力进入后续阶段。实际依赖还包含下载和 Hypit 分析选定路径所需的运行环境，主技能应单列验证。

`lark-markdown` **不属于依赖**：它只处理飞书 Drive 内的原生 `.md` 文件；其 SKILL.md 明确“不负责将 Markdown 导入为飞书在线文档”，且纯本地 Markdown 操作也不触发。本流程将准备好的报告 Markdown 保真导入 docx，使用 `lark-doc` 的 `docs +create --doc-format markdown`；口播稿 `.md` 只用 `drive +upload` 作为普通文件上传，不读写其内容，所以同样不需要 `lark-markdown`。读取 lark-doc 的 `lark-doc-create.md`、`lark-doc-md.md` 与 `lark-doc-fetch.md` 即可覆盖该导入/核验步骤；只有用到 XML 扩展时额外读取 XML 格式参考。

安装状态、认证、权限和服务余额必须分开报告：

- 缺 Skill/CLI/reference、可执行失败或所需命令不存在：依赖缺失/不兼容，停止让使用者安装或更新，之后复检。
- 未登录、token 过期、missing scopes、资源权限拒绝：账号/授权问题；安装并不能解决。停止依赖该账号的步骤，提供准确错误与所需修复，不切换 bot、不自行改权限、不自动重登或扩大授权。
- 积分不足、账户余额/存储配额不足：服务额度问题；准确转述原始错误，停止付费或写入步骤，不伪装为安装失败，也不改走其他服务消耗账户。
- 目标不存在/同名歧义：目标解析问题；保留已完成资料，等待明确目标，不能静默创建默认空间或传到根目录。

已完成的输出保留，复检后按任务清单续跑，避免重复创建或计费。

## 1. 身份、输出与路径约定

- 全程显式使用 `--as user`；不要无提示改为 bot，bot 可能只看到自己的资源并返回空成功。
- Shortcut 成功以 `ok == true`、进程退出码 0 为准，不能使用顶层 `code == 0`。错误一般在 stderr 的 `error`，保留具体错误供用户判断。
- 用户已要求创建归档目录、上传视频与口播稿、创建拆解文档，属于已授权范围。不要重复请求普通创建/上传许可；不要顺带改公开权限、成员、owner 或发送消息。
- 本地输入、输出和 `@file` 使用当前工作目录内相对路径。Python 调用 CLI 优先传 `subprocess.run([...])`，避免标题、路径和链接被 shell 展开。
- 前置检查只读验证登录/依赖；出现认证、scope 或资源权限错误时，按上述门禁停止并报告，参考 lark-shared 解释修复路径；不得输出凭据或自动修复账号权限。

## 2. 默认目标与名称解析

默认空间名称：`贝拉自媒体秘密基地`。默认目标节点标题：`视频拆解`。例如目标可以嵌套为 `视频号 / 视频拆解`；默认只配置叶子标题，完整遍历后确定唯一位置。用户配置完整路径时按路径逐层解析，不能固定 token。允许用户指定另一个空间、完整节点路径或 Wiki URL，明确指定优先于默认值。

### 2.1 空间分页查询

首批：

```bash
lark-cli wiki +space-list --as user --format json --page-size 50
```

续页仅在 `data.has_more == true` 时执行：

```bash
lark-cli wiki +space-list --as user --format json --page-size 50 --page-token '<上页 data.page_token>'
```

输出形态：

```json
{
  "ok": true,
  "identity": "user",
  "data": {
    "spaces": [
      {"space_id":"<运行时 ID>","name":"<空间名>","description":"...","space_type":"team","visibility":"public","open_sharing":"closed"}
    ],
    "has_more": false,
    "page_token": "<可能非空>"
  },
  "meta": {"count":1}
}
```

务必用 `has_more` 判断结束：实测末页可能仍返回非空 `page_token`。`--page-token` 强制单页；`--page-all` 默认最多 10 页，必须检查剩余的 `has_more`。可用 `--page-all --page-limit 0` 汇总所有页，但显式游标循环更便于控制和验证。

在所有页面中对空间名称做精确匹配。0 个匹配：报告未找到或当前用户不可见，不自动建同名空间、不模糊选取。1 个匹配：取其 `space_id`。多于 1 个：列出名称、描述、space_id 让用户选定。不能因首批只有一个匹配就假定全局唯一。

`+space-list` 不包含 `my_library` 个人知识库。只有用户明确指定个人文档库时，另走该别名的解析；不要把团队空间查找降级成个人库。

### 2.2 根节点、直接子节点与分页

列空间根节点（省略 `--parent-node-token`）：

```bash
lark-cli wiki +node-list --space-id '<已解析 space_id>' --as user --format json --page-size 50
```

列某节点的直接子节点：

```bash
lark-cli wiki +node-list --space-id '<space_id>' --parent-node-token '<wiki node_token>' --as user --format json --page-size 50
```

续页在相同命令上追加 `--page-token '<上页游标>'`；直到 `has_more == false`。输出：

```json
{
  "ok":true,
  "identity":"user",
  "data":{
    "nodes":[
      {"space_id":"<ID>","node_token":"<Wiki token>","obj_token":"<底层对象 token>","obj_type":"docx","parent_node_token":"<父 Wiki token 或空串>","node_type":"origin","title":"视频拆解","has_child":true}
    ],
    "has_more":false,
    "page_token":""
  },
  "meta":{"count":1}
}
```

`--space-id` 必须是数字空间 ID，不能传空间名称、Wiki URL 或 node_token。`--parent-node-token` 必须是 Wiki node_token，不要误用 docx obj_token。

### 2.3 完整路径优先；只有叶子名称时递归找全候选

有完整路径（例如 `视频号 / 视频拆解`）时：

1. 列全空间根节点，精确匹配第一段标题。
2. 在匹配节点下列全直接子节点，匹配下一段。
3. 每层必须得到唯一结果；遇到同名兄弟，不自行选第一条。最终保留空间 ID、目标 node_token、完整路径。

只有 `视频拆解` 叶子名称时：

1. 从所有根节点开始 BFS/DFS；对 `has_child == true` 的节点列全直接子节点。
2. 用 visited 集合防止重复遍历；对快捷方式谨慎，不沿同一 token 重复展开。
3. 收集全空间所有标题精确匹配的节点，附完整路径。只有遍历完目标空间且唯一命中时才可确定。
4. 0 个命中不自动创建；多个命中列出路径与 token 让用户选择。若触达执行预算或访问受限，标明扫描不完整，不把局部唯一当成全局唯一。

若用户提供 Wiki URL，则用：

```bash
lark-cli wiki +node-get --node-token '<用户给的完整 URL>' --as user --format json
```

直接读取 `data.space_id/node_token/obj_token/obj_type/title`；用户给的精确目标无需再按默认名称猜测。

遇到 `invalid_parameters`、`not_found`、`permission_denied` 不要按原参数重复请求或切换身份试错。只有 rate limit 按提示退避。不得在无法解析目标时静默上传到 Drive 根目录。

## 3. 新建本条视频的归档目录

先列全目标的直接子节点，检查拟用归档标题是否已存在。为避免重试重复创建，保存当前任务清单中的 node_token，继续任务时优先回查它。同名且无法判断是否同次任务时，让用户决定复用还是新建，不能把陌生同名目录当本次目录覆盖。

Wiki API 的普通目录可用一个 docx 类型 Wiki 节点承载，三个资料（视频、拆解 docx、口播稿 .md）作为其子节点；不向 `wiki +node-create` 传不支持的 `obj-type=folder`。

```bash
lark-cli wiki +node-create --parent-node-token '<目标 node_token>' --title '<directory_title，如 1031-博主｜标题>' --as user --format json
```

成功返回 `data.node_token`、`obj_token`、`obj_type=docx`、`title`、`resolved_space_id/space_id`，当前 CLI 还返回新目录的 `url`。保存这些运行时结果；创建成功后不得因客户端后续步骤失败而重复创建目录。

## 4. 上传视频与创建拆解文档

视频保留下载成片字节，不为了上传而转码。文件名用 `archive_names.py` 的 `video_filename`（`【视频】<博主>_<标题>.mp4`），仅清除路径非法字符或缩短超过文件系统限制的名称；正文保留完整标题。

```bash
lark-cli drive +upload --file './outputs/<视频文件>.mp4' --wiki-token '<新目录 node_token>' --name '<video_filename，如 【视频】博主_标题.mp4>' --as user --format json
```

上传输出 `data.file_name/file_token/size/url/version`。`url` 可能为 `/file/` URL。随后列目录子节点，通过 `obj_type=file && obj_token==file_token` 找对应 Wiki node_token，不猜测 token。

有 Markdown 和本地证据图时，直接创建成在线 docx：

```bash
lark-cli docs +create --doc-format markdown --content '@./outputs/<拆解文档>.md' --parent-token '<新目录 node_token>' --title '<document_title，如 【视频拆解】博主｜标题>' --as user
```

本地图片语法：

```markdown
![00:03｜开场对比](@./work/evidence/figure-hook.jpg)
![带空格路径](<@./work/evidence/figure detail.jpg>)
```

`@./` 必须相对执行 cwd，图片 alt 转为 caption。图片嵌入文档，不创建 Wiki 目录子文件。普通 `![](./...)` 与 `drive +import` 是否会处理相对图片未验证，不依赖它们完成本地图片导入。

`docs +create` 输出 `data.document.document_id/revision_id/url/new_blocks`，其中 `new_blocks` 包含图片的 block_id/block_token/block_type。必须检查 warnings/tips（若存在）判断有无内容降级。

若图必须后加，CLI 支持 `docs +media-insert --doc '<document_id>' --file './work/evidence/figure.jpg' --caption '<说明>' --width 1000 --as user`，只会追加到文末；通常一次创建时嵌图更可靠。`--doc` 此处传 document_id，不传 Wiki URL。

### 上传口播稿

口播稿以**原生 `.md` 文件**上传，和视频走同一条 `drive +upload` 路径，不转成 docx，也不需要 `lark-markdown`：

```bash
lark-cli drive +upload --file './outputs/<口播稿>.md' --wiki-token '<新目录 node_token>' --name '<transcript_filename，如 【口播稿】博主｜标题.md>' --as user --format json
```

同样从返回的 `file_token` 回查目录子节点得到它的 Wiki node_token。

## 5. 回读与数量验证

```bash
lark-cli docs +fetch --doc '<document_id>' --doc-format xml --detail full --as user
lark-cli wiki +node-list --space-id '<space_id>' --parent-node-token '<归档目录 node_token>' --as user --format json --page-size 50
```

全文在 `data.document.content`，验证准确标题、时间轴表格、预期图片数、末节及末段，勿仅凭创建成功判定内容完整。图片应为已上传 token 的 `<img>` 节点，不是遗留本地路径文本。目录分页列完后应恰有三个直属子项：两个 file（视频、口播稿 .md）和一个 docx（拆解），并分别核对底层 token 与文件名。若有额外项，先报告，不自动删除可能属于用户的资料。

将视频、文档、目录的 token、返回 URL、原链接、标题、大小、成功步骤、核验结果保存在当前任务 `work/` 清单，便于重入与幂等。

链接域名从 CLI 本次返回的 URL 提取，不写死 `feishu.cn` 租户前缀。目录已有返回 Wiki URL；视频或报告若只有 file/docx URL，可从该 URL 提取 origin，结合子节点回查得到的 node_token 构造 `${origin}/wiki/${node_token}`，不能使用旧任务 token 或个人域名。

