# Dataset与DataLoader：样本、采样、分批、补齐和数据吞吐

## 训练循环前面还有一条数据流水线

Dataset定义怎样取得样本，Sampler定义读哪些样本及顺序，DataLoader负责迭代、组成batch和可选并行加载，collate_fn把多条样本整理成模型输入。

它们和模型forward不同。训练慢可能是磁盘、解码、tokenization或搬运，而不是网络结构计算慢。把所有逻辑塞进模型会使数据问题难以定位。

## 两类数据集

Map-style常实现__len__与__getitem__，可以按索引取样。Iterable-style按流产生样本，适合某些大文件或远程流，但不一定支持随机访问或可靠长度。

多worker或多rank迭代流时，必须设计分片，避免每个进程从头读取同一数据。仅增加worker数可能使样本重复，不能当作自动正确的并行方案。

## Shuffle与训练/验证边界

Shuffle改变顺序，不改变数据所属集合。应先按文档、客户、时间等任务单位划分训练/验证，再在训练内部打乱。先把近重复切片打散再随机划分，可能造成泄漏。

打乱也不等于类别平衡。加权采样会改变实际训练分布，影响损失和指标解释；验证集一般仍应代表希望评估的真实分布。

## Collate与padding

三条序列长度[2,4,3]，补齐到当前batch最大长度4，总槽位12，有效token9，padding3，占25%。pad_to_max_length若补到固定128，则浪费会大得多。

attention mask区分真实位置与padding；loss label还应按约定忽略padding和非监督部分。右padding还是左padding取决于模型和任务配置，不能一概而论。

按近似长度组batch能减少padding，但会改变样本组合和顺序，需保留足够随机性并评估偏差。Packing与padding是不同策略，packing还需考虑样本边界。

## drop_last不是无害默认

10条数据、batch_size=4：保留尾部得到[4,4,2]，drop_last得到[4,4]，少看2条。训练时某些层或分布式配置需要固定batch，但丢弃会影响数据覆盖；验证阶段丢尾可能直接漏算样本。

最后小batch的mean loss不能与大batch均值等权汇总。应按样本数或有效监督token数累计分子分母。计算指标时同样注意缺失尾部和重复样本。

## worker、prefetch与内存

num_workers增加加载并行，prefetch_factor控制预取数量，persistent_workers减少反复启动。更多并行可能提高吞吐，也可能增加进程复制、共享内存、文件句柄和队列占用。

粗略预取数据本体约worker数×每worker预取批数×每批字节；还要加当前batch、解码临时对象和进程开销。4个worker、每个预取2批、每批100MiB，队列数据本体可能约800MiB，不是整个训练内存。

pin_memory有助某些CPU到GPU搬运路径，non_blocking能在支持的条件下安排异步传输；它们不是无条件加速开关，仍要测实际重叠和瓶颈。

## 复现与部署环境

Sampler顺序、worker随机源、数据增强和流游标都影响复现。Windows或spawn启动方式还要求可序列化对象及正确的入口保护；不要把仅在单进程能运行的lambda/闭包随意用于多进程worker。

不要在每个训练batch临时调用业务数据库或生产接口取标签：高并发、不稳定源和版本变化会降低可复现性。通常先生成带版本的训练快照，加载阶段读取该快照。

## 练习

数学示例核对padding占比和drop_last覆盖。检查你自己的样本：是否保存稳定ID、标签版本、来源、长度和划分组？训练器输出的batch中是否还保留可追溯ID？

## 来源

PyTorch基础数据教程与DataLoader源码；形状、吞吐预算及业务数据策略独立编写。本文没有实际启动多worker或加载真实数据集。

核验日期：2026-10-04。固定来源：

- [pytorch/tutorials / beginner_source/basics/data_tutorial.py](https://github.com/pytorch/tutorials/blob/11512db7cbbcc4b530ecfc63205d3fed13fa190d/beginner_source/basics/data_tutorial.py)
- [pytorch/pytorch / torch/utils/data/dataloader.py](https://github.com/pytorch/pytorch/blob/496340f06ef7bda2800522429ba3f4e3473a92fa/torch/utils/data/dataloader.py)

[专题入口](README.md) · [验证记录](VALIDATION.md)
