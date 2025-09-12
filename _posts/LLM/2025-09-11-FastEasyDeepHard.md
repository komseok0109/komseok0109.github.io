---
title: "[논문리뷰] Fast on the Easy, Deep on the Hard: Efficient Reasoning via Powered
 Length Penalty"
date: 2025-09-11
last_modified_at: 2025-09-11
categories:
  - 논문리뷰
tags:
  - Reinforcement Learning
  - Reasoning
  - LLM
  - Efficiency
excerpt: "Fast on Easy, Deep on Hard"
use_math: True
classes: wide
---
> arXiv 2025. [[Paper](https://arxiv.org/abs/2506.10446)] 
> 12 Jun 2025

![](/assets/img/EffReason/fedh.webp)

# Method
- LLM: $\pi_\theta$
- Given input $x$, model generate a response $y\sim \pi_\theta(\cdot\vert x)$

$$
accuracy=\begin{cases}
  1 & \text{if } y=y* \\
  0, & \text{otherwise}
\end{cases}
$$

- Note that intermeidate reasoning steps do not contribute to accuracy.

REINFORCE 알고리즘은 기존의 PPO 와 달리 critic 을 사용하지 않아 memory overhead 가 적다. 본 논문에서는 math 를 training data 로 사용하고 있기 때문에 위에서 정의한 accuracy 를 그대로 reward로 사용할 수 있다. 고로 reward 모델도 사용하지 않는다. REINFORCE 알고리즘의 gradient는 다음과 같다:

$$
\mathbb{E}_{x\sim \mathcal{D}, y\sim\pi_\theta (\cdot\vert x)}[R(y,z)\nabla_\theta\log\pi_\theta(y\vert x)]
$$

잘 알려진대로, bias 를 줄이기 위해 RLOO (REINFORCE Leave-One-Out (RLOO)) 를 이용한다. k 개의 sample 을 생성한뒤 아래의 공식을 이용해 계산한다. 각 sample에 대해 나머지 k-1 sample 들의 return의 평균값을 빼준 뒤 그 값의 평균을 취한다.

$$
\frac{1}{k}\sum_{i=1}^k[R(y^{(i)},x)-\frac{1}{k-1}\sum_{j\neq i}R(y^{(i)},x)]\nabla \log\pi(y^{(i)}\vert x)
$$

Training 시에는 최대 길이 제한을 두어 그것보다 길게 생성하면 자른다. 그럼 최종 답이 생성되지 않을 것이고, 너무 길게 생성된 친구들은 틀린 것으로 간주될 것이다. 또, prompt에 "Please reason step by step, and put your final answer within boxed." 라는 instruction 을 통해 reasoning 한 이후에 답을 생성하도록 지시한다. reward 는 다음과 같이 계산한다.

$$
R(y^{(i)},x)=\begin{cases}
  f(len(y^{(i)})), & \text{if } y=y* \\
  0, & \text{otherwise}
\end{cases}
$$

단순히 accuracy 를 reward 로 사용하면 efficient reasoning 을 위한 학습을 할 수 없으니 length penalty 를 이용한다:

$$
f(\text{len}(y^{(i)}))=1+\frac{\alpha}{\text{len}(y^{(i)})^\gamma}\qquad\text{where }\gamma>0,\alpha\geq 0
$$

즉, 같은 정답이라고 해도 길이가 길수록 낮은 reward 를 받게 된다. 쉬운 문제일 수록 정답을 맞추기는 쉽기 때문에 response를 짧게 생성하도록 모델이 학습될 것이고 반대로 어려운 문제일수록 길이를 짧게 하면 답을 맞추지 못해서 reward를 0으로 받을 것이기 때문에 길이가 좀 길어져도 정답을 더 맞추는 방향으로 학습이 될 것이다. 즉 문제 난이도에 따라 정답을 맞추는데 필요한 적절한 reasoning 길이를 생성하도록 학습이 되는 것이다. 기존 연구와 달리 normalization 없이 길이값을 직접적으로 사용했다.

# Advantage Function
RLOO 에서 k-1 개의 sample 들의 reward 의 평균값을 빼는 과정은 이들을 baseline으로 보는 것으로 해석할 수 있다. 각 sample 의 reward 에서 baseline 의 평균을 빼는 과정을 통해 이 sample 이 다른 sample 보다 얼마나 더 나은지를 나타내는 advantage 값이 되는 것이다. 위에서 언급한대로 지금의 reward 함수는 어려운 질문일수록 모델이 생성할 수 있는 길이를 더 허용하는 형태이다. 이전 연구에서는 normalization 을 사용했는데 이는 값의 scale 자체가 줄어들기 때문에 모델 output 의 길이가 폭넓게 분포되지 않은 이상 길이가 길지만 의미있는 output을 제대로 구분해내기 힘들다. 복잡한 문제를 푸는데 도움이 되는데도 불구하고 그런 sample을 학습에 반영할 수 없다. 

예를 들어, $\gamma=\frac{1}{2}$ 로 두고, 모델 output 의 길이가 uniform distribution $\mathcal{U}(a,b)$ 를 따른다고 하자. 그럼 penalty $Z=1+\frac{1}{\sqrt{len(y)}}$ 의 variancesms 다음과 같다.

$$
Var(Z)=\frac{\ln b - \ln a}{b-a}-\frac{4}{(\sqrt{a}+\sqrt{b})^2}
$$

a 와 b 가 증가할 수록 variance는 감소한다. 즉, 어려운 문제에 대해서는 길이가 길어지고 거기서는 penalty를 길이별로 주는 것보다 정답을 맞추는 것이 더 중요해진다. 이럴 때는 reward의 variance를 크게 두지 않는다. 대신 길이가 짧은 쉬운 문제에 대해서는 penalty를 길이별로 크게 두어서 더 짧은 답을 생성하도록 유도하게 되는 것이다. 하지만 normalization 을 하면 정의상 variance가 1이 되고 문제의 난이도, 요구되는 길이의 분포와 관계없이 penalty 값이 비슷해지기 때문에 필요할 때 길게 reasoning을 하는 행동을 모델이 하도록 유도할 수 없게 된다.

![](/assets/img/EffReason/fedh2.webp)

