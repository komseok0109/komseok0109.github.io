---
title: "[논문리뷰] BigCodeBench: Benchmarking Code Generation with Diverse Function Calls and Complex Instructions"
date: 2025-06-26
last_modified_at: 2025-06-26
categories:
  - 논문리뷰
tags:
  - Code Generation
  - LLM
excerpt: "`BigCodeBench`"
use_math: True
classes: wide
---
> ICLR 2025. [[Paper](https://openreview.net/forum?id=YrycTjllL0)] [[Code](https://github.com/bigcode-project/bigcodebench)] 
> Terry Yue Zhuo, Vu Minh Chien, Jenny Chim, Han Hu, Wenhao Yu, Ratnadira Widyasari, Imam Nur Bani Yusuf, Haolan Zhan, Junda He, Indraneil Paul, Simon Brunner, Chen GONG, James Hoang, Armel Randy Zebaze, Xiaoheng Hong, Wen-Ding Li, Jean Kaddour, Ming Xu, Zhihan Zhang, Prateek Yadav
> 23 Jan 2025

## Introduction
MBPP, HumanEval 등의 code generation benchmark들은 대부분 짧고, 알고리즘 중심이며, 독립적인 task만 포함하고 있다. 하지만, 실제 real-world task는 두 가지 특징을 가지고 있다.
- 다양한 함수 호출 sequence가 요구된다. 똑같은 기능을 새로 만들지 않고 도메인 특화 라이브러리 API를 이용한다.
- Instruction이 복잡하다. 구현하고자 하는 functionality의 복잡한 구조와 순서를 요소 별로 설명하는 instruction은 기존 benchmark에 비해 복잡해야 한다.
![eg](/assets/img/BigCodeBench/eg.webp)
예를 들어 HTTP GET request를 생성하는 함수의 경우, SSL context 관리, response, socket connection 등의 여러 요소를 다양한 함수 호출을 통해 하나의 함수로 통합해서 구현할 수 있어야 한다.

Real-world task를 반영할 수 있는 benchmark를 만드는 것은 다음의 이유들로 쉽지 않다.
- Instruction이 복잡하면서 독립적인 기능을 하는 코드 data를 구할 소스가 없다. Github Repo에는 real-world 코드가 매우 많지만 cross-file로 구현되어 있는 경우가 대부분이다.
- Real-world task는 범위가 매우 넓다
- 기존 benchmark의 speicification은 애매하거나 구체적이지 않은 경우가 많다.
- LLM으로 data를 수정해서 사용하는 경우 bias와 reliability 문제가 존재한다.

`BigCodeBench`는 나열된 문제를 해결하기 위해 아래의 framework를 통해 생성한 새로운 benchmark이다. 
![frame](/assets//img/BigCodeBench/frame.webp)
LLM을 이용해 사람의 지도 아래 programming task를 추출하고, refactor한 후, test case를 추가한다. `BigCodeBench`는 1140개의 task (723개의 함수/139개의 라이브러리/7개의 domain) 으로 구성된다. 각 task마다 unit test case를 가지고 있다

- `BigCodeBench-Complete`: docstring이 주어졌을 때 LLM이 코드를 생성할 수 있는지 평가한다.
- `BigCodeBench-Instruct`: 세부사항 보다는 자연어 instruction이 주어졌을 때 LLM이 코드를 생성할 수 있는지 평가한다.

## Benchmark Construction
`BigCodeBench-Complete`는 Data Synthesis, Semi-automatic Program Refactoring, Testing Case Generation 을 거쳐 생성된다.`BigCodeBench-Instruct`는 자연어 instruction 용 benchmark이다. `BigCodeBench-Complete`의 각 data는 PEP-257-structured docstring으로 작성된 instruction으로, 여러 개의 라이브러리를 사용해야 하고 최소 5개의 test case를 가지고 있다. 각 test case는 단순한 input-output assertion 형태가 아니라 복잡한 형태로 program behavior를 검증할 수 있게 구성되어 있다.
### Data Synthesis
Repo에서 data를 구하는 것이 가장 쉬운 방법이지만 cross-file로 구현되어 있는 경우가 많다. 대신, 사람의 지도 아래 LLM을 이용하는 방법을 택했다. 짧은 instruction과 API호출 예시를 프롬프팅해서 LLM이 알맞은 코드를 생성하게 했다. 프롬프팅시 two-shot demonstration을 포함시켰다. GPT-4를 사용했다.

LLM은 자기가 생성한 코드랑 비슷한 코드를 잘 맞추는 경향성이 있다. 이를 해결하기 위해 다음과 같은 후처리를 거쳤다.
- 함수 이름을 dummy로 바꿨다.
- docstring의 경우 back-translation을 이용해 GPT-4에 편향되지 않도록 재작성했다.
후처리를 거친 후 AST parser로 타당성을 검증해서 4718개의 프로그래밍 sample을 수집했다.

### Semi-Automatic Program Refactoring & Test Case Generation 
LLM으로 코드를 생성했기 때문에 undeclared variable, runtime bug 등의 문제가 있을 수 있다. 그러므로 ground-truth solution으로 바로 활용하기 어렵다. 그러므로 testing을 통해 생성한 코드의 검증이 필요하다. 하지만 LLM이 생성한 코드를 일일이 이해하고 testing을 위해 refactoring하는 것은 많은 노력이 필요하다. 대신에, GPT-4의 Code Interpreter를 이용해 검증을 진행했다.
- Human Aspect: 13명의 annotator들이 자기가 선호하는 data type (e.g. SQL, built-in, CSV) 과 task scenario (DA, network, visualization) 에 맞는 코드들을 할당받는다. 분류 과정은 GPT-4 API를 이용했다. 각 annotator는 GPT-4를 이용해 할당된 코드를 실행하고 버그가 발생하거나 testing을 통과하지 못하면 반복적으로 refinement하는 방식을 사용한다.
- LLM Aspect: LLM은 다음을 포함한 프롬프트를 받게 된다.
  - 사용하지 않은 라이브러리는 제거하고 필요한 라이브러리 추가
  - PEP-257 convention에 맞게 docstring 재작성
  - docstring의 instruction과 맞아떨어지는 구현 작성
  - test case를 작성하고 실행
Code Interpreter도 mocking test를 작성하지 못한다거나 bug가 잘 해결되지 않는 경우 session time out이 발생할 때까지 계속 수정을 반복하기 때문에 사람이 지켜보면서 feedback을 해주어야 한다. 위 과정을 거친 후 test case가 잘 작성되지 않은 경우를 제외하니 1223개의 task가 생성되었다.

### Human Curation
**Examination**: 사람이 직접 가이드라인을 따라 test case를 추가하고 runtime issue를 해결한다. 또 아래 규칙을 따르는지 확인한다.
- Task scope에 맞는 라이브러리 최소 2개 이용
- 구현에서 사용하는 것만 `import`
- PEP-257 convetion docstring
- Docstring과 구현, test case가 맞아떨어지는지 확인
- Docstring에 적힌 라이브러리가 `import` 되어있는지 확인
- Test case과 `unittest` framework로 encapsulate 되어있는지 확인
- Test case가 deterministic한지 확인
**Pre-Evaluation**: GPT-3.5-turbo를 이용해 task가 잘 작성되었는지 확인한다. 만약 코드를 잘 생성하는데 실패한 경우 docstring을 더 명확하게 수정한다.
**Cross-Checking**: 위 과정에 관여하지 않은 추가 인원이 cross-checking한다. 검증보다는 utility 위주로 refactor한다. 각 annotator들은 docstring이 task description, function paramter, expected return, exception handling, required module, example들을 포함하는지 확인하고 수정한다. 사용하지 않은 imported moudle도 제거한다. 마지막으로 github container registry를 활용해 구현을 검증한 뒤, annotator들이 몇 개를 골라서 직접 코드를 작성해서 benchmark 구성을 완료한다.

### Benchmarking NL-Oriented Instructions to Code Generatinos
사용자와 mutli-turn dialogue를 통해 코드를 생성하는 경우 자연어 기반 instruction을 입력받아 코드를 생성해야 한다. 사용자는 일반적으로 너무 구체적인 디테일보단 자연어 기반 high-level instruction을 LLM에게 제시할 가능성이 높다. `BigCodeBench-Instruct`는 위에서 구성한 `BigCodeBench-Instruct`에서 prompt를 parsing rule을 이용해 자연어 기반으로 변경한다.
![inst](/assets//img/BigCodeBench/inst.webp)

## Benchmark Statistics
![inst](/assets//img/BigCodeBench/domain.webp)
![inst](/assets//img/BigCodeBench/stat.webp)
Cov: branch coverage, Char: characters, C.C.: complexity Lib: Library Dom.: domain Std standard library Ext.: External Library

위 table에서 알 수 있듯이 library 사용 개수가 가장 많다. 또, 하나의 함수를 작성할 때 여러 개의 library를 사용한다. (2.6/4.7) Combination 개수도 월등히 많다.
![comp](/assets/img/BigCodeBench/comp.webp)
BigCodeBench는 tool개수, complexity가 높아 LLM에게 복잡한 reasoning 능력을 요구할 수 있는 benchmark이다.

## Task-level performance
![res](/assets/img/BigCodeBench/res.webp)
- LLM이 input 길이가 길어질 때 응답에서 import statement와 같은 중요한 디테일을 생략하는 현상이 발생하고 이로 인해 task failure가 발생한다. 이를 model laziness라고 하는데 import statement가 빠진 경우 추가해서 calibrated score를 계산해보았더니 GPT에서 laziness증상이 발견되었고 이는 OpenAI도 확인하고 있는 현상이다. Performance degradation이 프롬프트의 평균 길이가 더 긴 `BigCodeBench-Complete`에서 더 큰데 이는 input길이가 길수록 laziness가 길어짐을 증명한다.
- Instruction-tuned LLM과 그렇지 않은 LLM을 비교했을 때 instruction-tuned LLM이 성능이 더 좋았고 이는 프롬프트의 복잡한 constraint들을 instruction tuning을 했을 때 더 잘 이해했음을 의미한다.
- 순위 분포는 비슷하면서 평균적인 성능지표가 `BigCodeBench-Instruct`에서 더 이는 instruct prompt가 아무래도 verbosity가 낮기 때문에 모호성이 더 크기 때문으로 예상된다. 
  
성능 지표에서 알 수 있듯이 가장 높은 LLM의 60%의 성능을 기록했고 인간은 97% 정도 되기 때문에 LLM이 사람만큼 복잡한 instruction과 function call이 많이 필요한 프로그램 작성은 개선이 필요하다.

## Tool-level performance
![res](/assets/img/BigCodeBench/res2.webp)
Training data의 domain분포가 다르기 때문에 각 모델이 각 domain을 얼마나 잘하는지도 분포가 형성되는 것을 확인할 수 있다.
![res](/assets/img/BigCodeBench/res3.webp)
pass한 task의 20%가 GT 라이브러리를 사용하지 않았지만 추가적인 라이브러리를 사용해서 통과했다. 이때 대개 standard library를 사용했다. Function call의 경우 ground truth와 다른 function을 많이 호출한 걸 확인 할 수 있다. 하지만 fail의 비율에서 알 수 있듯이 비교하자면 GT와 동일한 함수를 사용했을 때 더 성공할 가능성이 높다.