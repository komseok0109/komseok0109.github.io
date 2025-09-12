---
title: "[논문리뷰] Training Language Models to Reason Efficiently"
date: 2025-09-11
last_modified_at: 2025-09-11
categories:
  - 논문리뷰
tags:
  - Reinforcement Learning
  - Reasoning
  - LLM
  - Efficiency
excerpt: "Normalized Length Penalty"
use_math: True
classes: wide
---
> arXiv 2025. [[Paper](https://arxiv.org/abs/2502.04463)] 
> 19 May 2025

![](/assets/img/EffReason/fedh.webp)

# Method
- LLM: $p$
- Given prompt $x$, $p$ produces a response $y=(y^1,y^2,\dots,y^t)$, where $y^i$ represents i-th token.
- Autoregressive: $y^{k+1}\sim p(\cdot\vert x,y^{\leq k})$, where $y^{\leq k}=(y^1,y^2,\dots,y^k)$. This generation stops when LLM outputs the EOS token.
- CoT: LLM is said to produce a “chain of thought” when it produces intermediate tokens that are not part of the output before generating the final answer in an autoregressive way.
- Verifier/Reward model: Given problem and response, we can calculate the score via reward model or verifier => $f(x,y)=1\{y=y^\star(x)\}$ where $y^\star$ is ground truth.
- LRMs are trained to maximize the following objective function: $\text{ACCURACY}(p)=\mathbb{E}_{x\sim\rho}\mathbb{E}_{y\sim p(x)}[f(x,y)]$
  
본 연구의 목적은 모델이 위의 objective function 을 maximize 하는 동시에 생성하는 token 수를 효율적으로 낮추는 것이다. 효율적이라는 것의 의미는 쉬운 문제일수록 적은 token 수를 어려운 문제일수록 그 문제 풀이에 맞게 적절하게 긴 token 수를 사용하는 것을 얘기한다. 이를 위해 objective function 을 아래와 같이 변경시킨다.

$$
\mathbb{E}[f(x,y)(1-\alpha f(\text{LEN}(y)))]\qquad\text{where $\alpha\in[0,1)$ is a tunable paramter.} 
$$

위의 objective function 은 정답이 맞은 경우, y의 길이가 짧으면 짧을 수록 큰 값을 가지게 된다. 즉 길이가 길면 penalty 를 주는 것이다. 이를 통해 모델이 최소한의 token 만 뱉고 정답을 생성하도록 유도할 수 있다. $\alpha$ 값이 크면 클수록 regurlization 을 크게 주게 된다. Penalty 는 아래와 같이 계산한다.

$$
f(\text{LEN}(y))=\sigma\left(\frac{\text{LEN}(y)-\text{MEAN}(x)}{\text{STD}(x)}\right)
$$

MEAN(x), STD(x) 는 prompt x 를 입력으로 생성한 response 들 중에 정답을 맞춘 response 의 길이의 평균, 표준편차이다. 즉, per-prompt normalization 을 사용해 penalty 를 계산한다. sigmoid 함수를 사용해 값을 0 과 1 사이로 맞추었다. 또, 당연히 길이가 길어도 정답을 맞춘게 정답을 못 맞춘거보다 더 높은 reward 를 받게 설계되었다. 본 논문에서는 optimization 으로 RLOO + PPO 를 사용했다: 

$$
\mathcal{A}(y_i,x)=\mathcal{R}(y_i,x)-\frac{1}{n-1}\sum_{j\neq i}\mathcal{R}(y_j,x)
$$

sequence (response) level advantage 를 사용한다. loss 는 PPO 를 사용했다:

$$
\min \{f^t_\theta(y,x)\mathcal{A}(y,x),\text{clip}_{1-\epsilon}^{1+\epsilon}[f^t_\theta(y,x)]\mathcal{A}(y,x)\}
$$

$f^t_\theta(y,x)$ 는 importance ratio 이다.

# Proof
We can consider language model $p_\theta$ conditioned on a prompt $x$ as a multinomial distribution over $N$ responses $y_1, \dots, y_N$. That means, given $\vert\mathcal{X}\vert$ minomial distributions $p(\cdot\vert x)$, there exists a parameter $\theta$ that realizes such a choice. Formally, for every choice of $p$ s.t.

$$
p(y_i\vert x)\in [0,1], \forall x \in\mathcal{X},i\in[N]
$$

$$
\sum_i p(y_i\vert x ) = 1,\forall x \in\mathcal{X}
$$

there exists a $\theta$ such that

$$
p_\theta(y_i\vert x)=p(y_i\vert x),\forall i\in[N],\forall x \in\mathcal{X}
$$

This assumption can be justified by the expressive power of the neural network.

We consider another assumption: For every prompt, there exists at least a correct response that the LLM can output for an appropriate value of $\theta$. Formally, for all prompts $x\in\mathcal{X}$, $\exists y\in\{y_i\}^N_{i=1}$ such that $y=y^\star(x)$.

Let $p_{\theta^\star}$ denote the reasoning model that is the population level maximizer of the accuracy. That is, $\theta$ maximizes the expectation of the accuracy. This reasoning model can cover the correct solution for each of the prompts. Now, let $\theta^\star_{eff}$ denote the parameter that maximizes our objective function. (Length regurlarized) We can prove that $\theta^\star_{eff}$ is as accurate as $\theta^\star$. Furthermore, under the above assumptions listed, $\forall x \in \mathcal{X}$, $\forall y'$ s.t. $y'=y^\star(x)$, 

$$
\mathbb{E}_{y\sim p_{$\theta^\star_{eff}$}(x)[LEN(y)]}\leq LEN(y')
$$

Thus, training objective yields the Shortest Correct Solution

# Limitation
$\alpha$ 값을 통해 전체 길이를 조절은 가능하지만 application 마다 그 정도를 조절할 수 가 없다. 즉 precise 하게 response 마다 조정할 수 없다는 믜이다.