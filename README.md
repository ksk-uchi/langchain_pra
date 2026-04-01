# langchain_pra

Practice repo for LangChain

## command

### Registry

`corpus` コレクションに `./corpus` 配下にある `.txt` および `.md` を登録する

```
python ./commands/registry/main.py --path=./corpus --collection=corpus
```

### Query

`corpus` コレクションに `クエリ` を問い合わせ、関連性の高い TOP 10 のコンテキストを取得し、
LLM に対してコンテキストとともにクエリを問い合わせる。

```
python commands/query/main.py --collection=corpus --n=10 --query="クエリ"
```
