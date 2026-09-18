# Jev 流式思考监督首轮验证

> 日期：2026 年 9 月 18 日。样本很小，属于机制与可行性实验，不是模型质量基准。

## 结论

第三方网关支持 SSE，并会返回 `reasoning` 增量；Jev 可异步检查已经出现的思考窗口。**在本轮真实请求里，监督器没有及时打断任何一次推理，也没有证明可以缩短作答时间。** 三道简单题通常只思考约 20–30 token，等 Jev 判断的成本高于可能节约的思考时间。较长的硬币题中，Jev 倾向继续，或判断在模型答完之后才返回。

模拟流测试证明控制器能在正文生成前关闭流；但现有接口的“继续”是关闭当前请求后重新发起请求，不是恢复同一段内部计算。关闭客户端流也不能保证供应商停止计算和计费。

## 实现

- [评测脚本](../scripts/evaluate_thinking_supervisor.py) 使用 `.env` 中的 TypeSafe 和第三方模型配置，不记录密钥。
- SSE 中提取 `reasoning` / `reasoning_content`，达到字符检查点时异步调用 Jev；用户回答继续流出，不等待 Jev。
- Jev 同时回答 `continue/answer_now` 和“是否仍需实质性推理”。只有两项均达到保守阈值、且主模型尚未输出正文时，才关闭流并重新请求直接回答。
- 模型、网关或 Jev 出错会记录错误；Jev 失败时不打断主模型。结果只落盘答案、时长、用量和判断概率，不落盘原始思考文本。
- `baseline` 不调用 Jev；`observe` 只记录判断；`intervene` 允许打断。检查点和阈值均可配置。

## 实测

使用当前 `.env` 配置；网关在响应里报告的模型 ID 为 `cline-pass/deepseek-v4-flash`，**不是最初提到的 `deepseek-v4.1-flash`**。配置是否实际映射到同一模型，需要供应商确认。所有模式均发送配置中的思考档位，但本实验未证明网关确实执行了该档位。

低检查点实验设置为 50 个思考字符、Jev 双条件阈值 0.7、最多 4096 输出 token。四题各跑一次三种模式，共 12 个模型请求、8 个 Jev 判断；12 个最终答案都正确，8 个 Jev 判断都在模型流结束后才完成，真实打断次数为 0。

| 题目 | baseline 答案就绪 | observe 答案就绪 | intervene 答案就绪 | 观察 |
| --- | ---: | ---: | ---: | --- |
| 书架算术 | 4.98s | 1.91s | 2.32s | Jev 想收束，但已答完 |
| 小数比较 | 2.14s | 2.77s | 2.10s | Jev 想收束，但已答完 |
| 数列 | 2.19s | 2.23s | 2.25s | Jev 想收束，但已答完 |
| 12 枚硬币 | 4.40s | 2.81s | 16.00s | Jev 倾向继续；16s 是单次异常慢响应，原因未确认 |

Jev 判断耗时约 1.33–1.53s。这里“答案就绪”只计主模型流完成时间；监督判断可能在答案之后完成，完整评测用时另记。各模式只跑一次，顺序固定，后续请求还可能享受提示缓存，所以不能把表中单次差异解释为监督提速。尤其 `intervene` 模式本次没有实际干预。

原始结果：[简单题](../artifacts/thinking-supervision-low-checkpoint-v1.json)、[压力题](../artifacts/thinking-supervision-stress-low-checkpoint-v1.json)。

最初的高检查点探测另存为 [简单题 pilot](../artifacts/thinking-supervision-v1.json) 和 [压力题 pilot](../artifacts/thinking-supervision-stress-v1.json)。pilot 的压力题 `Yes` 曾被旧版大小写敏感评分误记为错；现只把派生的 `correct` 改为 `true`，原始回答和计时没有更动。

## 下一步门槛

只有拿到**真实长时间、且确实在反复空转的推理任务**，这个方案才值得进一步验证。应先收集任务与耗时分布，确认“发现冗余后的剩余推理时间”通常显著大于 Jev 判断和重启的开销；再用同一批任务重复运行，统计实际及时打断率、最终正确率、P50/P95 延迟、总费用和错误打断率。可以把检查点从固定字符数改为按阶段或工具调用触发。纠正错误思路需要更具体的证据和反馈机制，本版尚未实现自动纠错。

复现命令：

```sh
python3 scripts/evaluate_thinking_supervisor.py --output artifacts/thinking-supervision-low-checkpoint-v1.json --min-reasoning-chars 50
python3 scripts/evaluate_thinking_supervisor.py --dataset evals/thinking-supervision-stress-v1.json --output artifacts/thinking-supervision-stress-low-checkpoint-v1.json --min-reasoning-chars 50
python3 -m unittest discover -s tests -v
```
