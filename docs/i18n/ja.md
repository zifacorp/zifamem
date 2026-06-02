<p align="center">
  <img src="https://raw.githubusercontent.com/zifacorp/zifamem/main/assets/zifamem-banner.png" alt="ZifaMem - AI コンパニオンのための感情的長期記憶" width="100%">
</p>

<p align="center">
  <a href="../../README.md">English</a> |
  <a href="zh-CN.md">简体中文</a> |
  <a href="ja.md">日本語</a> |
  <a href="ru.md">Русский</a> |
  <a href="ko.md">한국어</a> |
  <a href="es.md">Español</a> |
  <a href="pt.md">Português</a>
</p>

<p align="center">
  <strong>AI コンパニオンが成長し、適応し、時間とともに大切なことを記憶するための感情的長期記憶。</strong>
</p>

<p align="center">
  <a href="#overview">概要</a>
  ·
  <a href="#features">機能</a>
  ·
  <a href="#why-zifamem">なぜ ZifaMem か</a>
  ·
  <a href="#how-it-evolves">進化</a>
  ·
  <a href="#use-cases">ユースケース</a>
  ·
  <a href="#planned-features">ロードマップ</a>
  ·
  <a href="#project-status">ステータス</a>
</p>

<p align="center">
  <img alt="Status" src="https://img.shields.io/badge/status-coming%20soon-dc5f66">
  <img alt="Focus" src="https://img.shields.io/badge/focus-emotional%20memory-111827">
  <img alt="Built for" src="https://img.shields.io/badge/built%20for-growing%20agents-f6d365">
  <img alt="Lifecycle" src="https://img.shields.io/badge/lifecycle-reinforce%20%7C%20reflect%20%7C%20forget-8b5cf6">
</p>

> ソースコード、ドキュメント、サンプルを準備中です。オープンソース公開は近日予定です。

<a id="overview"></a>
## 概要

ZifaMem は、AI エージェント、AI コンパニオン、関係性を中心にしたプロダクトのための感情的長期記憶フレームワークです。

多くの記憶システムは、エージェントが事実を検索するためのものです。ZifaMem は、エージェントが**成長**することを目的に設計されています。関係性の変化に応じて、記憶は強化され、弱まり、統合され、振り返られ、忘れられます。無限に会話ログをためるのではなく、AI コンパニオンが時間とともに一貫性を増し、より個人的で、感情的文脈を理解できるようにする生きた記憶レイヤーを目指します。

<a id="features"></a>
## 機能

- 気分、感情、強度、信頼、安心感、衝突、愛着、境界線などの感情記憶モデリング
- 長期的なユーザーとエージェントの連続性を支える関係タイムライン
- 強化、減衰、統合、振り返り、忘却のための記憶ライフサイクルポリシー
- 意味的関連性と関係文脈を組み合わせる感情認識型リコール
- 抽出、保存、検索、振り返り、応答生成のためのエージェントネイティブなインターフェース
- 記憶の確認、修正、削除、同意に基づくパーソナライズのためのユーザー可視な制御を計画中

## ZifaMem は誰のためのものですか？

ZifaMem は、エージェントが単にデータベースを検索するのではなく、関係性を学んでいるように感じられる AI プロダクトを作るチームのためのものです。

ZifaMem は次のような場合に適しています。

- AI コンパニオン、キャラクター、コーチ、感情サポートエージェントを作っている
- 信頼の形成、衝突の修復、繰り返されるパターンに応じて記憶を変化させたい
- すべての会話を永久保存せずに、エージェントをより個人的にしたい
- 感情的連続性、同意、ユーザー制御、長期安全性を重視している
- 数か月から数年にわたる振り返りとエージェント成長を支える記憶レイヤーが必要

短期的なチャット履歴、文書検索、タスク向けの事実リコールだけが必要な場合、ZifaMem は最適ではないかもしれません。

<a id="why-zifamem"></a>
## なぜ ZifaMem か

多くの AI 記憶システムは、名前、好み、文書、タスク、検索された断片などの事実リコールに最適化されています。

ZifaMem は、別の層の記憶、つまり**感情的連続性**のために設計されています。

AI コンパニオンや関係性を中心にした AI では、何が起きたかだけでなく、それがどう感じられたか、なぜ重要だったか、関係が時間とともにどう変化したかを保持する必要があります。ZifaMem は、信頼、安心感、衝突、愛着、境界線、修復、繰り返される感情パターン、意味のある共有履歴を記憶する必要があるシステムのために作られています。

## 何が違うのか

| 静的な記憶 | ZifaMem |
| --- | --- |
| 事実と断片を保存する | 感情的に意味のある記憶をモデル化する |
| 意味的類似度を最適化する | 関連性、新しさ、強度、関係文脈をバランスする |
| 記憶を静的なテキストとして扱う | 記憶を強め、薄め、統合し、忘れられるようにする |
| ユーザーが言ったことを思い出す | 何が重要で、それが関係をどう形作ったかを思い出す |
| 孤立した好みからパーソナライズする | 進化する関係タイムラインからパーソナライズする |
| タスク型エージェントに向いている | コンパニオン、ロールプレイ、コーチング、ソーシャル AI のために設計されている |

## いつ ZifaMem を使うべきですか？

ボトルネックが基本的な検索ではなく**連続性**になったとき、ZifaMem が役立ちます。

- セッションをまたいで感情的履歴を覚える必要がある長期運用エージェント
- 信頼、弱さ、安心感、衝突が重要なコンパニオン製品
- 安定した共有履歴が必要なロールプレイやキャラクターエージェント
- 繰り返される感情パターンに気づく必要があるコーチングや振り返りツール
- 同意、減衰、修正のための記憶ポリシーが必要なソーシャル AI システム
- ユーザーとの関係が成熟するにつれて応答を改善すべきエージェント

<a id="how-it-evolves"></a>
## どのように進化するか

ZifaMem は記憶を、保存されたメッセージの山ではなくライフサイクルとして扱います。

```mermaid
flowchart LR
    CHAT["会話"] --> EXTRACT["信号を抽出"]
    EXTRACT --> SCORE["感情的意味を評価"]
    SCORE --> STORE["記憶を保存"]
    STORE --> RECALL["文脈リコール"]
    RECALL --> RESPOND["エージェント応答"]
    RESPOND --> FEEDBACK["ユーザー反応"]
    FEEDBACK --> REFLECT["振り返りと統合"]
    REFLECT --> UPDATE["強化、統合、減衰、忘却"]
    UPDATE --> STORE

    STORE -.- M1["共有履歴"]
    RECALL -.- M2["関係文脈"]
    REFLECT -.- M3["エージェント成長"]
    UPDATE -.- M4["生きた記憶"]

    style CHAT fill:#f6d365,stroke:#d97706,stroke-width:2px,color:#111827
    style EXTRACT fill:#f9a8d4,stroke:#be185d,stroke-width:2px,color:#111827
    style SCORE fill:#f472b6,stroke:#be185d,stroke-width:2px,color:#111827
    style STORE fill:#8b5cf6,stroke:#6d28d9,stroke-width:2px,color:#ffffff
    style RECALL fill:#6366f1,stroke:#4338ca,stroke-width:2px,color:#ffffff
    style RESPOND fill:#14b8a6,stroke:#0f766e,stroke-width:2px,color:#ffffff
    style FEEDBACK fill:#f97316,stroke:#c2410c,stroke-width:2px,color:#ffffff
    style REFLECT fill:#dc5f66,stroke:#b91c1c,stroke-width:2px,color:#ffffff
    style UPDATE fill:#111827,stroke:#374151,stroke-width:2px,color:#ffffff
    style M1 fill:#ffffff,stroke:#8b5cf6,stroke-width:1px,color:#6d28d9
    style M2 fill:#ffffff,stroke:#6366f1,stroke-width:1px,color:#4338ca
    style M3 fill:#ffffff,stroke:#dc5f66,stroke-width:1px,color:#b91c1c
    style M4 fill:#ffffff,stroke:#111827,stroke-width:1px,color:#111827
```

## 主要コンセプト

### 感情記憶

記憶は、気分、感情傾向、強度、安心感、弱さ、衝突、信頼、愛着関連性などの感情信号を持つことができます。

### 関係タイムライン

ZifaMem は、孤立した会話チャンクではなく、ユーザーと AI システムの間で進化する関係を中心に記憶を整理します。

### 記憶ライフサイクル

記憶は作成、強化、弱化、更新、統合、忘却されます。目的は、古い文脈を永遠に蓄積するのではなく、進化する記憶システムを作ることです。

### エージェント成長

エージェントは記憶の振り返りを使って、ユーザーの感情パターン、関係履歴、望ましい支援の形によりよく合わせることができます。

### 文脈リコール

リコールは、意味、感情的関連性、時間、ユーザー状態、関係状態、会話意図を組み合わせるように設計されています。

### エージェントネイティブ設計

ZifaMem は、抽出、保存、検索、振り返り、パーソナライズ、感情認識型応答生成のためのエージェント向けフレームワークとして計画されています。

<a id="use-cases"></a>
## ユースケース

- AI コンパニオン
- 感情サポートエージェント
- ロールプレイとキャラクターエージェント
- 長期運用の個人 AI アシスタント
- コーチングと振り返りツール
- ソーシャル AI 製品
- 感情認識型コミュニティおよびカスタマーエージェント

<a id="planned-features"></a>
## 計画中の機能

- 感情記憶スキーマ
- 会話から記憶への抽出
- 感情と関係信号のタグ付け
- 長期保存抽象化
- 関係タイムラインモデリング
- 感情認識型リトリーバルランキング
- 記憶の統合と振り返り
- 有用な記憶を強化し古い記憶を修正するエージェント成長ループ
- 忘却、減衰、強化ポリシー
- ユーザーが制御できる記憶の可視性
- 同意に基づく記憶編集と削除
- コンパニオンエージェント向け SDK サンプル
- 記憶連続性の評価ツール

## よくある質問

### ZifaMem はベクトルデータベースですか？

いいえ。ZifaMem は保存や検索システムと連携できる記憶フレームワークとして計画されていますが、焦点は感情的意味、ライフサイクルポリシー、関係の連続性、エージェント成長です。

### ZifaMem はすべての会話を保存しますか？

いいえ。目的は意味のある記憶を抽出し、それらを時間とともに変化させることです。一部の記憶は強化され、一部は修正され、一部は薄れたり忘れられたりするべきです。

### 通常のパーソナライズと何が違いますか？

通常のパーソナライズは好みを保存することが多いです。ZifaMem は、信頼、安心感、衝突、弱さ、愛着、境界線、修復、共有履歴といった関係性の文脈のために設計されています。

### ユーザーは記憶を制御できますか？

記憶の確認、修正、削除、同意に基づく制御は計画中のロードマップに含まれています。

<a id="project-status"></a>
## プロジェクトステータス

ZifaMem は初期開発段階です。

この公開リポジトリは、プロジェクトの方向性を示すプレビューです。実装、ドキュメント、サンプル、コントリビューションガイド、ライセンスは近日公開予定です。

## フォロー

オープンソース公開を追うには、このリポジトリを Watch してください。

組織の更新情報は [Zifa AI](https://github.com/zifacorp) をご覧ください。

## ライセンス

ソースコード公開時に発表予定です。
