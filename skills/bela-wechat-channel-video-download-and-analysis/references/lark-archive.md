# 归档到用户指定的飞书位置

用户选择飞书或两处保存时，运行 `python3 "$SKILL_DIR/scripts/user_config.py" destination`，按需传入本次方式（`--mode feishu` 或 `--mode both`）和 `--feishu-parent-url`。本次链接优先，未指定时读取已保存的 `delivery.feishu_parent_url`。只有 `status=destination_ready` 且返回的 `feishu_parent_url` 非空时才进入飞书分支。返回 `feishu_parent_url_required` 时提示「请粘贴要保存到的飞书文件夹或知识库节点链接。」返回 `invalid_feishu_parent_url` 时请用户更正链接。等待期间暂缓飞书归档；选择两处时可继续本地交付。

用户提供链接后先在本地校验格式并去掉查询串和片段。首次指定的常用目标或「以后用这里」记入个人配置；独立文档先按下文确认其父位置；「仅这次」只用于当前任务。清空父链接后，下次选择飞书时重新询问。账号或租户变化时先与用户核对是否沿用这个链接。分享口令、授权码、凭据和本次创建的作品目录均不作为常用目标。

有具体目标链接，且本次需要上传的成品就绪后，才准备 CLI、核对远端位置和归档。下载失败或等待用户补交素材时只报告素材状态。每条作品直接归入目标下的 `{MMDD}-{博主}｜{标题}`，文件夹和在线文档分别使用命名脚本的 `cloud_directory_title`、`cloud_document_title`。上传附件沿用本地文件名。完整交付包括 MP4、口播稿 Markdown 和带图的在线拆解文档，取得并核验原封面时再附上封面。

## 准备当前用户的 CLI

1. 运行 `lark-cli --version`。找不到命令时，在已选择飞书的前提下用 npm 安装官方包 `npm install -g @larksuite/cli`，再验证命令可用。使用 `lark-cli skills read lark-shared`、`lark-cli skills read lark-drive` 和 `lark-cli skills read lark-doc` 读取当前版本附带的说明，按需要读取其中列出的参考。无需把这些说明独立安装到用户的全局 Skills。
2. 沿用本机已配置的 CLI、应用和当前用户凭据。先以 `--as user` 做归档本就需要的只读操作，按下文读取用户指定的 Wiki 节点或检查指定文件夹。读取成功就继续。首次确实缺少应用配置时才按 CLI 提示绑定应用。
3. 读取失败时保留 CLI 的具体错误。对认证错误，运行 `lark-cli auth status --json --verify` 查看 `identities.user`；顶层默认身份可能是 bot。若已有此次尚有效的设备授权，用户完成浏览器确认后，用原 `device_code` 完成 `lark-cli auth login --device-code <本次设备码>`，再重试原操作。当前用户已有效时直接重试原读取即可。
4. 只有 CLI 确认用户尚未登录或登录已失效且无法续期，才按本次交付所需范围发起一次设备登录。若已登录且业务命令明确报 `missing_scopes`，只申请返回的所缺权限（`lark-cli auth login --scope '<所缺权限>' --no-wait --json`）。链接和二维码按 `lark-shared` 展示。同一有效授权等待期间沿用原流程。网络、目录无访问权、容量和目标位置错误分别处理。设备码与登录凭据仅供当前认证使用。
5. 下文的云端读写均显式使用 `--as user`。以退出码与 JSON 的 `ok` 核对结果；部分失败时保留本地文件和进度。

## 在指定位置创建作品目录

按链接类型核对目标。创建、上传和回读均显式传入已经核实的非空父 token。链接无效、无权限或目标无法承载子项时，说明具体问题，请用户提供可写的目标链接或开通该位置的权限，保留本地成品与进度。不要调用省略父位置的创建命令，CLI 会将内容写到账号的默认位置。

### 云盘文件夹链接

用 `lark-cli drive +inspect --url '<用户给的文件夹 URL>' --as user` 核实资源为文件夹，取其标题与 token。只列该文件夹的直属子项。逐页检查 `data.has_more`，将 `data.next_page_token` 作为下一页的 `page_token`。缺页或游标无效时先解决读取问题，再判断是否新建。

```bash
lark-cli drive files list --params '{"folder_token":"<指定文件夹 token>","page_size":200}' --as user --format json
lark-cli drive +create-folder --folder-token '<指定文件夹 token>' --name '<本条目录名>' --as user
```

仅在已核实没有本条作品目录时执行创建命令。根据已有收据和源文件辨认同名项。记下作品目录的 token 与返回的链接，后续所有文件归入此目录。多条作品共用父级时，串行核对和创建目录。

### 知识库节点链接

读取 `lark-cli skills read lark-wiki`。用 `lark-cli wiki +node-get --node-token '<用户给的 Wiki URL>' --as user` 取得 `space_id` 和 `node_token`。用 `lark-cli wiki +node-list --space-id '<空间 ID>' --parent-node-token '<指定节点 token>' --page-all --page-limit 0 --as user` 列全其直属子节点。确认需要新建时，执行 `lark-cli wiki +node-create --parent-node-token '<指定节点 token>' --title '<本条目录名>' --as user`。记录本条作品节点的 token。

在知识库上传文件时，下文 `drive +upload` 示例的 `--folder-token` 换成 `--wiki-token '<本条节点 token>'`。创建报告时 `docs +create --parent-token` 传本条节点 token。回读时用相同的 `wiki +node-list` 命令列全本条节点的子项，通过 `obj_type` 与 `obj_token` 核对。

### 文档链接

用 `drive +inspect --url '<文档 URL>' --as user` 核实文档类型与自身 token。普通文档 token 不能用作 Drive 文件夹 token。

- 文档属于知识库时，可用 `lark-cli wiki +node-get --node-token '<文档 URL>' --as user` 核实 `obj_token`、`node_token` 和 `space_id`。如果用户给这篇文档作为归档目标，按上一节在该节点下建作品目录。如果用户指定「和这篇文档同层」，用节点的 `parent_node_token` 核对父节点，并向用户确认目标名称和链接；用户已经明确给出该父节点链接时直接使用。
- 独立云文档自身不能承载作品文件夹。若已有具体候选文件夹，列其直属子项，用文档的类型和精确 token 核实归属，并向用户说明其父文件夹的名称、链接。用户明确确认「存到此文件夹」后，才把它用作归档位置；保存为常用位置时记规范的父链接。
- 普通文档的父位置无法核实，或用户只提供空间名称、标题或目录路径时，请用户粘贴可写文件夹或知识库节点的链接。等待期间保留成品；不通过全盘搜索同名项来确定目标。

## 写入视频、口播稿、封面与报告

在工作目录保留本次清单。键包含来源视频标识、当前登录身份及目标父目录。写前记下预期名称、本地文件哈希、目标及阶段。每次写成功立即记下返回的 token、URL 和服务端大小（如有）。一个来源和目标只由一个任务写入。重跑复用原归档日期与已验证的目录。用户可能隔天续跑。若找到同名目录，用清单、报告中的来源链接或已核验的源文件辨认。同名不同源或无法判定时，请用户选现有目录或为新任务另取名。

1. 用准备好的最终 MP4、校对口播稿和已验证的原封面文件逐项上传。保留本次确定的清晰度优先交付版本。有原封面才上传 `【视频号封面】博主｜标题.<实际扩展名>`。每个上传以 `drive +upload` 返回的 `file_token` 和云端链接登记。重试前查目录并核验已有项，遇到同名且不能确认内容时先比对哈希（必要时下载到工作区），保留已有资料。
2. 从本地拆解 Markdown 生成临时飞书导入稿。把成片链接改为刚核验的视频云端 URL，把本地 Markdown 的相对配图链接转换成 CLI 的 `![00:03 开场](<@./配图/开场 示例.jpg>)`。从归档目录运行，保证这些路径真实可读。保留面向本地阅读的原稿。导入时核对警告、返回的 `document_id` 和图片块，记入清单。

```bash
lark-cli drive +upload --file './<视频文件名>' --folder-token '<本条目录 token>' --as user
lark-cli drive +upload --file './<口播稿文件名>.md' --folder-token '<本条目录 token>' --as user
# 已验证原封面时执行
lark-cli drive +upload --file './<封面文件名>' --folder-token '<本条目录 token>' --as user
# 临时导入稿可通过 stdin 传入，配图路径相对当前工作目录解析
lark-cli docs +create --doc-format markdown --content - --parent-token '<本条目录 token>' --title '<【视频拆解】博主｜标题>' --as user < '<临时飞书导入稿路径>'
```

写入超时或连接中断时，先回查所属父目录。对可能已上传的文件核对来源、类型、大小和必要的内容哈希，对可能已创建的拆解文档核对来源链接、正文与图片。确认远端已成功就记录已有结果。若仍无法判断是否写入，请用户确认再重试，避免生成重复内容。

## 回读与交付

- 用 `lark-cli docs +fetch --doc '<document_id>' --doc-format xml --detail full --as user` 回读。核对报告标题、视频链接、时间轴至结尾、末节与末段，确认预期数量的图片块均有可用 token。
- 列本条目录所有直属子项，核对类型、名称、token。完整拆解应有 MP4 和原生口播稿 `.md` 两个 file，以及一个在线报告 docx。取到有效原封面时多一个 file，共四项。取不到原封面则列明原因。对额外条目只记录，无权替用户清理。若用户仅要求下载，依其范围核验实际文件。
- 返回真实目录链接和各交付物的链接。一项失败时单列成功项与待补项。图片直接嵌入报告，ASR、临时导入稿、全量网格和日志保留在本地工作区。
