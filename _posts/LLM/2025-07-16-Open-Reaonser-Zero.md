---
title: "[논문리뷰 ]Open-Reasoner-Zero:An Open Source Approach to Scaling Up Reinforcement Learning on the Base Model"
date: 2025-07-16
last_modified_at: 2025-07-16
categories:
  - 논문리뷰
tags:
  - Reinforcement Learning
  - Reasoning
  - LLM
excerpt: "Open-Reasoner-Zero"
use_math: True
classes: wide
---
> arXiv 2025. [[Paper](https://arxiv.org/abs/2503.24290)] [[Code](https://github.com/Open-Reasoner-Zero/Open-Reasoner-Zero)]
> 5 Jul 2025

Open-Reasoner-Zero는 DeepSeek-R1-zero와 유사하게 base model에서 RL 만을 이용해서 학습한 reasoning 모델이다. DeepSeek-R1-Zero 와 다르게 source code 까지 open 되어 있다. DeepSeek-R1-Zero 와 달리 GRPO 가 아닌 PPO를 사용했다. 각 token의 advantage를 계산할 때에는 GAE 를 사용했다. 

$$\hat{A}_t^{GAE(\gamma,\lambda)}=\sum_{k=0}^{T-t-1}(\gamma\lambda)^k\delta_{t+k}, \text{ where } \delta_{t+k}=r_{t+k}+\gamma V_\phi(s_{t+k+1})-V_\phi(s_{t+k})$$

PPO policy objective:

$$\mathcal{J}_{PPO}(\theta)=\mathbb{E}_{\tau\sim\pi_{\theta_{old}}}\left[\sum_{t=0}^{T-1}min(\rho_t(\theta)\hat{A}_t,clip(\rho_t(\theta),1-\epsilon,1+\epsilon)\hat{A}_t)\right] $$

where $\rho_t(\theta)=\frac{\pi_\theta(a_t\vert s_t)}{\pi_{\theta_{old}}(a_t\vert s_t)}$

Value estimate function parameter objective:

$$\mathcal{J}_{value}(\phi)=\frac{1}{2}\mathbb{E}_{\tau\sim\pi_{\theta_{old}}}\left[\sum_{t=0}^{T-1}(V_\phi(s_t)-V_t^{target})^2\right]$$

where $V_t^{target}=\hat{A}_t^{GAE(\gamma, \lambda)}+V\_\phi(s_t)$
 
GRPO는 value network가 없는 반면 PPO는 critic을 이용해 token-value estimation을 하고 있기 때문에 advantage estimation이 더 robust하다.

GAE의 경우 parameter의 선택이 중요하다.
- $\gamma$ 의 값이 작을수록 future reward에 곱해지는 weight이 감소하기 때문에 advantage가 작아진다. 고로 $\gamma$ 값이 학습 과정에서 sequence length를 조절한다고 볼 수 있다.
- $\lambda$ 값은 advantage estimation의 bias와 variance 의 balance를 맞추는 역할을 한다. Large-scale training에서는 데이터의 양이 많기 때문에 variance가 작아지므로 bias-free configuration $\lambda=1$ 을 사용한다.

$$\hat{A}_t^{GAE(\gamma=1,\lambda=1)}=R-V_\phi(s_t)$$

$$\mathcal{J}_{value}(\phi)=\frac{1}{2}\mathbb{E}_{\tau\sim\pi_{\theta_{old}}}\left[\sum_{t=0}^{T-1}(V_\phi(s_t)-R)^2\right]$$

![](/assets/img/Open-Reasoner-Zero/algo.webp)

DeepSeek-R1-Zero와 달리 KL regularization을 사용하지 않았다. KL regularization은 policy model이 orginal base model에서 너무 멀어지는 걸 막기 때문에 exploration을 제한한다. 또, KL 관련 hyperparameter tuning을 할 필요가 없어 학습이 단순해진다. reference model, KL 계산을 위한 overhead가 절약된다. 본 논문은 KL regularization 없이 안정적인 학습을 이뤄냈다고 주장하고 있다.

DeepSeek-R1은 reward를 계산할 때 format reward 를 추가적으로 도입했지만 본 논문에 의하면 reward hacking 이 발생할 수 있으므로 reward function 의 design 을 최소화했다. Reward function은 output의 \<answer\> ~ \<answer\> 과 reference answer 사이의 binary matching을 reward로 사용했다.

![](/assets/img/Open-Reasoner-Zero/reward.webp)

Format reward 를 도입하지 않았지만 format ratio가 안정적으로 증가함을 확인할 수 있다.