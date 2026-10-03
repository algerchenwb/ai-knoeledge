# 00 · 环境准备与仓库导航

> 原课程解读与中文重写；标为「工程补充」的内容是额外实践，不是原仓库承诺。核对日期：2026-10-03。

## 这节课解决什么问题

先把学习材料、Python 环境和模型接入分开，避免“程序跑不起来”与“模型效果不好”混在一起。微软提供 Codespaces、本地环境和开发容器三条路线。对 Windows + WSL 开发者，建议将 Python、依赖与运行命令放在同一个 WSL 环境，减少解释器与路径混用。

## 仓库怎么看

根 README 是总目录；00 是环境准备；01—05 是基础概念与提示词；06—11 是应用构建；12—14 是体验、安全、生命周期；15—21 是 RAG、开放模型、Agent、微调和模型家族案例。每个课程目录的 README 是正文，python/、typescript/ 等目录是存在时的代码入口，translations/zh-CN/ 是中文翻译。不要把翻译目录当成另外一套课程，也不要假设每节课都有相同语言的实现。

Learn 表示以概念为主，Build 表示带构建示例；两者都需要验证。Notebook 中单元格执行次序会影响状态，读懂一段代码不等于整个 Notebook 可以从头运行。

## 最小本地路线

以下命令适用于 Bash / WSL。学习代码在原仓库运行，学习笔记保存在本知识库。

~~~bash
git clone --filter=blob:none --sparse https://github.com/microsoft/generative-ai-for-beginners.git
cd generative-ai-for-beginners
git sparse-checkout set --no-cone '/*' '!translations' '!translated_images'
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
~~~

然后安装目标章节要求的依赖。用 python -m pip 确保 pip 对应当前解释器；需要 Notebook 时还要安装并选择对应内核。稀疏检出会减少下载内容，后续需要中文翻译可调整稀疏规则。

## 模型接入的四个概念

| 概念 | 通俗解释 | 常见错误 |
| --- | --- | --- |
| API Key | 服务发给你的访问凭据 | 把密钥写到 Git |
| Endpoint / Base URL | 请求要到哪里 | 把门户网页当 API 地址 |
| Model | 调用哪个模型 | 使用未开放的名称 |
| Deployment | 云平台中的部署实例名称 | 把部署名和基础模型名混用 |

API 接口相似不代表完全兼容：角色、工具格式、图片输入和参数可能不同。课程快照已提示 GitHub Models 接入迁移，但具体服务是否可用、配额与计费要在使用当天查对应官方文档；不要依据目录名 githubmodels 判断平台现状。

## 排错顺序〔工程补充〕

1. 确认 python --version、虚拟环境和 Notebook 内核一致。
2. 确认环境变量已加载，不打印密钥本身；只检查是否存在。
3. 用一个最简单的文本请求验证地址、凭据与模型。
4. 401 先查凭据，403 查权限，404 查端点和部署，429 查配额及请求速率。
5. 超时查代理、DNS、网络与服务耗时，再考虑模型输入大小。

.env 适合本地练习，应加入 .gitignore；生产环境用部署平台的密钥管理。把模型供应商放在适配层，业务代码只依赖统一的生成、检索和工具接口。

## 练习与自查

建立虚拟环境，运行第 06 课最小示例，再故意改错一个部署名观察错误。能解释“Python 导入失败”和“服务返回 401”分别属于哪一层，就完成了本课的关键目标。

## 来源与继续阅读

- [原课程正文](https://github.com/microsoft/generative-ai-for-beginners/blob/d8ec07e31c4b32bd283d565c1abd9b58bb5cf2e8/00-course-setup/README.md)
- [专题目录](README.md)
