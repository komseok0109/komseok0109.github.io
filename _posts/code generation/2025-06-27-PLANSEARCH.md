---
title: "[논문리뷰] Planning in Natural Language Improves LLM Search for Code Generation"
date: 2025-06-27
last_modified_at: 2025-06-27
categories:
  - 논문리뷰
tags:
  - Code Generation
  - LLM
excerpt: "PLANSEARCH"
use_math: True
classes: wide
---
> ICLR 2025. [[Paper](https://openreview.net/forum?id=48WAZhwHHw)] 
> Evan Z Wang, Federico Cassano, Catherine Wu, Yunfeng Bai, William Song, Vaskar Nath, Ziwen Han, Sean M. Hendryx, Summer Yue, Hugh Zhang
> 23 Jan 2025

## Introduction
LLM 분야에서 search를 통한 성능 개선을 이뤄낸 사례가 크게 많지 않다. Search란 inference씨 compute를 써서 성능을 향상시키는 기법들을 말한다. Code generation에서 LLM search가 잘 사용되지 못하는 이유는 LLM의 output이 다양하지 않기 때문이다. 이는 LLM들의 post-training objective가 다양한 output을 생성하는 것 보다는 정답 하나만 생성하는 것으로 유도하고 있기 때문이다. (e.g. RHLF, instruction tuning)

![](/assets/img/PlanSearch/30.webp)

Pass@1 지표는 instruction-tuned 모델이 더 좋지만 k값이 증가할수록 base 모델이 더 성능이 높은 것을 확인할 수 있다. Instruction tuning한 모델에 비해 search diversity가 더 크다고 생각할 수 있다.

다양성 부족은 search algorithm에도 좋지 않다. Greedy decoding을 사용하는 경우, 모델에서 sampling을 반복해도 다양성이 부족하니 어차피 비슷한 프로그램을 생성할 것이고, inference compute로 얻는 이익이 없다. 많은 benchmark는 single sample의 pass rate을 metric으로 사용하기 때문에 다양성 문제가 드러나기 힘들다. Single sample pass rate는 latency-sensitive하거나 compute가 부족한 상황에서는 더욱 의미있어지는 지표지만 inference compute가 충분한 상황에서는 모델의 quality를 모두 반영한다고는 보기 어렵다.

본 연구의 가설은 코드의 자연어 아이디어 단계에서 다양성을 탐색하는 것이 가장 적절하다는 것이다. 근거는 다음과 같다.
- LLM은 solution code를 backtranslation한 solution sketch가 주어져 있는 경우 정확히 코드를 생성한다.
- Sketch를 먼저 생성하고 코드를 생성하는 경우 정확도가 0% 혹은 100%로 나타난다. 이는 해당 문제를 해결할 수 있는지 여부가 sketch가 맞는지 여부에 달려있음을 의미한다.
고로, 구현 idea를 탐색하는 것이 올바른 방향이라고 결론낼 수 있다. `PLANSEARCH` 는 문제 해결을 위한 plan을 search해서 코드를 생성하는 방법론이다. Plan은 문제를 해결하기 위한 idea sketch, observation등이 포함되어 있다. 인간이 코드를 작성하기 전 문제를 관찰하고 디자인을 해보는 것과 유사하게 생각할 수 있다. Observation set을 생성하고, 해당 set의 subset을 이용하여 candidate plan을 생성한다. plan space를 탐색해서 코드를 생성한다. 이는 단순 sampling과 idea space 탐색보다 더 좋은 성능을 기록했다.

## Motivation
다른 자연어 생성 분야는 여러 개의 solution을 생성하고 그 중에 최적의 solution을 탐색해야 하지만 코딩은 test case라는 툴이 존재하기 때문에 여러 개의 solution을 생성하는 것만으로 탐색을 한다고 볼 수 있다. 고로 여러 개의 solution 중 하나를 골라야 하는 상황에서 발생하는 문제들을 고려할 필요가 없다.
- **Search Space**: Search space는 token, line, entire program이 될 수 있다. `PLANSEARCH` 는 solution sketch 혹은 plan space에서 탐색이 가장 적절하다고 가설을 세우고 있다. 즉, 풀어야할 문제의 자연어 description에서 탐색을 하는 것이다. 자연어 단계에서 reasoning을 먼저 하고 LLM을 이용하는 것의 효과는 이미 CoT 등의 연구에서 증명된 바 있다.
- **Backtranslation**: Solution sketch dataset이 없기 때문에 각 task마다 LLM을 1000번 돌려서 코드를 생성하고 test case를 통과하는 코드를 생성하지 못한 task는 필터링한다. 이후, LLM에게 성공적으로 생성된 코드와 task를 주고 코드 solution을 자연어 표현으로 변환하라고 프롬프팅한다. 아래의 왼쪽 그래프를 보면 translation이 주어졌을 때 성능이 증가했고 또 translation의 길이가 길어질 수록 성능이 증가한 것을 확인할 수 있다. Solution sketch가 주어지는 경우 correct solution을 생성할 수 있다는 것이 확인된 것이다. 그러므로 idea/plan space를 탐색하는 것이 타당한 접근 방식이다.

![](/assets/img/PlanSearch/res.webp)

- **Conditioning on Idea Quality**: 후속 실험으로 LLM이 sketch를 생성해서 코드를 생성하게 한다. 문제 해결 여부가 그 sketch가 맞냐 틀리냐 여부로 결정됨을 보이기 위해서  **특정 sketch가 주어졌을 때, solve rate의 분포 (conditioned), 전체 solve rate의 분포** 를 비교한다. 만약 conditioning한 분포가 0 혹은 1로 치우치는 현상이 보인다면 sketch가 옳을 때는 test를 거의 통과한다는 것이고 sketch가 틀릴 때는 거의 통과하지 못하는 것이므로 sketch가 옳은지 여부가 문제 해결 여부를 결정한다는 가설을 확인할 수 있다. 위의 그래프 중 오른쪽에서 {0,1} 로 쏠리는 것을 확인할 수 있다.

결론적으로, solution sketch를 생성하고 탐색하는 것이 올바른 방향이라는 가설을 설명 가능하다.

## Methods
![](/assets/img/PlanSearch/plan.webp)

**`Repeated Sampling`**: Baseline. Few-shot (problem-solution pairs) prompting을 이용해 코드를 생성하고 test를 통과하는 코드가 생성되거나 max attempt 시도 횟수만큼 시도할 때까지 반복적으로 sampling한다.

**`IDEASERACH`**: LLM에게 해결해야 할 문제 $P$ 를 주고 자연어 solution $S$ 를 생성하게 한다. 이후, $P$ 와 $S$ 를 주고 코드를 생성하게 한다.

### `PLANSEARCH`
LLM에게 해결해야할 문제 $P$ 를 주고 first-order observations $O_i^1,i\in\{1,\dots,n_1\}$ 을 생성하게 한다. Observation 집합 $s^1=\\{O_1^1,\dots,O^1_{n_1}\\}$ 의 최대 크기가 $S=2$ 인 부분집합들을 생성한다.

$$C_i^1,\quad i\in\{1,\dots,l_1\},\text{ where } l_1=1+n_1+\binom{n_1}{2} $$ 

위에서 생성한 observation 집합은 Root node가 $P$, $C_i^1$ 가 $P$ 의 child인 depth 1짜리 tree로 생각할 수 있다. 이후 $P$, $C_i^1$ 를 LLM에게 주고 second-order observation의 집합: $s_i^2=\\{O^2\_{i,1},\dots O^2\_{i,n_{i,2}}\\}$ 를 생성한다. 이후, 각 집합을 이용해서 최대 크기가 2인 부분집합 $C_{i,j}^2\text{ }\forall i\in\{1,\dots,l_1\}$ 를 생성한다. 결론적으로 depth가 2인 tree가 생성되었다. Observation의 correctness는 검증하지 않고 실제로 많이 틀리지만 다양성을 위해 그대로 이용한다.

이후, 각 leaf node마다 observation 집합을 가지고 있기 때문에 해당 집합 내의 모든 element를 LLM에게 $P$ 와 함께 프롬프팅한다. LLM이 해야 할 일은 observation을 바탕으로 $P$ 를 해결할 수 있는 자연어 solution 하나를 생성하고 해당 solution이 틀렸다고 가정하고 비판/피드백을 작성해서 두 개의 solution을 생성하는 것이다. Observation 기반 solution 외에 하나를 더 만들었기에 diversity가 증가한다. 생성된 자연어 solution은 pseudocode로 변환되고 이후 코드로 변한된다. Translation error를 방지하기 위해 두 단계 과정을 거친다. 

## Experiments
![](/assets/img/PlanSearch/res0.webp)
LiveCodeBench 에서 성능이 개선되었다.
![](/assets/img/PlanSearch/res2.webp)
IS는 `IDEASERACH`, PS는 `PLANSEARCH`를 의미한다. Pass@200 성능이 증가되었다.
![](/assets/img/PlanSearch/res3.webp)
public test filtering을 거친 plot이다. public test filtering이란 생성된 코드 pool에서 public test를 통과한 코드만 metric을 계산할 때 이용하는 것이다. Low quality candidate를 제거하고 metric을 계산하니 pass@k 곡선 자체가 왼쪽으로 이동, 즉 전반적인 값이 증가한다.

## Analysis
`PLANSEARCH` 가 기존의 sampling 보다 성능이 높았다. 또, Chain of Thought prompting 방식과 비교해도 성능이 더 높게 기록되었다.

$k=1$ 일 때 성능이 떨어지고 다른 method들보다도 성능이 떨어지는데 이는 직관적으로 다양성이 증가했으니 특정 idea가 생성될 확률이 감소하는 동시에 pool에 correct idea가 최소 하나 들어 있을 확률이 증가했기 때문이다. 정확한 idea가 들어있을 확률은 크지만 그걸 딱 찍을 확률이 감소한다. 당연히 attempt가 작을 수록 그 확률은 적다. attempt가 늘어날수록 그 많음 attempt 중에 한 번은 찍을 수 있을 것이다. 

결론적으로 충분한 inference compute가 주어진다면 `PLANSEARCH`가 다른 method를 능가한다.

Diversity가 증가할수록  search performance가 얼마나 증가하는지 pass@1과 pass@200 사이의 relative gain을 이용해 분석해본다.

![](/assets/img/PlanSearch/res4.webp)

코드 집합 $\\{c_1,\dots, c_n\\}$이 주어졌을 때 diversity는 다음 공식을 이용해 계산된다.

$$ D=1-\frac{\sum_{i<j}S(c_i,c_j)}{\binom{n}{2}} $$

$S(c_i,c_j)$는 만약 두 코드가 유사하면 $1$ 아니면 $0$ 의 값을 가진다. idea space 상에서 $\epsilon$ 보다 덜차이가 나면 유사한 것으로 판단한다. Diversity가 클 수록 attempt가 늘어날 때 성능이 크게 개선됨을 확인할 수 있다.

결론적으로, idea space에서 다양성이 증가할수록 inference 연산을 하는 것의 효율성이 증가한다. 즉 attempt가 많아질수록 성능이 개선되는 정도가 다양성과 비례한다. 