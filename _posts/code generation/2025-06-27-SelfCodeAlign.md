---
title: "[논문리뷰] SelfCodeAlign: Self-Alignment for Code Generation"
date: 2025-06-27
last_modified_at: 2025-06-27
categories:
  - 논문리뷰
tags:
  - Code Generation
  - LLM
excerpt: "SelfCodeAlign"
use_math: True
classes: wide
---
> NeurIPS 2024. [[Paper](https://openreview.net/forum?id=HrtjdYHep6)] [[Page](https://github.com/bigcode-project/selfcodealign)]
> Yuxiang Wei, Federico Cassano, Jiawei Liu, Yifeng Ding, Naman Jain, Zachary Mueller, Harm de Vries, Leandro von Werra, Arjun Guha, Lingming Zhang
> 01 Jan 2024

## Introduction
Instruction tuning이란 instruction-output pair dataset에 LLM을 fine-tuning해서 모델을 개선하는 것을 말한다. Instruction tuning을 위한 data를 위해 human annotator를 사용할 수 있지만 cost가 크다. 다른 방법으로는 distillation을 사용할 수 있다. Stronger LLM이 생성한 output을 이용해 weaker LLM을 학습하는 방식이다. 하지만 대부분의 stronger LLLM은 closed-source라서 distillation이 불법이다. SelfCodeAlign은 스스로 생성한 isntruction data로 base code LLM을 self-align하는 pipeline이다.
- Stack V1 dataset의 seed function들에서 code concept들을 뽑아낸다.
- Base model에게 새로운 코딩 task를 생성하라고 프롬프팅한다.
- 이후, 각 task에 대해 코드와 test case pair를 여러 개 생성하라고 지시한다.
- 마지막으로, sandbox execution을 이용해 test하고 test case를 통과한 instruciton-response pair를 선택해 instruction-tuning 용 dataset을 구축한다.

## SelfCodeAlign
![](/assets/img/SelfCodeAlign/overview.webp)
- **Seed Snippets Collection** Stack V1에서 seed 코드 집합을 수집한다. Quality가 높은 코드를 다양하게 수집한다. Quality를 보장하기 위해 먼저 docstring을 가지고 있는 python 함수를 추출하고, filtering rule을 여러 개 적용시켜 수집한다. 필터링의 경우, Pyright type checker, benchmark item, duplicate 제거, poor documented code 제거 등이 적용되었다.
- **Diverse Instruction Generation**: 수집한 seed 코드 snippe에서 instruction을 다음 두 과정을 거쳐 생성한다.
    - Concepts extraction: base 모델에게 함수내에서 사용된 code concept의 list를 생성하라고 지시한다. Code concept이란 코딩에서 이용되는 기본적인 원리나 테크닉들을 의미한다. (e.g. pattern matching, data type conversion)
    - Instruction Generation: 생성한 code concept을 base 모델에게 주고 해당 code concept이 포함되어야 하는 coding task를 생성하게 한다. 이때 prompt에는 code concept 뿐만 아니라 difficulty (easy/medium/hard), category (function/class/program) 을 포함한다. difficulty와 category는 무작위로 정해진다.
- **Response Generation & Self-Validation**: Base 모델에게 위에서 생성한 instruction을 주고 코드와 test case를 생성하도록 지시한다. Teacher LLM을 사용하지 않는 self-align 방식이다. 모델은 각 instruction마다 (response,test) 를 여러 개 생성하고 sandbox environment (no external host) 에서 test 를 통과한 response만 필터링한다. 그 중 하나를 무작위로 골라 instruction tuning dataset에 추가한다. 이를 self-validation이라고 한다.

## Main Evaluation
### Funtion-level Code generation
HumanEval+ & MBPP+
![](/assets/img/SelfCodeAlign/res.webp)

LiveCodeBench
![](/assets/img/SelfCodeAlign/res1.webp)

EvoEval
![](/assets/img/SelfCodeAlign/res2.webp)

EvalPerf (The efficiency evaluation)
![](/assets/img/SelfCodeAlign/res3.webp)

### Class-level Code Generation
ClassEval
![](/assets/img/SelfCodeAlign/res4.webp)

### Data Science Programming
DS-1000
![](/assets/img/SelfCodeAlign/res5.webp)

### Code Editing
CanItEdit (Fixing bugs, adding new features, improving existing features)
![](/assets/img/SelfCodeAlign/res6.webp)

## Component Analysis
### Self-Alignment with Different Models
![](/assets/img/SelfCodeAlign/res7.webp)

다른 모델에서도 SelfAlignCode pipeline을 검증해본다. Base model은 fine-tuning되는 모델, data-generation model은 pipeline에 사용되는 모델이다. diagonal cell이 self-alignment에 해당될 것이다. 나열된 순서가 HumalEval+의 성능 순서이다. 고로 diagonal cell에서 오른쪽으로 갈수록 base model보다 성능이 조금 더 좋은 teacher model을 이용한 것이 된다. 확인할 수 있는건 teacher model가 성능이 크게 차이 나지 않는 경우 self-alignment를 사용하는 것이 좋다. 하지만 teacher model가 차이가 커지면 distillation한 것이 성능이 더 좋다.

### Effectiveness of Execution-based Filtering
![](/assets/img/SelfCodeAlign/res8.webp)

Self-validation이 효율적인지 분석한다. 4가지 조건으로 달리해서 실험을 진행한다.
- Random selection (all) : 생성된 response 중 아무거나 하나 골라서 instruction과 pair.
- Random selection (subset) : 위의 방식은 필터링한 것 대비 개수가 너무 많기 때문에 subset만 이용.
- Failures only: 실패한 response 중 하나와 pair
- Passes only: 통과한 response 중 하나와 pair

Randoming selection 한 것은 dataset 사이즈가 passes only보다 큼에도 불구하고 성능이 낮다. Failure only는 성능이 가장 낮다. Execution-filtering, code correctness의 중요성을 알 수 있다.

### Importance of Seed Selection and Concepts Generation
![](/assets/img/SelfCodeAlign/res9.webp)

Seed에서 바로 instruction 생성하는 방식, 처음에 snippet 뽑을 때 quality 따지지 않고 무작위로 뽑은 방식, SelfCodeAlign 3가지를 비교한다. Seed에서 바로 instruction 생성하는 방식이 성능이 가장 떨어진다. Instruction 생성할 때 seed함수를 주고 생성하는 방식이 모델이 접한 적이 없기 때문에 instruction이 잘 생성되지 않았을 가능성이 크다. Concept을 뽑아냄으로써 더 자연스럽고 현실적인 instruction이 생성 가능하다. Random snippet을 사용한 경우는 snippet이 다양해지지만 정확도가 떨어져서 결론적으로는 성능이 떨어진 것을 확인 가능하다.

### Comparing Self-Alignment to Distillation
![](/assets/img/SelfCodeAlign/res10.webp)

## Limitation
- 현재는 token개수 제한되어 있어 instruction 길이가 medium size에 편향되어 있다. 더 긴 instruction-response pair로 학습하면 성능 개선 가능
- negative sample은 필터링 되지만 RL loop에 이용 가능
- 생성한 test case 자체에 대해서는 검증하는 과정 없다.
