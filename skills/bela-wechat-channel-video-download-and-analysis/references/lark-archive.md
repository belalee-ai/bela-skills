# 保存到飞书「我的空间」

仅当用户选择飞书或两处（`feishu`、`both`），且本次要求上传的文件已在本地就绪时进入本分支。下载失败、等待用户播放或补交 MP4 时，返回当前素材状态即可。默认位置是当前飞书用户的 **我的空间 / 视频号爆款拆解 / {MMDD}-{博主}｜{标题}**。每条视频交付 MP4、口播稿 Markdown、带图的飞书在线拆解文档。取得并验证原封面时，多交付一张「视频号封面」。飞书目录和在线文档分别使用命名脚本的 `cloud_directory_title`、`cloud_document_title`，保留原标题中的标点。上传附件沿用本地文件名。

## 本机交付偏好

读取当前用户主目录下的 JSON 文件 `~/.bela-skills-config/bela-wechat-channel-video-download-and-analysis.config`。以当次明确指定的方式和位置为先，再取已记住的 `delivery.mode`、`delivery.local_root` 和 `delivery.feishu_parent_url`。首次 `mode` 为空时先问保存本地、飞书还是两处。选本地且根目录为空时用 `~/视频号爆款拆解/`。选飞书且父链接为空时用当前登录账号的「我的空间 / 视频号爆款拆解」。

- 初次确定的常用位置、后续「以后用这里」的选择，按主流程写入用户配置，下次直接复用。用户说「仅这次」时只覆盖本次任务。若要求清除某项偏好，单独重置该字段：保存方式或飞书父链接恢复为 `null`，本地根目录恢复为 `~/视频号爆款拆解`。清除飞书父链接后，下一次飞书交付使用个人云盘默认目录。清除方式后，下一次未指定时重新询问。
- 输入自定义位置时先在本地保存干净的资源链接。实际上传前，通过本机 CLI 核对其类型和当前用户的访问权限；若需解析普通文档所属的父位置，在该阶段按下文处理。分享签名、访问口令、临时链接、授权码、凭据和本次创建的作品目录链接均不写入这项偏好。选择个人云盘默认位置时保存 `null`，让它自然跟随当次登录账号。
- 换号或切换租户时，重新核对身份和当前目标。对于已保存的自定义父链接，即使新账号也能访问，仍需确认是沿用该位置、改用新位置还是新账号的个人云盘。明确仅更换本次目标时保留旧偏好。先前账户的任务收据不用于新账号的续传。

## 准备当前用户的 CLI

1. 运行 `lark-cli --version`。找不到命令时，在已选择飞书的前提下用 npm 安装官方包 `npm install -g @larksuite/cli`，再验证命令可用。使用 `lark-cli skills read lark-shared`、`lark-cli skills read lark-drive` 和 `lark-cli skills read lark-doc` 读取当前版本附带的说明，按需要读取其中列出的参考。无需把这些说明独立安装到用户的全局 Skills。
2. 沿用本机已配置的 CLI、应用和当前用户凭据。先以 `--as user` 做归档本就需要的只读操作，例如按下文读取父 Wiki 节点、检查指定文件夹或列出个人云盘根目录；读取成功就继续。首次确实缺少应用配置时才按 CLI 提示绑定应用。
3. 读取失败时保留 CLI 的具体错误。对认证错误，运行 `lark-cli auth status --json --verify` 查看 `identities.user`；顶层默认身份可能是 bot。若已有此次尚有效的设备授权，用户完成浏览器确认后，用原 `device_code` 完成 `lark-cli auth login --device-code <本次设备码>`，再重试原操作。当前用户已有效时直接重试原读取即可。
4. 只有 CLI 确认用户尚未登录或登录已失效且无法续期，才按本次交付所需范围发起一次设备登录。若已登录且业务命令明确报 `missing_scopes`，只申请返回的所缺权限（`lark-cli auth login --scope '<所缺权限>' --no-wait --json`）。链接和二维码按 `lark-shared` 展示。同一有效授权等待期间沿用原流程。网络、目录无访问权、容量和目标位置错误分别处理。设备码与登录凭据仅供当前认证使用。
5. 下文的云端读写均显式使用 `--as user`。以退出码与 JSON 的 `ok` 核对结果；部分失败时保留本地文件和进度。

## 解析或创建归档文件夹

默认先列个人云盘根目录的直接子项。根目录和子文件夹均按实际返回的 `data.has_more` 分页，将 `data.next_page_token` 作为下一页的 `page_token`。缺页或游标无效时，先解决读取问题再创建。

```bash
lark-cli drive files list --params '{"folder_token":"","page_size":200}' --as user --format json
lark-cli drive files list --params '{"folder_token":"<父文件夹 token>","page_size":200}' --as user --format json
```

- 根目录已有唯一 `type=folder` 且 `name=视频号爆款拆解` 的条目就复用其 `token`。完全无同名项时执行 `lark-cli drive +create-folder --name '视频号爆款拆解' --as user`，保存返回的 `folder_token`。同名多项或同名非文件夹时请用户指定准确位置。
- 用户指定了 Drive 父文件夹时，直接通过 `lark-cli drive +inspect --url '<文件夹 URL>' --as user` 核实类型、名称、token，使用该位置作为每条视频目录的父级。裸 token 配合 `--type folder`。用户提供的是路径时按层核对直接子项，遇到重名让用户选。读取指定位置失败时报告原始错误。
- 在父文件夹中，同法查找本条视频目录。需要新建时执行 `lark-cli drive +create-folder --folder-token '<父文件夹 token>' --name '<本条目录名>' --as user`。保存目录 token 和返回的链接。批量处理共用一个父文件夹时，解析与创建目录串行执行。

### 收到普通文档链接时

先识别链接表示的资源及用户指的归档位置。`drive +inspect` 返回该文档自身的类型、标题、token 和规范 URL。`drive.metas.batch_query` 的结果也只描述文档自身。普通 `/docx/…` 的 token 不能作为 Drive 文件夹 token。

- 如果它实际属于知识库，已有相应权限时可以用 `lark-cli wiki +node-get --node-token '<docx URL>' --as user` 确认对象与 `space_id`、`node_token`。当用户想放在**该节点下**且节点可承载子项时，根据解析出的 Wiki 节点操作。如果用户说的是**与文档同层**，应核验其 `parent_node_token` 所指的节点。
- 如果已有候选 Drive 文件夹（例如用户同时给了文件夹链接，或任务收据记录了明确的所在目录），分页列其直属子项，用 `type=docx` 和精确的文档 token 验证该条目的 `parent_token` 及文件夹身份。核实后可将文档**所在文件夹**作为指定父级并保存其规范链接。
- 仅有普通文档链接且无法核实可用父位置时，请用户给出父文件夹链接或选择「我的空间 / 视频号爆款拆解」。得到选择后再写入。不以文档同名搜索结果猜位置，不扫描整个云盘，也不默默改投默认目录。若收到的是无法持久保存的分享链接，按同样方式取得可验证的标准位置。

### 明确指定已有知识库位置时

如果用户明确给自己的 Wiki 父节点链接，读取 `lark-cli skills read lark-wiki`，仅为这一路径补必要 Wiki 权限。用 `lark-cli wiki +node-get --node-token '<Wiki URL>' --as user` 读取实际的 `space_id` 和 `node_token`。沿用经用户指定的旧配置（知识库名称和节点路径）时，用 `wiki +space-list` 精确找到知识库，沿路径用 `wiki +node-list` 列全各层直接子项。只有末级名称时遍历该空间，逐页以 `has_more` 为准，使用唯一命中。有歧义时请用户提供父节点链接。

在该父节点下先列现有子节点，再用 `lark-cli wiki +node-create --parent-node-token '<父节点 token>' --title '<本条目录名>' --as user` 创建承载本视频资料的节点。下文文件上传的 `--folder-token` 改为 `--wiki-token <本条节点 token>`，创建报告的 `--parent-token` 传本条节点 token。核验目录时用 `lark-cli wiki +node-list --space-id '<空间 ID>' --parent-node-token '<本条节点 token>' --as user` 列全子节点，按 `obj_type` 与 `obj_token` 核对。

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
