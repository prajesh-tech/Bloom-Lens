from pathlib import Path
import pytest
from app.utils.validators import SUPPORTED_EXAM_TYPES
from app.core.config import Settings


@pytest.mark.asyncio
async def test_exam_types_are_the_upload_contract(client, unauthed_client):
    response = await client.get('/api/v1/papers/exam-types')
    assert response.status_code == 200
    assert response.json() == SUPPORTED_EXAM_TYPES
    assert (await unauthed_client.get('/api/v1/papers/exam-types')).status_code == 401


def test_example_thresholds_match_code_defaults():
    example = dict(line.split('=', 1) for line in (Path(__file__).parents[1] / '.env.example').read_text().splitlines() if line and not line.startswith('#') and '=' in line)
    for name in ('BLOOM_VERIFICATION_THRESHOLD', 'SIMILARITY_THRESHOLD_SEMANTIC'):
        assert float(example[name]) == Settings.model_fields[name].default
