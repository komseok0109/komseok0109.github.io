---
title: "[논문리뷰] Planning in Natural Language Improves LLM Search for Code Generation"
date: 2025-06-25
last_modified_at: 2025-06-25
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
먼저, 본 연구에서 inference동안 연산을 통해 성능을 높이는 것을 search라고 한다. 연구의 가설은 search의 bottleneck이 모델 output의 다양성이 높지 않다는 것이다. 대부분의 모델이 다양한 output을 생성하는 것보다 하나의 정확하고 선호되는 정답을 생성하는데 집중하기 때문이다. output의 다양성이 적으면 모델은 inference 연산을 늘리는 것에서 큰 수익을 얻지 못했다.