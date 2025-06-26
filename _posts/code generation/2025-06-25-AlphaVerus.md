---
title: "[논문리뷰] AlphaVerus: Bootstrapping Formally Verified Code Generation through
 Self-Improving Translation and Treefinement"
date: 2025-06-25
last_modified_at: 2025-06-25
categories:
  - 논문리뷰
tags:
  - Code Generation
  - LLM
excerpt: "AlphaVerus"
use_math: True
classes: wide
---
> ICML 2025. [[Paper](https://arxiv.org/abs/2412.06176)] [[Code](https://github.com/cmu-l3/alphaverus)] 
> Pranjal Aggarwal, Bryan Parno, Sean Welleck
> 9 Dec 2024

## Introduction
LLM은 기본적으로 아무 문장이나 생성할 수 있기 때문에 보안 취약성이나 버그를 포함한 코드를 생성할 수 있다. 오늘날의 code generation 방법들은 모든 가능한 input을 테스트하는 것이 아닌 runtime testing, human inspection등의 불완적한 평가 기준으로 correctness를 검증한다.모든 input을 커버하는 것은 불가능한 동시에 모든 걸 커버하지 않으면 unreliable한 signal을 모델이 생성할 수 있다. 사람이 일일히 검사하는 것은 당연히 scalable하지 않다. 또, 코드가 복잡하거나 길수록 옳은 코드인지 직접 검사하는 것은 매우 어렵다.

반면, verification-aware programming language (e.g. Verus) 의 경우 작성한 프로그램이 모든 input을 커버할 수 있는지 수학적으로 보장이 가능하다. 작성한 코드, specification, proof를 verifier에 입력으로 넣으면 specification을 코드가 만족하는지 검사할 수 있다. 그러므로 Verus와 같은 언어의 경우 LLM으로 생성한 코드의 신뢰성을 크게 확보할 수 있다. 대신에, proof와 formal specification을 작성해야 하고 verified 코드를 LLM이 작성하는 것을 잘하지 못한다는 점을 고려해야 한다. 이유는 training data가 부족하기 때문이다. Verification-aware language는 Danfy, F*, Verus등이 있지만 실제 mainstream에서는 거의 사용하지 않기 때문이다. Verus (a verification language for the very popular language Rust) 는 Rust용인데도 불구하고 레포가 10개 미만이다. 그러므로 training data가 부족해서 Verus 코드를 생성할 기초 모델조차 학습이 어려운 상황이다.

AlphaVerus는 formally verified 코드를 생성하는 framework이다.
![Framework](/assets//img/AlphaVerus/framework.webp)
아래 3가지 단계로 구성된다.
- Exploration: resource-rich domain source language에서 target langague로 translation한다. Candidate들을 LLM을 이용해 생성하고 verifier를 이용해 partially verified, fully verified한 candidate를 골라내서 저장한다.
- Treefinement: verified되지 않은 candidate를 tree search와 verifier feedback을 이용해 verified 되도록 반복적으로 refinement한다.
- Critique: specification에 맞지 않는 코드나 align되지 않은 translation을 필터링한다. 이 단계로 인해 reward hacking을 줄일 수 있다. Reward hacking은 엄청 자명하거나 incomplete한 specification을 생성해서 코드가 틀려도 verifier를 통과하게 하거나 verifier가 할 수 없는 한계점을 찾아서 verifier를 통과하게 하는 것을 말한다. Test case 없이 align되지 않은 translation이나 specification에 맞지 않는 코드를 필터링함으로써 reward hacking을 줄일 수 있다.

각 iteration마다 생성된 예제들을 수집해서 모델이 스스로 발전할 수 있는 self-improving framework이다. self-improving framework를 통해 fine-tuning없이도 더 나은 모델을 만들어낼 수 있다.

본 연구에서는 source language로 Dafny를, target language로 Verus를 사용했다. AlphaVerus 모델을 이용해 생성된 verus code, error correction, critique example로 구성된 DAFNY2VERUS-COLLECTION dataset을 생성했다. 해당 dataset에서 data를 몇 개 뽑아 few-shot prmompting한 후에 formally verifed code generation에 사용할 수 있는 모델을 만들었다.

## Formally Verified Code Generation
![Form](/assets//img/AlphaVerus/form.webp)
- Formal verificatoin of code: input-output을 정의하는 formal speicification $y_S$, code implementation $y_I$, proof $y_P$ 로 구성된다. Verifier $v(y_S,y_I,y_P)\to\{0,1\}$ 는 proof를 이용해 코드가 모든 input에 대해 specification을 만족하는지 확인한다. 만약 실패해서 $0$을 return하는 경우 $\{m_1,\dot,m_M}\$을 함께 return한다. 메시지는 통과한 조건문의 개수, 에러의 개수, 에러 메시지로 구성된다.
- Misaligned specs and implementations: Specification은 verification에 포함되지 않으므로 모든 input에 대해 output behavior를 정의하고 있어야 한다. 만약 그렇지 않은 경우를 misaligned되었다고 한다. Speicification과 프로그래머의 의도가 misalign된 것이다.
- Formally verified code generation: $(y_I,y_P)\sim G(y_S;c,\theta)$  speicifaction $S$와 context $c$가 주어졌을 때 코드와 proof를 생성하는 생성 모델 $G$ 를 만드는 것이 목표이다. 생성한 코드가 verify 되어야 한다. $v(y_S,y_I,y_P)=1$
- Bootstrapping problem: Verus는 예제가 너무 없어서 training data 없이 초기 생성 모델을 만들어야 하는 문제가 있다.

## `AlphaVerus`
### Translation
Exploration, treefinement, critique로 구성된 self-reinforcing cycle을 통해 Verus program dataset을 생성한다.
![Form](/assets//img/AlphaVerus/algo.webp)
**Exploration**: 주어진 source language $x$에 대해

$$\{y_1,\dots,y_k\}\sim G_{explore}(x;D^{(i)}_{x\to y})$$

translation candidate set $\{y_1,\dots,y_k\}$을 생성한다. 각 $y$는 위에서 설명한대로 코드, proof, speicification으로 구성된다. $D^{(i)}_{x\to y}$는 지금까지 생성한 source,target 예제들이다. 생성된 pair는 candidate set $C$에 위치하게 되고 필터링을 거치게 된다. Verify되지 않은 candidate는 $C$에서 제외된다. Verify된 candidate가 하나도 없다면 refinement 단계로 넘어간다.
**Treefinement**: 
- verified 되지 않은 source, target pair $(x,y)$ 에 대하여 $(y,e(y))$ 를 root node로 하는 tree를 initialize하고 아래 과정을 반복한다.
- Tree의 node마다 아래 공식을 이용해 점수를 계산한다. $n_{ver}(y)/n_{unver}(y)$ 는 verfied된 함수와 그렇지 함수의 개수를 의미한다. $n_{err}(y)/n_{warn}(y)$ 는 verifier가 출력한 error와 warning의 개수를 의미한다. 아래의 점수가 클수록 verified program에 가깝다.

$$s(y)=\frac{n_{ver}(y)-\alpha n_{err}(y)-\beta n_{warn}(y)}{n_{ver}(y)+n_{unver}(y)} $$

- 위에서 계산한 점수와 REBASE (Reward balanced search) 알고리즘을 이용해 $(y',e(y'))$ 을 선택하고 아래 모델을 이용해 candidate를 모두 refinement한다. $D^{(i)}_{y\to y'}$는 program,error,correct programm의 집합이다.

$$\{y'_1,\dots,y'_{k'}\}\sim G_{refine}(y,e(y);D^{(i)}_{y\to y'})$$

- refinement한 candidate들에 대해 verification을 통과한 candidate는 $x$와 함께 $C$에 추가하고 search trajectory를 $C_{\tau}$에 추가한다. 통과 못한 경우 tree에 추가된다.
**Critique**
Verus 특성상 verifier를 통과는 하지만 아무 기능은 없는 자명한 코드를 만들어낼 수도 있고 specification의 의도와 동떨어진 코드를 작성하게 될 수도 있다. 이러한 reward hacking을 막기 위해서 rule-based, comparison, exploit을 사용해서 필터링을 하는 단계이다.
- Rule-based: candidate $y$가 `assume(false)`, `#[verifier:external]`, trival precondition등의 trivial feature를 포함하는지 확인한다. 몇 개 없어서 rule-base로 가능하다
- Comparison model $f(x,y)$: $f$는 source $x$와 candidate $y$를 입력으로 받아 candidate의 algorithm과 specification이 source의 algorithm/specification과 일치하는지 비교하는 모델이다. $r$ 번 일치하지 않는 걸로 계산되면 false를 return한다.
- Exploit: adversarial approach를 이용한다.$(y_I,y_P)\sim G_{exploit}(y_S;D^{(i)}_{exploit})$ 모델을 이용해 $y$의 specification $y_S$를 검증한다. 모델에게 단순하고 자명한 $y_I,y_P$를 생성하라고 프롬프팅한다. 만약 이 pair가 $y_S$를 통과하면 $y_S$는 잘못되었다는 이야기이다. $D^{(i)}_{exploit}$ 는 (specification, code + proof) 의 집합이다. Verifier를 pass한 pair는 $D^{(i)}_{exploit}$ 에 추가된다.

위 3가지 조건을 통과하지 못하는 경우 해당 candidate는 제거한다.
**Self-improvement**
마지막으로, 각 $D^{(i)}^를 업데이트한다.

$$ D^{(i)}_{x\to y} \cup C \to D^{(i+1)}_{x\to y}$$

$$ D^{(i)}_{y\to y'}\cup\{(y,e(y),y')\vert(x,y')\in C_\tau\}\to D^{(i+1)}_{y\to y'} $$

Source는 Dafny를 이용했다. 두 가지 어려운 점이 있다.
- data type, verifier design등의 차이가 있다.
- Verus는 proof가 더 복잡하다.

### Downstream Evaluation
주어진 specification $y_S$에 대해 아래와 같이 코드 + proof를 생성할 수 있다.

$$(y_I,y_P)\sim G(y_S;D_y,D_{y\to y'})$$

위의 과정을 통해 얻은 dataset $D_y$ 와 $y_S$로 프롬프팅 했을 때 k개의 candidate problem을 생성하고 verify되는게 하나도 없으면 dataset 생성할 때와 유사하게 tree refinement를 거쳐 생성한 집합 $D_{y\to y'}$를 바탕으로 구현과 proof를 생성할 수 있다.

## Results & Analysis
![iter](/assets/img/AlphaVerus/Iteration.webp)
self-improving을 확인할 수 있다.

![res](/assets/img/AlphaVerus/result.webp)
AlphaVerus가 verified code 생성을 할 수 있다는 것과 tree구조를 사용하는 것이 효과적임을 알 수 있다.
![res](/assets/img/AlphaVerus/tree.webp)
refinement를 사용한 것이 퍼포먼스를 크게 증가시켰다.
![c](/assets/img/AlphaVerus/cri.webp)
Critique를 사용하지 않는 경우 reward hacking이 발생함을 확인할 수 있다.
![t](/assets/img/AlphaVerus/tran.png)
생성한 dataset을 다른 모델에 transfer하는 경우에도 성능 향상에 기여했다.


  