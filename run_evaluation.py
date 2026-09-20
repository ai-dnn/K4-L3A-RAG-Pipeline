"""Evaluation script -- chạy 2 config (dense-only vs hybrid+RRF) trên golden dataset."""

import json
import os
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
ROOT = Path(__file__).parent
GOLDEN_PATH = ROOT / "group_project" / "evaluation" / "golden_dataset.json"
RESULT_PATH = ROOT / "group_project" / "evaluation" / "eval_results.json"


def _retrieve_and_generate(question: str, config: str) -> dict:
    """Retrieve + generate cho một câu hỏi với config cho trước."""
    from src.task10_generation import generate_with_citation, REFUSAL
    from src.task9_retrieval_pipeline import retrieve

    top_k = 5
    if config == "dense_only":
        chunks = retrieve(question, top_k=top_k, use_reranking=False)
    else:
        chunks = retrieve(question, top_k=top_k, use_reranking=True)

    result = generate_with_citation(question, top_k=top_k)
    return {
        "question": question,
        "answer": result["answer"],
        "contexts": [c["content"] for c in result["sources"]],
        "retrieval_source": result["retrieval_source"],
        "config": config,
    }


def run_evaluation():
    """Chạy evaluation trên golden dataset với 2 config."""
    if not GOLDEN_PATH.exists():
        print(f"Golden dataset not found: {GOLDEN_PATH}")
        sys.exit(1)

    golden = json.loads(GOLDEN_PATH.read_text(encoding="utf-8"))
    print(f"Loaded {len(golden)} questions from golden dataset")

    results = {"dense_only": [], "hybrid_rrf": []}

    for config in ["dense_only", "hybrid_rrf"]:
        print(f"\n{'='*60}")
        print(f"Running config: {config}")
        print(f"{'='*60}")

        for i, item in enumerate(golden, 1):
            question = item["question"]
            ground_truth = item["ground_truth"]
            print(f"\n[{i}/{len(golden)}] {question[:80]}...")

            try:
                result = _retrieve_and_generate(question, config)
                result["ground_truth"] = ground_truth
                results[config].append(result)
                print(f"  Answer: {result['answer'][:100]}...")
                print(f"  Contexts: {len(result['contexts'])} chunks")
            except Exception as e:
                print(f"  ERROR: {e}")
                results[config].append({
                    "question": question,
                    "ground_truth": ground_truth,
                    "answer": f"ERROR: {e}",
                    "contexts": [],
                    "config": config,
                    "error": str(e),
                })

            time.sleep(0.5)

    RESULT_PATH.write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"\nResults saved to: {RESULT_PATH}")
    print(f"Dense-only: {len(results['dense_only'])} results")
    print(f"Hybrid+RRF: {len(results['hybrid_rrf'])} results")


def compute_metrics():
    """Tính metrics từ kết quả evaluation (cần ragas)."""
    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_recall, context_precision
        from datasets import Dataset
    except ImportError:
        print("ragas hoặc datasets chưa được cài. Chạy: pip install ragas datasets")
        return

    if not RESULT_PATH.exists():
        print("Chưa có kết quả evaluation. Chạy run_evaluation() trước.")
        return

    results = json.loads(RESULT_PATH.read_text(encoding="utf-8"))

    for config_name, config_results in results.items():
        print(f"\n{'='*60}")
        print(f"Computing metrics for: {config_name}")
        print(f"{'='*60}")

        valid = [r for r in config_results if "error" not in r and r.get("contexts")]
        if not valid:
            print("  No valid results to evaluate.")
            continue

        dataset = Dataset.from_dict({
            "question": [r["question"] for r in valid],
            "answer": [r["answer"] for r in valid],
            "contexts": [r["contexts"] for r in valid],
            "ground_truth": [r["ground_truth"] for r in valid],
        })

        try:
            score = evaluate(
                dataset,
                metrics=[faithfulness, answer_relevancy, context_recall, context_precision],
            )
            print(f"  Faithfulness:      {score['faithfulness']:.4f}")
            print(f"  Answer Relevancy:  {score['answer_relevancy']:.4f}")
            print(f"  Context Recall:    {score['context_recall']:.4f}")
            print(f"  Context Precision: {score['context_precision']:.4f}")
        except Exception as e:
            print(f"  Error computing metrics: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "metrics":
        compute_metrics()
    else:
        run_evaluation()
