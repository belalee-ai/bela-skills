# 依赖 skill 的版本门禁与定向更新

本参考依据 2026-10-31 的只读核验。缺失依赖、CLI 不兼容、所选语音模型或服务未就绪时仍须停止，由用户准备后复检。

## 1. 规则与范围

每次实际使用某个依赖 skill 之前，都要检查该 skill 的最新状态。**已经安装且确认过期的 skill，按原来源、原安装范围自动定向升级，然后重新读取升级后的说明、复检能力，再继续。** 用户已授权这一更新行为，不再次要求确认。

- 更新只覆盖本次需要使用的那个 skill；必须明确名称与 global/project 范围，不使用无名称的全量 `update`、`update -g`、`update -p` 或通配符。
- skill 缺失时停止，不能借 `update`、`add`、临时 `npx` 或包缓存悄悄补装。尤其不能只看 lock：必须确认真实 `SKILL.md` 存在，链接目标可读。
- 仅沿用可追溯的已安装来源；不搜索同名仓库替换来源，不迁移安装范围，不新增依赖 skill。
- 本地修改先保留备份和差异记录，再执行已授权更新；更新失败保留原文件和错误，不切换来源。
- 网络失败、来源不明、上游删除或路径歧义、版本追踪字段缺失等均记为 `unknown` 或具体错误并停止。不能把“未查到更新”“被跳过”“退出码为 0”写成“已经最新”。
- 升级后需从真实安装位置重新读取 `SKILL.md` 及本次需要的参考文件。对话里先前加载的说明可能已旧，不能继续沿用。

## 2. 先识别安装来源和管理器

只读取目标条目的必要来源字段。通常全局记录在 `~/.agents/.skill-lock.json`，项目记录在 `skills-lock.json`；记录位置以当前安装器为准。不要转储整个配置、环境变量、认证文件或 token。

需要记录：skill 名称、真实安装位置、安装范围、来源类型、来源仓库/公开主机、skill 子路径、选定 ref，以及本地追踪 hash/digest。来源 URL 展示时去掉用户名、密码、查询参数和片段。

目前可追溯的来源例子（示例不是所有用户的固定配置）：

| skill | 已知官方或安装来源 | 可用追踪信息 |
| --- | --- | --- |
| `hypit` | `hypit-ai/hypit`，`skills/hypit/SKILL.md` | GitHub 仓库和 skill 文件夹 tree hash |
| `wechat-video-downloader` | `redfox-data/redfox-community`，`skills/wechat-video-downloader/SKILL.md` | GitHub 仓库和 skill 文件夹 tree hash |
| `lark-shared` / `lark-doc` / `lark-drive` / `lark-wiki` | `https://open.feishu.cn` 的 well-known skills 发布源 | `sourceBaseUrl`、单 skill URL、`wellKnownDigest` |

这些来源从实际安装记录核验，不是按名称猜测。其他安装渠道（插件、系统内置、Git checkout）遵循其原渠道的**单项**检查和更新能力；不能擅自交给另一安装器覆盖。不能获得可核验最新状态时停在版本门禁。

如果 lock 固定了 tag/commit，必须说明“该 ref 的状态”与“上游最新发布”不同。不能把固定 ref 的一致性叫作最新，也不能偷偷改 ref；先解决与“始终最新”策略的冲突。

## 3. 当前 skills CLI 的精确命令与陷阱

存在的本地管理器可这样只读识别：

```sh
npx --no-install skills --version
npx --no-install skills --help
npx --no-install skills update --help
```

`--no-install` 保证缺少包时不自动安装。若这些命令因未安装而失败，报告“skill 管理 CLI 缺失”，等待用户安装；不要去掉 `--no-install`。已直接安装的 `skills` 可调用其已核验 launcher。

本次本地缓存的 CLI 为 **skills 1.7.4**，支持以下**有写入行为**的定向更新语法：

```sh
# 已安装的全局 Hypit skill
npx --no-install skills update hypit -g -y

# 已安装的项目 Hypit skill：从该项目根目录运行
npx --no-install skills update hypit -p -y

# 每次按待使用的确切名称替换 hypit；不省略名称或范围
```

`-y` 不代替 scope；总是显式给 `-g` 或 `-p`。该更新流程会先查询原来源，仅对筛选名称执行必要更新。主流程可以在授权范围内把它作为“定向检查并更新”操作，但必须核验实际结果，不能称它是只读检查。Hypit 官方分发说明同样给出了 `skills update hypit -g` 的指定更新方式。[Hypit 分发说明](https://github.com/hypit-ai/hypit/blob/main/skills/hypit/references/environment/distribution.md)

### 不要盲信 `skills check` 是只读

官方最新文档将 `check` 描述为只读检查；当前 GitHub main 的源码也把它分派到 `runUpdate(restArgs, 'check')`，并支持名称筛选和安装范围。[CLI 文档](https://github.com/vercel-labs/skills/blob/main/docs/commands.md)、[官方 CLI 源码](https://github.com/vercel-labs/skills/blob/main/src/cli.ts)、[检查/更新实现](https://github.com/vercel-labs/skills/blob/main/src/update.ts)

**但本次已安装的 skills 1.7.4 发布包实际把 `check`、`update`、`upgrade` 都调用到同一个 `runUpdate(restArgs)`。因此在这份安装中，`skills check` 可能执行更新。** 同时，GitHub main 的 `package.json` 也标为 1.7.4，所以单靠版本号不能判断已安装包是否具有真正的只读 check。需要核验所用安装的真实实现或经过验证的发布说明，不能仅看网站文档。[上游包版本声明](https://github.com/vercel-labs/skills/blob/main/package.json)

仅在确认所用实现存在真正 check 模式之后，才可以使用：

```sh
npx --no-install skills check hypit -g
npx --no-install skills check hypit -p
```

这是**有条件可用**的语法，不是在本次 1.7.4 安装上已验证只读的命令。`check` 返回 1 既可能意味着发现更新，也可能意味着检查失败；读取具体输出，分别处理。帮助输出不证明实际行为。没有可靠只读 check 时，按下一节只读比较来源，或执行已授权的单项“检查并更新”；不要为了检查而全量更新。

## 4. 无可靠只读 check 时如何核验

只查询当前目标 skill 已记录的来源，不访问无关私有仓库，也不打印认证信息。

### GitHub 来源

1. 从目标条目取得仓库、选定 ref、skill 路径及 `skillFolderHash`。没有 ref 时，先读取仓库的实际默认分支/HEAD，记录本次解析到的 commit；不要永远假定是 `main`。
2. 只读请求该 commit 的 Git tree，定位包含 `SKILL.md` 的完整 skill 文件夹，取得 tree SHA。必须覆盖整个文件夹，不能只比较 `SKILL.md`，否则会漏掉 references/scripts 的更新。
3. 对于当前记录中采用 Git tree SHA 的条目，将远端目录 tree SHA 与记录值比较。不要把 Git tree SHA 与普通文件 SHA256 混作同一种算法。若安装器采用其他内容 hash，使用该安装器的已核验算法。
4. 相同可证明“安装记录对应内容与所查来源版本一致”；还需确认真实本地文件未被单独修改、未缺失。存在本地偏移时保留备份，再按原源刷新并复检。
5. 不同则自动执行指定名称和范围的更新。更新后重读目标条目、核验安装内容和新的远端标识；上游仍可能继续变化，结果注明检查时间与 commit，避免声称永久最新。

### Well-known 来源

1. 使用条目已有的 `sourceBaseUrl`，读取该来源公开的 skills 索引，只选目标名称。当前 skills 实现识别 `/.well-known/agent-skills/index.json` 和 `/.well-known/skills/index.json`；使用发布者实际存在的索引。
2. 如果目标索引条目提供受支持的内容 digest，用它与记录的 `wellKnownDigest` 比较；不要将索引协议的 `version`（例如 0.2.0）误当作 skill 内容版本。
3. 无发布方 digest 时，读取该目标 skill 的完整文件集合，按安装器定义的算法比较。当前 skills 算法对排序后的相对路径、NUL、文件内容、NUL 依次计算 SHA256；仅哈希 `SKILL.md` 不能代替整个 skill 的 digest。
4. 更新仍用 `skills update <确切名称> <明确范围>`，不能照搬 CLI 可能显示的无 `--skill`、全来源 `add` 建议，避免把同源其他 skill 也装入。
5. 索引不可达、目标消失、文件缺失或 digest 无法验证时停止，不将它当作无需更新。



## 5. “skill 最新”与“执行环境兼容”分开检查

更新 skill 只更新操作说明，不会自动把 CLI、模型、服务和项目输出变成就绪状态。Hypit 官方明确将 skill、`@hypit/hypit` executable 和视频项目视作三个独立生命周期。[Hypit 分发说明](https://github.com/hypit-ai/hypit/blob/main/skills/hypit/references/environment/distribution.md)

版本门禁通过后，再检查：

- 新说明需要的命令和选项，是否真的存在于已安装 CLI；分别记录 CLI 版本与实际 launcher。新 skill 提及某个参数不代表旧 CLI 已支持它。
- FFmpeg/FFprobe、选择的 standalone Whisper CLI 和模型文件，或明确选择的 Hypit endpoint，是否仍符合实际分析任务。
- 必需的模型、服务、账号和语言资源是否就绪；skill 自动升级不授权下载新模型、切换识别后端或付费调用。

CLI 缺失或与新 skill 不兼容时停止并说明所需准备；不执行失败后降级，不把“skill 已最新”当作环境通过。用户授权自动升级 skill，并不自动扩大为重装所有执行工具、模型和项目依赖。用户另行完成必要环境安装/升级后，重新执行 skill 版本门禁和能力门禁。

成功条件应同时为：**目标 skill 最新状态已核验；所需 CLI 兼容；选定模型/服务就绪；本次操作权限与付费范围成立。**

建议单次记录字段：`skill`、`scope`、`source`、`ref`、`before_identity`、`remote_identity`、`checked_at`、`status`、`update_result`、`after_identity`、`cli_version`、`compatibility_result`。不记录凭据。

