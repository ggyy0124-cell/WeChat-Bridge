# AGENTS.md：仓库约定

WeChat Bridge 是微信消息推送桥接服务（fork 自 yuuouu/WeChat-Bridge）。动手前先读 [README](README.md) 与 [贡献指南](.github/CONTRIBUTING.md)，变化记录见 [docs/CHANGELOG.md](docs/CHANGELOG.md)。

## 开发与检查

- `make install-dev` 安装依赖；`make check` 运行 ruff 检查、格式检查与全部测试，提交前须通过。
- 行为变化要有对应测试；接口或配置变化同步更新 README 与 docs。

## 分支、提交与 PR

- 开发不要用 worktree：直接在原仓库从最新的 `main` 新开临时分支处理；开发完删除临时分支，切回 `main` 并拉取更新。
- 提交使用 Conventional Commits，类型用英文、描述用中文。
- 这是 fork 仓库，`gh pr create` 等命令必须指定 `-R ggyy0124-cell/WeChat-Bridge`，否则会默认指向上游。
- `main` 受保护：只能经 PR 合入，CI 的 `lint`、`test (3.10)`、`test (3.11)`、`test (3.12)` 必须通过，并需要 1 个批准（作者本人不计）。合并后自动删除远端分支。

## 版本与发布

- 版本号格式为「上游版本-本分支修订号」，如 `1.4.0-0.2`；变化写进 `docs/CHANGELOG.md`。
- 推送 `vX.Y.Z-N` 标签后自动构建镜像 `ghcr.io/ggyy0124-cell/wechat-bridge` 并发布 Release。
