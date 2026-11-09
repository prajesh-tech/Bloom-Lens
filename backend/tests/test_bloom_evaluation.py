import hashlib
import json
from scripts.evaluate_bloom import DATA, evaluate


def test_classifier_does_not_drop_below_frozen_internal_baseline():
    baseline = json.loads(DATA.with_name('bloom_baseline.json').read_text())
    assert hashlib.sha256(DATA.read_bytes()).hexdigest() == baseline['dataset_sha256']
    result = evaluate()
    assert result['questions'] >= 150
    assert len(result['subjects']) >= 3
    assert result['accuracy'] >= baseline['accuracy']
