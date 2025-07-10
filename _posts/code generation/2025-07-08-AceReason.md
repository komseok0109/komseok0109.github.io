---
title: "[논문리뷰] Learning to Generate Unit Tests for Automated Debugging"
date: 2025-07-08
last_modified_at: 2025-07-08
categories:
  - 논문리뷰
tags:
  - Unit Test
  - Code Generation
  - LLM
excerpt: "UTGen"
use_math: True
classes: wide
---
> arXiv 2025 [[Paper](https://arxiv.org/abs/2505.01619)] [[Page](https://github.com/archiki/UTGenDebug)]
>  Archiki Prasad, Elias Stengel-Eskin, Zaid Khan, Justin Chih-Yao Chen, Mohit Bansal

## Introduction
Unit test 를 inference time에 생성해서 feedback으로 활용하기 위해서는 두 가지가 만족되어야 한다.
- Unit test 의 input 이 error를 trigger 하는 코드여야 한다. 즉, 너무 자명한 unit test는 아무 의미가 없다.
- Unit test 의 output 이 input 가 problem 에 맞아야 한다. 기존 연구는 reference solution 을 이용해 output 을 생성했지만 이는 자동화로 나아가는 방향이 아니고, reference solution 이 없는 일반적인 user 의 input가 맞지 않다.

이를 해결하기 위해서 unit test generator는 다음 두 가지 특성을 지녀야 한다.
- high attack rate: given a faulty code, UT generator should generate inputs likely to trigger erros
- high output accuracy: UT output should be consistent with the task description 
