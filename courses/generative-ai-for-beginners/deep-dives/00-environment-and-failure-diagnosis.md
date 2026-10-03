# 第00课深化：环境、凭据与故障定位

> 对应 [环境准备概览](../00-course-setup.md)。核对日期：2026-10-04；上游固定快照：d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8。
> 命令用于说明本地工作流程，本文没有替用户安装依赖或创建云资源。平台可用性和费用以实际账户为准。

## 1. 为什么“能打开 Notebook”还不够

一个教学示例能成功运行，依赖至少六层：文件版本、解释器、依赖、运行配置、网络与认证、服务端模型配置。故障定位应找到具体失败层，而不是反复改提示词。

同一个电脑中，Windows Python、WSL Python、容器 Python 和 Notebook kernel 可以是四套环境。Windows 安装了包，不代表 WSL 已安装；终端安装成功，不代表 Notebook 选择了那个解释器。

## 2. Fork、clone 与知识库有什么区别

- Fork 在 GitHub 创建上游仓库的派生副本，用来改课程代码。
- clone 把仓库文件和历史下载到本地，用来运行与编辑。
- 中文知识库保存解释、练习与来源，不必复制所有图片、权重或完整课程历史。
- 固定 commit 让某篇代码评述能被复核；仅链接 main，未来代码变化后结论可能不再成立。

本知识库将上游代码解释与原创工程补充分开。要运行原课代码，使用上游或自己的 fork；要阅读机制和复习，使用本专题即可。

## 3. 选择一套主要环境

| 方式 | 优势 | 需要管理的内容 |
|---|---|---|
| 本地 venv | 轻量、容易检查解释器 | 系统库与 Python 版本 |
| Conda | 可管理部分非 Python 依赖 | channel、环境文件和版本 |
| Dev Container | 团队共享环境描述 | Docker、镜像、磁盘与网络 |
| Codespaces | 浏览器中准备开发环境 | 账户配额、Secrets、远端状态 |
| Jupyter | 适合逐步探索 | kernel、执行顺序与隐藏状态 |

容器降低环境差异，但没有自动消除依赖漂移：未固定镜像与依赖版本，重新构建仍可能得到不同结果。Conda 和 venv 也不是越多层叠加越可靠。先确定一个解释器，再让编辑器与 Notebook 使用它。

## 4. Windows 与 WSL 的最小定位方法

在实际运行程序的终端检查：

```bash
python --version
python -c "import sys; print(sys.executable)"
python -m pip --version
git --version
```

在 Notebook 中检查：

```python
import sys
print(sys.executable)
```

解释器路径应能对应到选择的环境。使用 `python -m pip` 将安装动作绑定到当前 Python，比猜测裸 pip 的归属更清楚。

在 Linux/WSL 的课程代码目录中，可使用：

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

此处 requirements.txt 指上游课程的依赖文件，不是本知识库根目录文件。依赖安装可能访问网络；实际版本仍需检查。WSL 遇到 externally-managed-environment 时，应优先创建虚拟环境，而不是直接修改系统 Python 管理状态。

Windows 与 WSL 的代理和 DNS 配置也可能不同。PowerShell 能访问服务，不证明 WSL 能访问。先在失败环境确认目标域名解析、代理与 TLS；不要在公开日志中打印凭据或完整认证头。

## 5. 凭据配置不能混用

课程存在不同服务提供方路径。端点、密钥、部署名和模型名应来自同一服务配置，不能把一个平台的 token 填进另一个平台的客户端。

| 配置 | 含义 | 常见错误 |
|---|---|---|
| endpoint | 请求发到哪里 | 使用网页地址代替 API 地址 |
| credential | 谁在调用 | 过期、空值或错服务密钥 |
| deployment/model | 调用哪个部署或模型 | 展示名称与 API 标识混淆 |
| API/SDK version | 使用哪套协议 | 复制旧调用签名 |
| runtime environment | 程序实际读哪个配置 | 编辑文件后进程未重启 |

.env 是本地开发便利机制，不是加密保险箱。应忽略真实配置，发布仅含占位符的 .env.example。若凭据已经进入 Git 历史，后续删除文件不能撤销泄漏，应处理凭据本身及历史暴露。

配置检查只需要输出“是否设置”，不要输出密钥内容：

```python
import os
for name in ("AZURE_INFERENCE_ENDPOINT", "AZURE_INFERENCE_CREDENTIAL"):
    print(name, "set" if os.getenv(name) else "missing")
```

这段代码不会自动加载 .env；必须由启动环境注入，或先按所用配置方案加载文件。变量非空也不证明它有效。

## 6. 按层排错

| 症状 | 优先检查 | 不应直接得出的结论 |
|---|---|---|
| ModuleNotFoundError | 当前解释器和依赖 | 模型服务故障 |
| Notebook 运行旧结果 | kernel、重启、从头执行 | 修改后的代码已通过 |
| DNS/连接超时 | 失败环境的网络与代理 | API key 一定无效 |
| 401 | 认证方式、密钥、目标端点 | 必须重新安装 Python |
| 403 | 权限和服务访问条件 | 提示词不够好 |
| 404 | 路径、模型或部署标识 | 服务完全不存在 |
| 429 | 具体错误体、配额和速率 | 无限重试会恢复 |
| 返回格式变化 | SDK、模型与响应类型 | 输出必定在旧字段里 |
| JSON 无效 | 输出约束与解析边界 | 认证失败 |

状态码只能缩小范围，错误体和请求 ID 才提供更具体证据。对超时和临时故障使用有限重试；对明确无权限和非法参数，先修配置。

## 7. 可复现的运行记录

工程补充：保存上游 commit、操作系统、Python 路径与版本、依赖版本、Notebook kernel、SDK 版本、端点类别、模型/部署标识、输入与结果摘要。不要保存密钥。

Notebook 应重启 kernel 后从第一格运行，避免旧变量掩盖缺失 import。将核心逻辑移到模块、Notebook 保留演示，可以减少执行顺序依赖。

云服务页面名称、免费配额、退役时间与模型可用区域会变化。本文仅核对课程快照中的说明，不把它们当作当前账户的服务保证。

## 8. 验收练习

先跑 [离线示例](../examples/README.md)，验证 Python、路径与数据契约；再用所选提供方的最小请求验证网络和认证；最后运行课程完整样例。

请说明：为什么离线脚本成功不能证明云模型能调用？因为离线脚本不测试网络、凭据、模型部署和 SDK 请求协议。反过来，云请求成功也不证明业务授权、证据链和结果校验正确。

## 来源

- [上游环境准备](https://github.com/microsoft/generative-ai-for-beginners/blob/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8/00-course-setup/README.md)
- [上游本地安装](https://github.com/microsoft/generative-ai-for-beginners/blob/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8/00-course-setup/02-setup-local.md)
- [上游提供方说明](https://github.com/microsoft/generative-ai-for-beginners/blob/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8/00-course-setup/03-providers.md)
- [Microsoft MIT 许可](LICENSE-Microsoft.txt)。故障分层与验收流程为原创工程补充。
