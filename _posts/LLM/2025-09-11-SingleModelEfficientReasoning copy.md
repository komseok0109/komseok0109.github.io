---
title: "[논문리뷰] Don’t Overthink It: A Survey of Efficient R1-style
 Large Reasoning Models"
date: 2025-09-11
last_modified_at: 2025-09-11
categories:
  - 논문리뷰
tags:
  - Reinforcement Learning
  - Reasoning
  - LLM
  - Efficiency
excerpt: "Efficient Reasoning + Kimi 1.5"
use_math: True
classes: wide
---
# Early Exit
- Monitoring-Based Early Exit
  - Confidence-based termination
  - Entropy-based dynamic control method
  - Budget-constrained early termination method
  - Probe-based early termination method
- Generation Control-based Early Exit
- Adaptive Early Exit

# CoT Compression
Construdct dataset with shorter CoTs and use SFT.
- Granularity-based CoT Compression
  - Token-level compression based on importance estimation
  - Step-level compression based on importance stimation
  - Chain-level compression via rewriting
- Parallel thinking-based Compression
- Reward-based Compression 

# Adaptive Reasoning
- TLB: p = accuracy of sample, $L_{\bar{r}}$ = avg token length of correct responses
  
$$
L_{\text{budget}} = p \cdot L_{\bar{r}} + (1 - p) \cdot L_{\max}
$$

- RL-based Adaptive Reasoning
  - With a Warm-up phase: short, long reasoning path 로 이루어진 data 로 SFT 한 이후에 RL. Input 을 보고 directly answer, short reasoning, long reasoning 으로 선택할 수 있도록 학습. 혹은, 첫 번째 stage에서 단순히 long-chain reasoning model 과 기존 llm 을 parameter merge 를 통해 long, short reasoning path 모두 가능한 모델을 생성한다. 두 번째 stage에서는 두 가지 optimization을 한다. Group level로 비슷한 task끼리 묶어 task의 복잡도에 따라 reasoning 모드를 결정할 수 있도록 학습한다. 또 각 sample에 대해서는 accuracy를 유지하는 동시에 간결한 reasoning을 생성하도록 학습한다.
  - W/O a Warm-up phase: SFT 없이 preference learning 을 사용하거나 confidence estimation 을 optimize 하도록 RL loss 를 조정하는 방식을 사용한다. e.g. DAST, Guided by Gut. Thinker 의 경우 먼저 short reasoning 을 통해 답을 출력하고 틀린 경우 full reasoning 을 통해 correction을 한다. 그리고 요약하는 방식을 사용한다. 각 stage마다 별도의 reward function 을 사용해서 학습한다.
- Reasoning-mode Switching: 입력을 보고 fast/slow thinking, thinking/no-thinking 을 결정할 수 있도록 학습한다.
  - Token-based mode switching (explicit): eos token 처럼 fast_think, slow_think 등의 control token 를 삽입해서 reasoing mode를 explicit하게 나타내도록 한다. SFT dataset을 만들 때 중요한 step이면 slow-thinking, 반복되고 중요치 않은 step일 수록 fast-thinking 으로 마킹한다. SFT 이후 TLB reward를 이용해 input의 난이도에 따라 reasoning 길이를 조정한다. 유사하게 AdaCtrl 이라는 연구는 easy, hard token을 이용해 초기에 모드를 결정하도록 SFT dataset을 만들어 학습시켰다.
  - Token-based reasoning mode switiching (implicit): 생략 부호를 prompt 에 넣어 모델이 필요할 때만 reasoing 을 확장하도록 유도한다. 혹은 모델이 입력 난이도에 따라 think, nothink 모드로 나뉠 수 있게 학습시킨다. AdaCoT framework 에서는 reasoning 이 필요하지 않은 query의 경우 think 토큰 사이에 text를 넣지 않고 think 토큰과 /think 토큰만 넣어서 바로 답변 가능한 건 바로 답변 하도록 유도했다. CAR framework는 먼저 모델이 간결한 정답을 생성하게 한 뒤 perplexity 를 이용해 confidence가 낮은 경우 더 reasoning을 이어가게 유도했다.
  - Multi-mode reasoning switching: fast/short, think/no-think 중 하나를 고르는 형식이 아닌 여러 개의 strategy 중 하나를 고르는 방식이다. binary switching 과 비슷하게 SFT로 다양한 길이의 path 학습하고, group-wise policy optimization 이용해 task 마다 길이를 조정할 수 있도록 한다. 혹은 생각하고 답내는게 아니라 생각하고 답내고 생각하고의 방식을 이용해 중간 답을 reward signal로도 이용하고 그다음 reasoning  step의 guide로도 이용하게 한다.
- Adaptive Rasoning with Length Reward: Reward/Penalty 를 이용해 직접적으로 모델이 불필요한 step 은 줄이는 동시에 정확도를 유지할 수 있도록 학습한다. Task의 난이도와 target length 를 이용해 reward 를 주는 방식을 사용한다. HAPO 는 정답을 맞춘 가장 짧은 response의 길이를 기록해놓고 그보다 짧으면 reward 를, 그보다 길면 penalty를 준다. 또 다른 연구는 각 prompt가 optimal length를 각각 가지고 있다고 가정한 뒤, sampling 을 통해 해당 길이를 계산한 뒤 그 길이를 기준으로 reward/penalty 를 준다. ALP 라는 연구는 rollout 을 여러 개 생성해서 solve rate 를 계산해 문제의 난이도를 추산하고 난이도에 따라 length penalty를 동적으로 부여한다. 마지막으로, SelfBudgeter라는 연구는 cold-start SFT 에서 모델이 문제를 보고 필요한 token budget 을 계산할 수 있도록 학습시키고 GRPO 에서는 token budge 안에서 token 사용을 최소화하도록 학습된다.

## Kimi K1.5 Length Penalty
[Kimi K1.5](https://arxiv.org/abs/2501.12599) Length Penalty: RL 학습을 하면서 response length 가 계속 늘어나는 것은 성능 향상에 기여할 수 있지만, training/inference cost가 증가하게 된다. 이러한 overthinking 문제를 줄이기 위해 length reward를 사용한다. 정답이 $y*$ 인 Prompt $x$ 에 대하여 k 개의 response $(y_1,z_1),\dots,(y_k,z_k)$ 를 생성했다고 하자. $y$ 는 정답, $z$ 는 reasoning step이다. $\text{len}(i)$ 를 $(y_i,z_i)$ 의 길이라고 하고 `min_len` 을 `len(i)` 의 최솟값, `max_len` 을 최대값이라고 하자. 만약 두 값이 동일하면 모든 response의 길이가 동일하니 length reward 를 0으로 둔다. 그렇지 않으면 아래의 식을 이용해 계산한다.

$$
\text{len_reward}(i)=\begin{cases}
    \lambda & \text{If } r(x,y_i,y*)=1 \\
    \min(0,\lambda) & \text{If }  r(x,y_i,y*) = 0
\end{cases}\quad\quad\text{  where  }\lambda=0.5-\frac{len(i)-min_len}{max_len-min_len}
$$

답이 맞은 경우에, 짧은 답을 선호하도록, 답이 틀린 경우에 길이가 긴 답에 확실히 penalty를 주도록 설계되어 있다. weight 가 곱해져 기존 reward에 더해진다. 이를 사용하면 training이 느려지기 때문에 weight를 천천히 증가시켜야 한다.