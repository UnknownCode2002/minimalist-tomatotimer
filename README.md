# 番茄钟悬浮计时器 🍅

一个运行在 Windows 平台的番茄工作法辅助工具。它以透明悬浮窗形式置顶显示，帮助你用 25 分钟专注 + 5 分钟短休息的节奏进行学习或工作。

> 当前版本：`1.0.1`  
> 项目文件：`tomato_timer.pyw`  
> 本地统计数据：`stats.json`（默认不会上传到 GitHub）

## 功能特点

- **透明悬浮窗**：半透明、始终置顶，可拖拽到屏幕任意位置。
- **标准番茄周期**：25 分钟专注 → 5 分钟短休息；每完成 4 个番茄后进入 15 分钟长休息。
- **右键圆角菜单**：开始、暂停、重置、跳过、查看统计、开关通知、开关自动切换。
- **默认手动切换**：启动时自动切换默认关闭，阶段结束后可手动开始或开启自动切换。
- **阶段切换提醒**：每个阶段结束时弹出通知，可在菜单中关闭。
- **每日统计**：自动记录当天完成的番茄数，并保存累计完成数量。
- **零外部依赖**：仅使用 Python 标准库 `tkinter`，单文件即可运行。

## 运行环境

- Windows 10 / 11
- Python 3.9+（项目使用标准类型注解 `dict[str, int]`）
- 无需安装第三方依赖

## 运行方式

### 方式一：直接双击

在 Windows 中直接双击：

```text
tomato_timer.pyw
```

### 方式二：命令行运行

在项目目录下执行：

```bash
python tomato_timer.pyw
```

## 使用说明

| 操作 | 说明 |
|------|------|
| 鼠标左键拖拽 | 移动悬浮窗位置 |
| 鼠标悬停 | 窗口透明度提高，便于查看 |
| 鼠标双击 | 开始 / 暂停当前计时 |
| 鼠标右键 | 打开控制菜单 |

### 右键菜单选项

| 选项 | 功能 |
|------|------|
| ▶ 开始 | 开始或继续计时 |
| ⏸ 暂停 | 暂停当前计时 |
| ⏹ 重置 | 重置到就绪状态 |
| ⏭ 跳过 | 跳过当前阶段，进入下一阶段 |
| 📊 查看统计 | 查看今日与累计番茄统计 |
| 🔔 通知：开/关 | 切换阶段切换通知 |
| 🔄 自动切换：开/关 | 切换阶段结束后是否自动继续 |
| ❌ 退出 | 关闭程序 |

## 番茄工作法

1. 选择一个待完成的任务。
2. 设定 25 分钟专注时间。
3. 专注工作直到番茄钟结束。
4. 休息 5 分钟。
5. 每完成 4 个番茄，休息 15 分钟。
6. 重复以上步骤。

## 文件说明

```text
project-tomatoTimer/
├── tomato_timer.pyw     # 主程序，单文件运行
├── stats.json           # 本地自动生成，记录每日番茄完成统计
├── README.md            # 项目说明
├── CHANGELOG.md         # 版本变更日志
├── VERSION              # 当前版本号
├── LICENSE.md           # 许可证说明
└── .gitignore           # Git 忽略规则
```

## 版本管理

本项目已准备适合上传 GitHub 的版本管理基础文件：

- `VERSION`：记录当前发布版本，当前为 `1.0.1`。
- `CHANGELOG.md`：记录每个版本的更新内容。
- `.gitignore`：忽略 Python 缓存、虚拟环境、IDE 文件和 `stats.json`。
- `LICENSE.md`：MIT 开源许可证。

### 上传到 GitHub

在 GitHub 创建一个空仓库后，在项目目录执行：

```bash
git init
git add README.md CHANGELOG.md VERSION LICENSE.md .gitignore tomato_timer.pyw
git commit -m "chore: prepare github release"
git branch -M main
git remote add origin git@github.com:YOUR_USERNAME/project-tomatoTimer.git
git push -u origin main
```

> 注意：`stats.json` 已被 `.gitignore` 忽略，不会被提交或上传。

### 发布新版本

后续如需发布新版本，可按以下流程：

```bash
# 1. 修改 VERSION 文件，例如改为 1.1.0
# 2. 更新 CHANGELOG.md 的 Unreleased 内容
# 3. 提交代码
git add VERSION CHANGELOG.md
git commit -m "chore: release v1.1.0"

# 4. 打 Git 标签
git tag -a v1.1.0 -m "Release v1.1.0"
git push origin v1.1.0
```

GitHub Release 标题可使用：

```text
v1.1.0
```

发布说明可从 `CHANGELOG.md` 中复制对应版本内容。

## 隐私与数据

- 番茄统计数据仅保存在本地 `stats.json`。
- 程序不会联网、不会上传数据。
- 如果你希望 GitHub 仓库保持干净，请确认 `.gitignore` 已生效，避免提交个人统计记录。

## 常见问题

### 双击没有反应？

请确认电脑已安装 Python，并且 `.pyw` 文件关联了 Python。也可以在命令行中运行：

```bash
python tomato_timer.pyw
```

如果命令行显示错误信息，可以根据错误提示排查。

### 可以修改专注时间吗？

可以。打开 `tomato_timer.pyw`，修改 `STATE_CONFIG` 中各阶段的 `duration` 值即可。时间单位为秒，例如 25 分钟为 `25 * 60`。

### 可以上传到 GitHub 吗？

可以。当前项目已包含 README、版本文件、变更日志和 `.gitignore`，适合直接初始化为 Git 仓库并上传。上传前请确认 `stats.json` 没有被手动强制提交。

## 后续可优化方向

- 增加设置界面，支持自定义专注/休息时间。
- 增加开始菜单快捷方式或打包为 `.exe`。
- 增加最近 7 天统计图表。
- 增加 macOS / Linux 兼容版本。
