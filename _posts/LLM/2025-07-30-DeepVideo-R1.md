---
title: "[논문리뷰] DeepVideo-R1: Video Reinforcement Fine-Tuning via Difficulty-aware Regressive GRPO"
date: 2025-07-30
last_modified_at: 2025-07-30
categories:
  - 논문리뷰
tags:
  - Reinforcement Learning
  - Reasoning
  - LLM
  - Video
excerpt: "DeepVideo-R1"
use_math: True
classes: wide
---
> arXiv 2025. [[Paper](https://arxiv.org/abs/2506.07464v2)] 
> 12 Jun 2025

# Problems related to GRPO
- Reliance on safeguards: 기존의 grpo 는 모델의 parameter가 너무 심하게 바뀌는 것을 막기 위해 $\min$, clip 을 사용한다. 하지만 clip 과 $\min$ 을 사용하기 때문에 policy 모델과 학습 이전의 모델이 너무 차이나면 importance ratio 값이 커지기 때문에 loss 자체가 flat 한 형태가 된다. 그럼 gradient 가 0 이 되는 문제가 발생한다.
- Vanishing Advantage Problem: GRPO 에서는 advantage 를 loss 에 이용하고, advantage 는 group 내에서 normalized reward 로 계산된다. 이때 특정 prompt 를 입력으로 생성된 response 들이 서로 너무 비슷해서 reward값이 동일하여 advantage 도 0이 되어 loss에 기여를 하지 못해 학습에 아무 도움이 되지 않는 상황을 의미한다.

# Reg-GRPO
위에서 서술한 문제들을 해결하기 위해 regression 기반 GRPO를 본 논문에서는 제시하고 있다. Reg-GRPO loss는 다음과 같다.

$$
\mathcal{}_{reg-grpo}=\mathbb{E}_{\mathbf{x}\sim P(X)}\left[\frac{1}{G}\sum_{i=1}^G\left(\hat{A}^{(i)}-\epsilon\cdot\frac{\log \rho(\mathbf{x,y}^{(i)})-\mu_\rho}{\sigma_\rho}\right)^2\right]
$$

$$
\rho(\mathbf{x,y}^{(i)})=\frac{\pi_\theta(\mathbf{y\vert x})}{\pi_{\theta_{old}}(\mathbf{(y\vert x)})} \text{ and } \mu_\rho,\quad\sigma_\rho \text{ are mean and standard deviation of } \log \rho(\mathbf{x,y}^{(i)}) 
$$

# Difficulty-aware Data Augmentation
Vanishing advantage problem 의 경우 prompt 가 너무 쉽거나 너무 어려운 경우 발생한다. 본 연구는 training prompt의 난이도를 조절해서 variance 를 증가시키는 것을 목표로 한다. 기준을 잡기 위해 Prompt 의 current reward average $r_{cur}=\frac{1}{G}\sum_{i=1}^G\mathcal{R}(\mathbf{x,y}^{(i)})$ 를 계산한 뒤 reference reward $r_{ref}:=\text{moving average of reward over the past } W { training steps} $ 보다 작으면 `easy`, 크면 `difficult` 로 정의한다. Easy의 경우 perturbation level 을 증가해 task 를 더 어렵게 만든다. Difficult 의 경우 guidance를 도입해 task를 더 쉽게 만든다. 이를 통해 input data가 너무 쉽거나 너무 어려운 것을 방지해서 vanishing advantage problem 이 일어나지 않게 하는 것이 목표이다.

## Difficulty-decreasing augmentation
Difficult의 경우 ground-truth answer + multiple reasoning path 를 prompt에 넣어서 guidance를 제공한다. 이때 얼마나 sample data를 prompt 에 넣어줄지는 $l_{guide}=\text{round}(\vert r_{cur}-r_{ref}\vert)+1$ 값을 이용해 조절한다.

## Difficulty-increasing augmentation
Easy의 경우 video input 에 frame level 로 gaussian noise 를 이용해 input 을 더 어렵게 만든다. 

$$
\text{Input Video}+= \tau\cdot l_{perturb}, \text{ where }\tau\sim\mathcal{N}(0,1) \text{ and } l_{perturb}=\vert r_{cur}-r_{ref}\vert+1
$$